import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium as stealthChromium } from "playwright-extra";
import stealthPlugin from "puppeteer-extra-plugin-stealth";
import { devices, request } from "playwright";

import { buildReportHtml } from "./report-template.mjs";

stealthChromium.use(stealthPlugin());
const chromium = stealthChromium;

const realisticUserAgent =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";
const realisticHeaders = {
  "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
  "Sec-CH-UA": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
  "Sec-CH-UA-Mobile": "?0",
  "Sec-CH-UA-Platform": '"Windows"',
  "Upgrade-Insecure-Requests": "1"
};
const humanLocale = "tr-TR";
const humanTimezone = "Europe/Istanbul";
const launchArgs = [
  "--disable-blink-features=AutomationControlled",
  "--disable-features=IsolateOrigins,site-per-process",
  "--no-sandbox"
];

const currentDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(currentDir, "..");
const defaultOutputDir = resolve(projectRoot, "..", "output", "ui-auditor", "latest");
const desktopViewport = { width: 1440, height: 980 };
const iPhone = devices["iPhone 13"];
const assetLikeExtensions = /\.(png|jpe?g|svg|webp|gif|ico|pdf|zip|rar|mp4|webm|mp3|css|js|json|xml)$/i;
const blockedTextPattern =
  /access denied|request blocked|are you a (?:human|bot)|verify you are human|automated requests|cloudflare|just a moment|checking your browser|ddos protection|please complete the security check/i;

function normalizeUrl(rawUrl) {
  const url = new URL(rawUrl);
  url.hash = "";
  return url.toString();
}

function getArgValue(args, flag, fallback) {
  const index = args.indexOf(flag);
  if (index === -1 || index === args.length - 1) return fallback;
  return args[index + 1];
}

function parseArgs(argv) {
  const args = [...argv];
  const targetUrl = args.find((item) => !item.startsWith("--"));
  const outputDir = getArgValue(args, "--output", defaultOutputDir);
  const maxPages = Number(getArgValue(args, "--max-pages", "5"));

  if (!targetUrl) {
    throw new Error("Usage: npm run audit -- <url> [--max-pages 5] [--output path]");
  }

  return {
    targetUrl: normalizeUrl(targetUrl),
    outputDir: resolve(outputDir),
    maxPages: Number.isFinite(maxPages) && maxPages > 0 ? maxPages : 5
  };
}

function isHttpUrl(url) {
  return url.startsWith("http://") || url.startsWith("https://");
}

function isLikelyPageUrl(url) {
  return !assetLikeExtensions.test(new URL(url).pathname);
}

function formatStatusText(status, errorMessage) {
  if (errorMessage) return errorMessage;
  if (status >= 400) return `HTTP ${status}`;
  return `HTTP ${status}`;
}

function isRestrictedStatus(status) {
  return [401, 403, 429].includes(status);
}

function detectBlockedState({ status, textSample }) {
  return isRestrictedStatus(status) || blockedTextPattern.test(textSample);
}

function detectLoadingState({ textSample, blocked }) {
  if (blocked) return false;
  return /\bloading\b/i.test(textSample);
}

function randomBetween(min, max) {
  return Math.floor(min + Math.random() * (max - min));
}

async function humanize(page, viewport) {
  const width = viewport?.width ?? 1440;
  const height = viewport?.height ?? 900;

  try {
    for (let i = 0; i < 3; i += 1) {
      const x = randomBetween(40, Math.max(41, width - 40));
      const y = randomBetween(40, Math.max(41, height - 40));
      await page.mouse.move(x, y, { steps: randomBetween(12, 24) });
      await page.waitForTimeout(randomBetween(120, 280));
    }
  } catch {}

  try {
    await page.evaluate(async () => {
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
    });
  } catch {}

  await page.waitForTimeout(randomBetween(2000, 3000));
}

async function waitForChallenge(page) {
  try {
    await page.waitForFunction(
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
      },
      { timeout: 8000 }
    );
  } catch {}
}

async function checkLink(requestContext, url) {
  try {
    let response = await requestContext.fetch(url, {
      method: "HEAD",
      failOnStatusCode: false,
      timeout: 8000,
      maxRedirects: 5
    });

    if ([400, 401, 403, 405].includes(response.status())) {
      response = await requestContext.fetch(url, {
        method: "GET",
        failOnStatusCode: false,
        timeout: 8000,
        maxRedirects: 5
      });
    }

    return {
      ok: response.status() < 400,
      status: response.status(),
      statusText: formatStatusText(response.status()),
      finalUrl: response.url()
    };
  } catch (error) {
    return {
      ok: false,
      status: null,
      statusText: error.message,
      finalUrl: url
    };
  }
}

function intersectionArea(a, b) {
  const overlapWidth = Math.min(a.right, b.right) - Math.max(a.left, b.left);
  const overlapHeight = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);

  if (overlapWidth <= 0 || overlapHeight <= 0) {
    return 0;
  }

  return overlapWidth * overlapHeight;
}

