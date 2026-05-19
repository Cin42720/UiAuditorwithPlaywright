from __future__ import annotations

from html import escape
from typing import Any


REPORT_CSS = """
      @import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Instrument+Serif:ital@0;1&display=swap");

      :root {
        --bg: #f6f0e8;
        --panel: rgba(255, 250, 243, 0.92);
        --ink: #17242a;
        --muted: #5e6a6f;
        --line: rgba(23, 36, 42, 0.12);
        --accent: #ec6d3a;
        --accent-dark: #ba4f1f;
        --ok: #1e7a57;
        --warn: #c54e2f;
        --shadow: 0 30px 70px rgba(46, 26, 13, 0.14);
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        font-family: "Space Grotesk", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top, rgba(236, 109, 58, 0.18), transparent 24%),
          linear-gradient(180deg, #fffdf9 0%, var(--bg) 100%);
      }

      .shell {
        width: min(1180px, calc(100% - 32px));
        margin: 0 auto;
        padding: 42px 0 64px;
      }

      .hero {
        display: grid;
        gap: 24px;
        margin-bottom: 28px;
      }

      .eyebrow {
        margin: 0 0 10px;
        font-size: 12px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--accent-dark);
        font-weight: 700;
      }

      .hero h1 {
        margin: 0;
        font-family: "Instrument Serif", serif;
        font-size: clamp(40px, 8vw, 86px);
        line-height: 0.95;
        font-weight: 400;
      }

      .hero p {
        margin: 0;
        max-width: 760px;
        color: var(--muted);
        font-size: 18px;
        line-height: 1.7;
      }

      .hero-grid {
        display: grid;
        gap: 18px;
        grid-template-columns: 1.3fr 1fr;
      }

      .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 28px;
        box-shadow: var(--shadow);
        padding: 24px;
        backdrop-filter: blur(12px);
      }

      .panel--note {
        margin-bottom: 28px;
      }

      .scope-list {
        display: grid;
        gap: 10px;
        margin: 0;
        padding: 0;
        list-style: none;
      }

      .scope-list li {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        padding-bottom: 10px;
        border-bottom: 1px solid var(--line);
      }

      .scope-list li:last-child {
        border-bottom: none;
        padding-bottom: 0;
      }

      .metrics {
        display: grid;
        gap: 14px;
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }

      .metric {
        border-radius: 22px;
        padding: 18px;
        background: white;
        border: 1px solid var(--line);
      }

      .metric--warn {
        background: #fff0ea;
      }

      .metric--ok {
        background: #eaf7f0;
      }

      .metric__label {
        display: block;
        color: var(--muted);
        font-size: 13px;
        margin-bottom: 8px;
      }

      .metric__value {
        font-size: clamp(24px, 4vw, 38px);
      }

      .section-title {
        margin: 0 0 16px;
        font-size: 28px;
      }

      .pages {
        display: grid;
        gap: 22px;
        margin-top: 32px;
      }

      .page-card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 28px;
        padding: 24px;
        box-shadow: var(--shadow);
      }

      .page-card__header {
        display: flex;
        justify-content: space-between;
        gap: 18px;
        align-items: start;
        margin-bottom: 18px;
      }

      .page-card__header h3 {
        margin: 0 0 6px;
        font-size: 28px;
      }

      .page-card__header a {
        color: var(--muted);
        text-decoration: none;
        word-break: break-all;
      }

      .page-card__meta {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }

      .chip,
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 13px;
        font-weight: 700;
        background: #f1e4d6;
      }

      .chip--warn,
      .metric--warn .metric__value {
        color: var(--warn);
      }

      .warning-strip {
        display: grid;
        gap: 12px;
        margin-bottom: 18px;
      }

      .warning-card {
        display: grid;
        gap: 6px;
        padding: 16px 18px;
        border-radius: 18px;
        background: #fff0ea;
        border: 1px solid rgba(197, 78, 47, 0.18);
      }

      .warning-card strong {
        color: var(--warn);
      }

      .preview-grid {
        display: grid;
        gap: 16px;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        margin-bottom: 18px;
      }

      .preview {
        margin: 0;
        background: #fff;
        border-radius: 20px;
        border: 1px solid var(--line);
        overflow: hidden;
      }

      .preview img {
        display: block;
        width: 100%;
        height: clamp(280px, 38vw, 520px);
        object-fit: cover;
        object-position: top;
        background: #f7f3ed;
      }

      .preview figcaption {
        padding: 12px 14px;
        color: var(--muted);
        font-size: 13px;
      }

      .issue-grid {
        display: grid;
        gap: 14px;
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .issue-panel {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 18px;
      }

      .issue-panel__header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 12px;
      }

      .issue-panel__header h4 {
        margin: 0;
      }

      .issue-panel__empty {
        margin: 0;
        color: var(--muted);
        line-height: 1.6;
      }

      .issue-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 10px;
      }

      .issue-list__item {
        display: grid;
        gap: 4px;
        padding: 12px;
        border-radius: 14px;
        background: #fbf5ee;
      }

      .issue-list__item strong,
      .issue-list__item span {
        word-break: break-word;
      }

      @media (max-width: 980px) {
        .hero-grid,
        .metrics,
        .issue-grid {
          grid-template-columns: 1fr 1fr;
        }
      }

      @media (max-width: 720px) {
        .hero-grid,
        .metrics,
        .preview-grid,
        .issue-grid {
          grid-template-columns: 1fr;
        }

        .page-card__header {
          flex-direction: column;
        }
      }
"""


