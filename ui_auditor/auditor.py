from __future__ import annotations

import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from .report import build_report_html


REALISTIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REALISTIC_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Upgrade-Insecure-Requests": "1",
}
HUMAN_LOCALE = "tr-TR"
HUMAN_TIMEZONE = "Europe/Istanbul"
LAUNCH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--no-sandbox",
]
DESKTOP_VIEWPORT = {"width": 1440, "height": 980}
DEFAULT_OUTPUT_DIR = Path("output/ui-auditor/latest").resolve()
ASSET_LIKE_EXTENSIONS = re.compile(
    r"\.(png|jpe?g|svg|webp|gif|ico|pdf|zip|rar|mp4|webm|mp3|css|js|json|xml)$",
    re.IGNORECASE,
)
BLOCKED_TEXT_PATTERN = re.compile(
    r"access denied|request blocked|are you a (?:human|bot)|verify you are human|"
    r"automated requests|cloudflare|just a moment|checking your browser|"
    r"ddos protection|please complete the security check",
    re.IGNORECASE,
)

STEALTH_INIT_SCRIPT = """
(() => {
  Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  Object.defineProperty(navigator, "languages", { get: () => ["tr-TR", "tr", "en-US", "en"] });
  Object.defineProperty(navigator, "plugins", { get: () => [1, 2, 3, 4, 5] });
  window.chrome = window.chrome || { runtime: {} };
})();
"""


def normalize_url(raw_url: str) -> str:
    parts = urlsplit(raw_url)
    path = parts.path or "/"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))


def is_http_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")


def is_likely_page_url(url: str) -> bool:
    return ASSET_LIKE_EXTENSIONS.search(urlsplit(url).path) is None