async function collectPageSnapshot(page) {
  return page.evaluate(() => {
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
        const area = (() => {
          const overlapWidth =
            Math.min(first.rect.right, second.rect.right) - Math.max(first.rect.left, second.rect.left);
          const overlapHeight =
            Math.min(first.rect.bottom, second.rect.bottom) - Math.max(first.rect.top, second.rect.top);

          if (overlapWidth <= 0 || overlapHeight <= 0) return 0;
          return overlapWidth * overlapHeight;
        })();

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
  });
}

async function auditSinglePage({
  browser,
  requestContext,
  url,
  origin,
  index,
  screenshotsDir
}) {
  const desktopContext = await browser.newContext({
    viewport: desktopViewport,
    ignoreHTTPSErrors: true,
    userAgent: realisticUserAgent,
    locale: humanLocale,
    timezoneId: humanTimezone,
    extraHTTPHeaders: realisticHeaders
  });
  const desktopPage = await desktopContext.newPage();
  const failedImageRequests = [];

  desktopPage.on("requestfailed", (req) => {
    if (req.resourceType() === "image") {
      failedImageRequests.push({
        url: req.url(),
        reason: req.failure()?.errorText || "Image request failed"
      });
    }
  });

  const response = await desktopPage.goto(url, {
    waitUntil: "domcontentloaded",
    timeout: 25000
  });
  await desktopPage.waitForLoadState("load").catch(() => {});
  await waitForChallenge(desktopPage);
  await humanize(desktopPage, desktopViewport);

  const snapshot = await collectPageSnapshot(desktopPage);
  const navigationStatusCode = response?.status() ?? null;
  const blockedOnDesktop = detectBlockedState({
    status: navigationStatusCode,
    textSample: snapshot.textSample
  });
  const desktopScreenshotFile = `screenshots/page-${String(index).padStart(2, "0")}-desktop.png`;
  await desktopPage.screenshot({
    path: join(screenshotsDir, `page-${String(index).padStart(2, "0")}-desktop.png`),
    fullPage: true
  });

  const mobileContext = await browser.newContext({
    ...iPhone,
    ignoreHTTPSErrors: true,
    locale: humanLocale,
    timezoneId: humanTimezone,
    extraHTTPHeaders: {
      ...realisticHeaders,
      "Sec-CH-UA-Mobile": "?1",
      "Sec-CH-UA-Platform": '"iOS"'
    }
  });
  const mobilePage = await mobileContext.newPage();

  await mobilePage.goto(url, {
    waitUntil: "domcontentloaded",
    timeout: 25000
  });
  await mobilePage.waitForLoadState("load").catch(() => {});
  await waitForChallenge(mobilePage);
  await humanize(mobilePage, iPhone.viewport);

  const mobileSnapshot = await collectPageSnapshot(mobilePage);
  const mobileBlocked = detectBlockedState({
    status: navigationStatusCode,
    textSample: mobileSnapshot.textSample
  });
  const mobileLoading = detectLoadingState({
    textSample: mobileSnapshot.textSample,
    blocked: blockedOnDesktop || mobileBlocked
  });
  const mobileScreenshotFile = `screenshots/page-${String(index).padStart(2, "0")}-mobile.png`;
  await mobilePage.screenshot({
    path: join(screenshotsDir, `page-${String(index).padStart(2, "0")}-mobile.png`),
    fullPage: true
  });

  const linkMap = new Map();
  for (const link of snapshot.links) {
    if (!link.resolved || !isHttpUrl(link.resolved)) continue;
    const normalized = normalizeUrl(link.resolved);
    if (!linkMap.has(normalized)) {
      linkMap.set(normalized, null);
    }
  }

  for (const linkUrl of linkMap.keys()) {
    linkMap.set(linkUrl, await checkLink(requestContext, linkUrl));
  }

  const brokenLinks = snapshot.links
    .filter((link) => link.resolved && isHttpUrl(link.resolved))
    .map((link) => {
      const result = linkMap.get(normalizeUrl(link.resolved));
      return result && !result.ok
        ? {
            url: result.finalUrl || link.resolved,
            text: link.text,
            status: result.status,
            statusText: result.statusText
          }
        : null;
    })
    .filter(Boolean);

  const brokenImages = snapshot.images
    .filter((image) => image.url && (!image.complete || image.naturalWidth === 0))
    .map((image) => ({
      url: image.url,
      alt: image.alt,
      reason: "Browser reported an image that did not render correctly."
    }));

  for (const failed of failedImageRequests) {
    if (!brokenImages.some((item) => item.url === failed.url)) {
      brokenImages.push({
        url: failed.url,
        alt: "",
        reason: failed.reason
      });
    }
  }

  const navigationCandidates = Array.from(linkMap.keys()).filter((linkUrl) => {
    return new URL(linkUrl).origin === origin && isLikelyPageUrl(linkUrl);
  });

  const auditWarnings = [];

  if (blockedOnDesktop || mobileBlocked) {
    auditWarnings.push({
      type: "Access restricted",
      detail:
        "The page appears to be protected by access restrictions or anti-bot checks. Layout checks were skipped to avoid false positives."
    });
  } else if (mobileLoading) {
    auditWarnings.push({
      type: "Stalled loading state",
      detail:
        "The mobile page still displayed a loading state after the wait period. Layout checks were skipped because the interface may not have fully rendered."
    });
  }

  const shouldSkipMobileIssues = blockedOnDesktop || mobileBlocked || mobileLoading;

  await desktopContext.close();
  await mobileContext.close();

  return {
    url,
    title: snapshot.title,
    navigationStatus: response ? `HTTP ${response.status()}` : "No response",
    statusCode: navigationStatusCode,
    accessRestricted: blockedOnDesktop || mobileBlocked,
    desktopScreenshot: `./${desktopScreenshotFile}`,
    mobileScreenshot: `./${mobileScreenshotFile}`,
    checkedLinks: linkMap.size,
    brokenLinks,
    brokenImages,
    mobileIssues: shouldSkipMobileIssues ? [] : mobileSnapshot.mobileIssues,
    auditWarnings,
    navigationCandidates
  };
}

