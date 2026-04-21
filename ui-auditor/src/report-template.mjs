function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function metricCard(label, value, tone = "neutral") {
  return `
    <article class="metric metric--${tone}">
      <span class="metric__label">${escapeHtml(label)}</span>
      <strong class="metric__value">${escapeHtml(value)}</strong>
    </article>
  `;
}

function issueList(title, items, emptyText) {
  if (!items.length) {
    return `
      <section class="issue-panel">
        <header class="issue-panel__header">
          <h4>${escapeHtml(title)}</h4>
        </header>
        <p class="issue-panel__empty">${escapeHtml(emptyText)}</p>
      </section>
    `;
  }

  return `
    <section class="issue-panel">
      <header class="issue-panel__header">
        <h4>${escapeHtml(title)}</h4>
        <span class="pill">${items.length}</span>
      </header>
      <ul class="issue-list">
        ${items
          .map(
            (item) => `
              <li class="issue-list__item">
                <strong>${escapeHtml(item.label)}</strong>
                <span>${escapeHtml(item.detail)}</span>
              </li>
            `
          )
          .join("")}
      </ul>
    </section>
  `;
}

function renderPageCard(page) {
  const issueCount =
    page.brokenLinks.length + page.brokenImages.length + page.mobileIssues.length;
  const totalFlags = issueCount + page.auditWarnings.length;
  const skippedLayout = page.auditWarnings.some(
    (item) => item.type === "Access restricted" || item.type === "Stalled loading state"
  );

  return `
    <article class="page-card">
      <header class="page-card__header">
        <div>
          <p class="eyebrow">Audited page</p>
          <h3>${escapeHtml(page.title || page.url)}</h3>
          <a href="${escapeHtml(page.url)}" target="_blank" rel="noreferrer">${escapeHtml(page.url)}</a>
        </div>
        <div class="page-card__meta">
          <span class="chip">${page.navigationStatus}</span>
          <span class="chip chip--warn">${totalFlags} flag</span>
        </div>
      </header>

      ${
        page.auditWarnings.length
          ? `
            <section class="warning-strip">
              ${page.auditWarnings
                .map(
                  (warning) => `
                    <article class="warning-card">
                      <strong>${escapeHtml(warning.type)}</strong>
                      <span>${escapeHtml(warning.detail)}</span>
                    </article>
                  `
                )
                .join("")}
            </section>
          `
          : ""
      }

      <div class="preview-grid">
        <figure class="preview">
          <img src="${escapeHtml(page.desktopScreenshot)}" alt="Desktop preview for ${escapeHtml(page.url)}" />
          <figcaption>Desktop</figcaption>
        </figure>
        <figure class="preview">
          <img src="${escapeHtml(page.mobileScreenshot)}" alt="Mobile preview for ${escapeHtml(page.url)}" />
          <figcaption>iPhone 13</figcaption>
        </figure>
      </div>

      <div class="issue-grid">
        ${issueList(
          "Broken links",
          page.brokenLinks.map((item) => ({
            label: item.text || item.url,
            detail: `${item.url} - ${item.statusText}`
          })),
          "No broken link detected on this page."
        )}
        ${issueList(
          "Broken images",
          page.brokenImages.map((item) => ({
            label: item.alt || item.url,
            detail: item.reason
          })),
          "All detected images loaded successfully."
        )}
        ${issueList(
          "Mobile layout",
          page.mobileIssues.map((item) => ({
            label: item.type,
            detail: item.detail
          })),
          skippedLayout
            ? "Layout checks were skipped because the page was blocked or remained in loading state."
            : "No mobile overlap issue detected."
        )}
      </div>
    </article>
  `;
}

export function buildReportHtml(report) {
  const totalIssues =
    report.summary.brokenLinks +
    report.summary.brokenImages +
    report.summary.mobileIssues;

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>UI Auditor Report</title>
    <style>
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
    </style>
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
              <li><span>Target</span><strong>${escapeHtml(report.targetUrl)}</strong></li>
              <li><span>Generated</span><strong>${escapeHtml(report.generatedAt)}</strong></li>
              <li><span>Pages audited</span><strong>${report.summary.pagesAudited}</strong></li>
              <li><span>Total issues</span><strong>${totalIssues}</strong></li>
            </ul>
          </section>
          <section class="metrics">
            ${metricCard("Broken links", report.summary.brokenLinks, report.summary.brokenLinks ? "warn" : "ok")}
            ${metricCard("Broken images", report.summary.brokenImages, report.summary.brokenImages ? "warn" : "ok")}
            ${metricCard("Mobile issues", report.summary.mobileIssues, report.summary.mobileIssues ? "warn" : "ok")}
            ${metricCard("Checked links", report.summary.checkedLinks, "neutral")}
          </section>
        </div>
      </section>

      ${
        report.summary.blockedPages
          ? `
            <section class="panel panel--note">
              <p class="eyebrow">Access note</p>
              <p>
                ${report.summary.blockedPages} page(s) appeared to be protected by access restrictions or anti-bot checks.
                For those pages, layout findings were intentionally skipped to avoid misleading results.
              </p>
            </section>
          `
          : ""
      }

      <section>
        <h2 class="section-title">Page findings</h2>
        <div class="pages">
          ${report.pages.map(renderPageCard).join("")}
        </div>
      </section>
    </main>
  </body>
</html>`;
}