def escape_html(value: Any = "") -> str:
    return escape(str(value), quote=True)


def metric_card(label: str, value: Any, tone: str = "neutral") -> str:
    return f"""
    <article class="metric metric--{escape_html(tone)}">
      <span class="metric__label">{escape_html(label)}</span>
      <strong class="metric__value">{escape_html(value)}</strong>
    </article>
  """


def issue_list(title: str, items: list[dict[str, Any]], empty_text: str) -> str:
    if not items:
        return f"""
      <section class="issue-panel">
        <header class="issue-panel__header">
          <h4>{escape_html(title)}</h4>
        </header>
        <p class="issue-panel__empty">{escape_html(empty_text)}</p>
      </section>
    """

    rendered_items = "".join(
        f"""
              <li class="issue-list__item">
                <strong>{escape_html(item["label"])}</strong>
                <span>{escape_html(item["detail"])}</span>
              </li>
            """
        for item in items
    )

    return f"""
    <section class="issue-panel">
      <header class="issue-panel__header">
        <h4>{escape_html(title)}</h4>
        <span class="pill">{len(items)}</span>
      </header>
      <ul class="issue-list">
        {rendered_items}
      </ul>
    </section>
  """


def render_page_card(page: dict[str, Any]) -> str:
    issue_count = (
        len(page["brokenLinks"]) + len(page["brokenImages"]) + len(page["mobileIssues"])
    )
    total_flags = issue_count + len(page["auditWarnings"])
    skipped_layout = any(
        item["type"] in {"Access restricted", "Stalled loading state"}
        for item in page["auditWarnings"]
    )
    warnings = ""
    if page["auditWarnings"]:
        warning_cards = "".join(
            f"""
                    <article class="warning-card">
                      <strong>{escape_html(warning["type"])}</strong>
                      <span>{escape_html(warning["detail"])}</span>
                    </article>
                  """
            for warning in page["auditWarnings"]
        )
        warnings = f"""
            <section class="warning-strip">
              {warning_cards}
            </section>
          """

    return f"""
    <article class="page-card">
      <header class="page-card__header">
        <div>
          <p class="eyebrow">Audited page</p>
          <h3>{escape_html(page["title"] or page["url"])}</h3>
          <a href="{escape_html(page["url"])}" target="_blank" rel="noreferrer">{escape_html(page["url"])}</a>
        </div>
        <div class="page-card__meta">
          <span class="chip">{escape_html(page["navigationStatus"])}</span>
          <span class="chip chip--warn">{total_flags} flag</span>
        </div>
      </header>

      {warnings}

      <div class="preview-grid">
        <figure class="preview">
          <img src="{escape_html(page["desktopScreenshot"])}" alt="Desktop preview for {escape_html(page["url"])}" />
          <figcaption>Desktop</figcaption>
        </figure>
        <figure class="preview">
          <img src="{escape_html(page["mobileScreenshot"])}" alt="Mobile preview for {escape_html(page["url"])}" />
          <figcaption>iPhone 13</figcaption>
        </figure>
      </div>

      <div class="issue-grid">
        {issue_list(
          "Broken links",
          [
              {
                  "label": item["text"] or item["url"],
                  "detail": f"{item['url']} - {item['statusText']}",
              }
              for item in page["brokenLinks"]
          ],
          "No broken link detected on this page.",
        )}
        {issue_list(
          "Broken images",
          [
              {
                  "label": item["alt"] or item["url"],
                  "detail": item["reason"],
              }
              for item in page["brokenImages"]
          ],
          "All detected images loaded successfully.",
        )}
        {issue_list(
          "Mobile layout",
          [
              {
                  "label": item["type"],
                  "detail": item["detail"],
              }
              for item in page["mobileIssues"]
          ],
          "Layout checks were skipped because the page was blocked or remained in loading state."
          if skipped_layout
          else "No mobile overlap issue detected.",
        )}
      </div>
    </article>
  """


