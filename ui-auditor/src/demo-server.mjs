import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { createStaticServer } from "./static-server.mjs";

const currentDir = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(currentDir, "..");
const demoRoot = join(projectRoot, "demo-site");

const { url } = await createStaticServer(demoRoot, { port: 4173 });

console.log(`Demo site is ready at ${url}`);