function buildSummary(pages) {
  return pages.reduce(
    (accumulator, page) => {
      accumulator.pagesAudited += 1;
      accumulator.checkedLinks += page.checkedLinks;
      accumulator.brokenLinks += page.brokenLinks.length;
      accumulator.brokenImages += page.brokenImages.length;
      accumulator.mobileIssues += page.mobileIssues.length;
      accumulator.blockedPages += page.accessRestricted ? 1 : 0;
      accumulator.warningCount += page.auditWarnings.length;
      return accumulator;
    },
    {
      pagesAudited: 0,
      checkedLinks: 0,
      brokenLinks: 0,
      brokenImages: 0,
      mobileIssues: 0,
      blockedPages: 0,
      warningCount: 0
    }
  );
}

export async function auditSite({
  targetUrl,
  outputDir = defaultOutputDir,
  maxPages = 5
}) {
  const browser = await chromium.launch({
    headless: true,
    args: launchArgs
  });
  const requestContext = await request.newContext({
    ignoreHTTPSErrors: true,
    userAgent: realisticUserAgent,
    extraHTTPHeaders: realisticHeaders
  });

  const screenshotsDir = join(outputDir, "screenshots");
  await mkdir(screenshotsDir, { recursive: true });

  const startTime = Date.now();
  const origin = new URL(targetUrl).origin;
  const queue = [targetUrl];
  const queued = new Set(queue);
  const visited = new Set();
  const pages = [];

  while (queue.length && pages.length < maxPages) {
    const current = queue.shift();
    if (!current || visited.has(current)) continue;

    visited.add(current);

    try {
      const pageResult = await auditSinglePage({
        browser,
        requestContext,
        url: current,
        origin,
        index: pages.length + 1,
        screenshotsDir
      });
      pages.push(pageResult);

      for (const candidate of pageResult.navigationCandidates) {
        if (!visited.has(candidate) && !queued.has(candidate) && pages.length + queue.length < maxPages) {
          queue.push(candidate);
          queued.add(candidate);
        }
      }
    } catch (error) {
      pages.push({
        url: current,
        title: current,
        navigationStatus: error.message,
        statusCode: null,
        accessRestricted: false,
        desktopScreenshot: "",
        mobileScreenshot: "",
        checkedLinks: 0,
        brokenLinks: [],
        brokenImages: [],
        mobileIssues: [],
        auditWarnings: [
          {
            type: "Audit failure",
            detail: error.message
          }
        ],
        navigationCandidates: []
      });
    }
  }

  const summary = buildSummary(pages);
  const report = {
    targetUrl,
    generatedAt: new Date().toLocaleString("tr-TR"),
    durationMs: Date.now() - startTime,
    summary,
    pages
  };

  await writeFile(join(outputDir, "audit-result.json"), JSON.stringify(report, null, 2), "utf8");
  await writeFile(join(outputDir, "index.html"), buildReportHtml(report), "utf8");

  await requestContext.dispose();
  await browser.close();

  return report;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    const options = parseArgs(process.argv.slice(2));
    const report = await auditSite(options);
    console.log(
      `Audit completed: ${report.summary.pagesAudited} page(s), ${report.summary.brokenLinks} broken link(s), ${report.summary.brokenImages} broken image(s), ${report.summary.mobileIssues} mobile issue(s).`
    );
    console.log(`Report: ${join(options.outputDir, "index.html")}`);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