def build_report_html(report: dict[str, Any]) -> str:
    total_issues = (
        report["summary"]["brokenLinks"]
        + report["summary"]["brokenImages"]
        + report["summary"]["mobileIssues"]
    )
    blocked_note = ""
    if report["summary"]["blockedPages"]:
        blocked_note = f"""
            <section class="panel panel--note">
              <p class="eyebrow">Access note</p>
              <p>
                {report["summary"]["blockedPages"]} page(s) appeared to be protected by access restrictions or anti-bot checks.
                For those pages, layout findings were intentionally skipped to avoid misleading results.
              </p>
            </section>
          """

    page_cards = "".join(render_page_card(page) for page in report["pages"])

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>UI Auditor Report</title>
    <style>{REPORT_CSS}</style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div>
          <p class="eyebrow">Playwright powered inspection</p>
          <h1>UI Auditor</h1>
          <p>
            This audit checks broken links, image health and mobile layout collisions.
            It also captures desktop and iPhone screenshots so the report can be presented visually.
          </p>
        </div>
        <div class="hero-grid">
          <section class="panel">
            <p class="eyebrow">Scope</p>
            <ul class="scope-list">
              <li><span>Target</span><strong>{escape_html(report["targetUrl"])}</strong></li>
              <li><span>Generated</span><strong>{escape_html(report["generatedAt"])}</strong></li>
              <li><span>Pages audited</span><strong>{report["summary"]["pagesAudited"]}</strong></li>
              <li><span>Total issues</span><strong>{total_issues}</strong></li>
            </ul>
          </section>
          <section class="metrics">
            {metric_card("Broken links", report["summary"]["brokenLinks"], "warn" if report["summary"]["brokenLinks"] else "ok")}
            {metric_card("Broken images", report["summary"]["brokenImages"], "warn" if report["summary"]["brokenImages"] else "ok")}
            {metric_card("Mobile issues", report["summary"]["mobileIssues"], "warn" if report["summary"]["mobileIssues"] else "ok")}
            {metric_card("Checked links", report["summary"]["checkedLinks"], "neutral")}
          </section>
        </div>
      </section>

      {blocked_note}

      <section>
        <h2 class="section-title">Page findings</h2>
        <div class="pages">
          {page_cards}
        </div>
      </section>
    </main>
  </body>
</html>"""
