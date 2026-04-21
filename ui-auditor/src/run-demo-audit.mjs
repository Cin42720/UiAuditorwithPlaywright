import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { auditSite } from "./audit-site.mjs";
import { createStaticServer } from "./static-server.mjs";

const currentDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(currentDir, "..");
const demoRoot = join(projectRoot, "demo-site");
const outputDir = resolve(projectRoot, "..", "output", "ui-auditor", "demo-report");

const { url, close } = await createStaticServer(demoRoot, { port: 4173 });

try {
  const report = await auditSite({
    targetUrl: `${url}/index.html`,
    outputDir,
    maxPages: 4
  });

  console.log(
    `Demo audit finished with ${report.summary.brokenLinks} broken link(s), ${report.summary.brokenImages} broken image(s) and ${report.summary.mobileIssues} mobile issue(s).`
  );
  console.log(`Open: ${join(outputDir, "index.html")}`);
} finally {
  await close();
}