def origin_of(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def format_status_text(status: int | None, error_message: str | None = None) -> str:
    if error_message:
        return error_message
    if status is None:
        return "No response"
    return f"HTTP {status}"


def is_restricted_status(status: int | None) -> bool:
    return status in {401, 403, 429}


def detect_blocked_state(status: int | None, text_sample: str) -> bool:
    return is_restricted_status(status) or bool(BLOCKED_TEXT_PATTERN.search(text_sample))


def detect_loading_state(text_sample: str, blocked: bool) -> bool:
    if blocked:
        return False
    return bool(re.search(r"\bloading\b", text_sample, re.IGNORECASE))


def random_between(minimum: int, maximum: int) -> int:
    return random.randint(minimum, max(minimum, maximum - 1))


def apply_stealth_context(context: BrowserContext) -> None:
    context.add_init_script(STEALTH_INIT_SCRIPT)


def humanize(page: Page, viewport: dict[str, int] | None) -> None:
    width = (viewport or {}).get("width", 1440)
    height = (viewport or {}).get("height", 900)

    try:
        for _ in range(3):
            x = random_between(40, max(41, width - 40))
            y = random_between(40, max(41, height - 40))
            page.mouse.move(x, y, steps=random_between(12, 24))
            page.wait_for_timeout(random_between(120, 280))
    except Exception:
        pass

    try:
        page.evaluate(
            """
            async () => {
              await new Promise((resolve) => {
                const step = Math.max(120, Math.floor(window.innerHeight / 4));
                let current = 0;
                const timer = setInterval(() => {
                  window.scrollBy({ top: step, behavior: "smooth" });
                  current += step;
                  if (current >= document.body.scrollHeight) {
                    clearInterval(timer);
                    setTimeout(resolve, 350);
                  }
                }, 220);
              });
              await new Promise((resolve) => {
                window.scrollTo({ top: 0, behavior: "smooth" });
                setTimeout(resolve, 500);
              });
            }
            """
        )
    except Exception:
        pass

    page.wait_for_timeout(random_between(2000, 3000))


def wait_for_challenge(page: Page) -> None:
    try:
        page.wait_for_function(
            """
            () => {
              const title = (document.title || "").toLowerCase();
              const body = (document.body?.innerText || "").toLowerCase();
              const challengeSignals = [
                "just a moment",
                "checking your browser",
                "verifying you are human",
                "attention required"
              ];
              return !challengeSignals.some(
                (signal) => title.includes(signal) || body.includes(signal)
              );
            }
            """,
            timeout=8000,
        )
    except Exception:
        pass


def check_link(request_context: Any, url: str) -> dict[str, Any]:
    try:
        response = request_context.fetch(
            url,
            method="HEAD",
            fail_on_status_code=False,
            timeout=8000,
            max_redirects=5,
        )

        if response.status in {400, 401, 403, 405}:
            response = request_context.fetch(
                url,
                method="GET",
                fail_on_status_code=False,
                timeout=8000,
                max_redirects=5,
            )

        return {
            "ok": response.status < 400,
            "status": response.status,
            "statusText": format_status_text(response.status),
            "finalUrl": response.url,
        }
    except Exception as error:
        return {
            "ok": False,
            "status": None,
            "statusText": str(error),
            "finalUrl": url,
        }


def collect_page_snapshot(page: Page) -> dict[str, Any]:
    return page.evaluate(
        """
        () => {
          const bodyText = (document.body?.innerText || "").trim();

          const visibleElements = Array.from(
            document.querySelectorAll('button, a, [role="button"], input[type="button"], input[type="submit"]')
          )
            .map((element) => {
              const rect = element.getBoundingClientRect();
              const style = window.getComputedStyle(element);
              const label =
                element.getAttribute("aria-label") ||
                element.textContent?.trim() ||
                element.getAttribute("title") ||
                element.tagName.toLowerCase();

              return {
                label: label.slice(0, 80),
                rect: {
                  top: rect.top,
                  right: rect.right,
                  bottom: rect.bottom,
                  left: rect.left,
                  width: rect.width,
                  height: rect.height
                },
                visible:
                  rect.width > 0 &&
                  rect.height > 0 &&
                  style.display !== "none" &&
                  style.visibility !== "hidden" &&
                  Number(style.opacity || 1) > 0
              };
            })
            .filter((item) => item.visible);

          const mobileIssues = [];
          for (let i = 0; i < visibleElements.length; i += 1) {
            for (let j = i + 1; j < visibleElements.length; j += 1) {
              const first = visibleElements[i];
              const second = visibleElements[j];
              const overlapWidth =
                Math.min(first.rect.right, second.rect.right) - Math.max(first.rect.left, second.rect.left);
              const overlapHeight =
                Math.min(first.rect.bottom, second.rect.bottom) - Math.max(first.rect.top, second.rect.top);
              const area = overlapWidth <= 0 || overlapHeight <= 0 ? 0 : overlapWidth * overlapHeight;

              if (area > 80) {
                mobileIssues.push({
                  type: "Button overlap",
                  detail: `${first.label} overlaps with ${second.label}`
                });
              }
            }
          }

          if (document.documentElement.scrollWidth - window.innerWidth > 8) {
            mobileIssues.push({
              type: "Horizontal overflow",
              detail: `Page width exceeds viewport by ${document.documentElement.scrollWidth - window.innerWidth}px`
            });
          }

          const links = Array.from(document.querySelectorAll("a[href]")).map((anchor) => {
            const href = anchor.getAttribute("href") || "";
            let resolved = null;
            try {
              resolved = new URL(href, window.location.href).toString();
            } catch {
              resolved = null;
            }

            return {
              text: (anchor.textContent || "").trim().slice(0, 100),
              href,
              resolved
            };
          });

          const images = Array.from(document.images).map((img) => ({
            url: img.currentSrc || img.src || "",
            alt: (img.alt || "").trim().slice(0, 100),
            complete: img.complete,
            naturalWidth: img.naturalWidth
          }));

          return {
            title: document.title || window.location.pathname,
            textSample: bodyText.slice(0, 2000),
            links,
            images,
            mobileIssues
          };
        }
        """
    )


def new_desktop_context(browser: Browser) -> BrowserContext:
    context = browser.new_context(
        viewport=DESKTOP_VIEWPORT,
        ignore_https_errors=True,
        user_agent=REALISTIC_USER_AGENT,
        locale=HUMAN_LOCALE,
        timezone_id=HUMAN_TIMEZONE,
        extra_http_headers=REALISTIC_HEADERS,
    )
    apply_stealth_context(context)
    return context


def new_mobile_context(browser: Browser, playwright: Playwright) -> BrowserContext:
    iphone = dict(playwright.devices["iPhone 13"])
    iphone.pop("default_browser_type", None)
    context = browser.new_context(
        **iphone,
        ignore_https_errors=True,
        locale=HUMAN_LOCALE,
        timezone_id=HUMAN_TIMEZONE,
        extra_http_headers={
            **REALISTIC_HEADERS,
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA-Platform": '"iOS"',
        },
    )
    apply_stealth_context(context)
    return context


def audit_single_page(
    *,
    playwright: Playwright,
    browser: Browser,
    request_context: Any,
    url: str,
    origin: str,
    index: int,
    screenshots_dir: Path,
) -> dict[str, Any]:
    desktop_context = new_desktop_context(browser)
    mobile_context: BrowserContext | None = None

    try:
        desktop_page = desktop_context.new_page()
        failed_image_requests: list[dict[str, str]] = []

        def record_failed_image(request: Any) -> None:
            if request.resource_type == "image":
                failed_image_requests.append(
                    {
                        "url": request.url,
                        "reason": request.failure or "Image request failed",
                    }
                )

        desktop_page.on("requestfailed", record_failed_image)

        response = desktop_page.goto(url, wait_until="domcontentloaded", timeout=25000)
        try:
            desktop_page.wait_for_load_state("load")
        except Exception:
            pass
        wait_for_challenge(desktop_page)
        humanize(desktop_page, DESKTOP_VIEWPORT)

        snapshot = collect_page_snapshot(desktop_page)
        navigation_status_code = response.status if response else None
        blocked_on_desktop = detect_blocked_state(
            status=navigation_status_code,
            text_sample=snapshot["textSample"],
        )
        desktop_screenshot_file = f"screenshots/page-{index:02d}-desktop.png"
        desktop_page.screenshot(
            path=str(screenshots_dir / f"page-{index:02d}-desktop.png"),
            full_page=True,
        )

        mobile_context = new_mobile_context(browser, playwright)
        mobile_page = mobile_context.new_page()

        mobile_page.goto(url, wait_until="domcontentloaded", timeout=25000)
        try:
            mobile_page.wait_for_load_state("load")
        except Exception:
            pass
        wait_for_challenge(mobile_page)
        humanize(mobile_page, playwright.devices["iPhone 13"]["viewport"])

        mobile_snapshot = collect_page_snapshot(mobile_page)
        mobile_blocked = detect_blocked_state(
            status=navigation_status_code,
            text_sample=mobile_snapshot["textSample"],
        )
        mobile_loading = detect_loading_state(
            text_sample=mobile_snapshot["textSample"],
            blocked=blocked_on_desktop or mobile_blocked,
        )
        mobile_screenshot_file = f"screenshots/page-{index:02d}-mobile.png"
        mobile_page.screenshot(
            path=str(screenshots_dir / f"page-{index:02d}-mobile.png"),
            full_page=True,
        )

        link_map: dict[str, dict[str, Any] | None] = {}
        for link in snapshot["links"]:
            resolved = link.get("resolved")
            if not resolved or not is_http_url(resolved):
                continue
            link_map.setdefault(normalize_url(resolved), None)

        for link_url in list(link_map):
            link_map[link_url] = check_link(request_context, link_url)

        broken_links = []
        for link in snapshot["links"]:
            resolved = link.get("resolved")
            if not resolved or not is_http_url(resolved):
                continue
            result = link_map.get(normalize_url(resolved))
            if result and not result["ok"]:
                broken_links.append(
                    {
                        "url": result.get("finalUrl") or resolved,
                        "text": link.get("text") or "",
                        "status": result.get("status"),
                        "statusText": result.get("statusText"),
                    }
                )

        broken_images = [
            {
                "url": image["url"],
                "alt": image["alt"],
                "reason": "Browser reported an image that did not render correctly.",
            }
            for image in snapshot["images"]
            if image.get("url") and (not image.get("complete") or image.get("naturalWidth") == 0)
        ]

        for failed in failed_image_requests:
            if not any(item["url"] == failed["url"] for item in broken_images):
                broken_images.append(
                    {
                        "url": failed["url"],
                        "alt": "",
                        "reason": failed["reason"],
                    }
                )

        navigation_candidates = [
            link_url
            for link_url in link_map
            if origin_of(link_url) == origin and is_likely_page_url(link_url)
        ]

        audit_warnings = []
        if blocked_on_desktop or mobile_blocked:
            audit_warnings.append(
                {
                    "type": "Access restricted",
                    "detail": (
                        "The page appears to be protected by access restrictions or anti-bot checks. "
                        "Layout checks were skipped to avoid false positives."
                    ),
                }
            )
        elif mobile_loading:
            audit_warnings.append(
                {
                    "type": "Stalled loading state",
                    "detail": (
                        "The mobile page still displayed a loading state after the wait period. "
                        "Layout checks were skipped because the interface may not have fully rendered."
                    ),
                }
            )

        should_skip_mobile_issues = blocked_on_desktop or mobile_blocked or mobile_loading

        return {
            "url": url,
            "title": snapshot["title"],
            "navigationStatus": format_status_text(navigation_status_code),
            "statusCode": navigation_status_code,
            "accessRestricted": blocked_on_desktop or mobile_blocked,
            "desktopScreenshot": f"./{desktop_screenshot_file}",
            "mobileScreenshot": f"./{mobile_screenshot_file}",
            "checkedLinks": len(link_map),
            "brokenLinks": broken_links,
            "brokenImages": broken_images,
            "mobileIssues": [] if should_skip_mobile_issues else mobile_snapshot["mobileIssues"],
            "auditWarnings": audit_warnings,
            "navigationCandidates": navigation_candidates,
        }
    finally:
        if mobile_context is not None:
            mobile_context.close()
        desktop_context.close()


def build_summary(pages: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "pagesAudited": 0,
        "checkedLinks": 0,
        "brokenLinks": 0,
        "brokenImages": 0,
        "mobileIssues": 0,
        "blockedPages": 0,
        "warningCount": 0,
    }

    for page in pages:
        summary["pagesAudited"] += 1
        summary["checkedLinks"] += page["checkedLinks"]
        summary["brokenLinks"] += len(page["brokenLinks"])
        summary["brokenImages"] += len(page["brokenImages"])
        summary["mobileIssues"] += len(page["mobileIssues"])
        summary["blockedPages"] += 1 if page["accessRestricted"] else 0
        summary["warningCount"] += len(page["auditWarnings"])

    return summary


def audit_site(
    *,
    target_url: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    max_pages: int = 5,
) -> dict[str, Any]:
    target_url = normalize_url(target_url)
    output_path = Path(output_dir).resolve()
    screenshots_dir = output_path / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=LAUNCH_ARGS)
        request_context = playwright.request.new_context(
            ignore_https_errors=True,
            user_agent=REALISTIC_USER_AGENT,
            extra_http_headers=REALISTIC_HEADERS,
        )

        try:
            start_time = time.time()
            origin = origin_of(target_url)
            queue = [target_url]
            queued = set(queue)
            visited: set[str] = set()
            pages: list[dict[str, Any]] = []

            while queue and len(pages) < max_pages:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)

                try:
                    page_result = audit_single_page(
                        playwright=playwright,
                        browser=browser,
                        request_context=request_context,
                        url=current,
                        origin=origin,
                        index=len(pages) + 1,
                        screenshots_dir=screenshots_dir,
                    )
                    pages.append(page_result)

                    for candidate in page_result["navigationCandidates"]:
                        if (
                            candidate not in visited
                            and candidate not in queued
                            and len(pages) + len(queue) < max_pages
                        ):
                            queue.append(candidate)
                            queued.add(candidate)
                except Exception as error:
                    pages.append(
                        {
                            "url": current,
                            "title": current,
                            "navigationStatus": str(error),
                            "statusCode": None,
                            "accessRestricted": False,
                            "desktopScreenshot": "",
                            "mobileScreenshot": "",
                            "checkedLinks": 0,
                            "brokenLinks": [],
                            "brokenImages": [],
                            "mobileIssues": [],
                            "auditWarnings": [
                                {
                                    "type": "Audit failure",
                                    "detail": str(error),
                                }
                            ],
                            "navigationCandidates": [],
                        }
                    )

            report = {
                "targetUrl": target_url,
                "generatedAt": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "durationMs": int((time.time() - start_time) * 1000),
                "summary": build_summary(pages),
                "pages": pages,
            }

            (output_path / "audit-result.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (output_path / "index.html").write_text(
                build_report_html(report),
                encoding="utf-8",
            )

            return report
        finally:
            request_context.dispose()
            browser.close()
