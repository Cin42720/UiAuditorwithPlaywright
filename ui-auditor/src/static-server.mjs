import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";

const MIME_TYPES = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml; charset=utf-8"
};

export async function createStaticServer(rootDir, { port = 0 } = {}) {
  const absoluteRoot = resolve(rootDir);

  const server = createServer(async (req, res) => {
    try {
      const requestPath = req.url === "/" ? "/index.html" : req.url;
      const filePath = normalize(join(absoluteRoot, requestPath));

      if (!filePath.startsWith(absoluteRoot)) {
        res.writeHead(403, {
          "Content-Type": "text/plain; charset=utf-8"
        });
        res.end("Forbidden");
        return;
      }

      const content = await readFile(filePath);
      const extension = extname(filePath);

      res.writeHead(200, {
        "Content-Type": MIME_TYPES[extension] || "application/octet-stream"
      });
      res.end(content);
    } catch {
      res.writeHead(404, {
        "Content-Type": "text/plain; charset=utf-8"
      });
      res.end("Not found");
    }
  });

  await new Promise((resolveServer) => {
    server.listen(port, "127.0.0.1", resolveServer);
  });

  const address = server.address();
  const actualPort = typeof address === "object" && address ? address.port : port;
  const url = `http://127.0.0.1:${actualPort}`;

  return {
    server,
    url,
    close: () =>
      new Promise((resolveClose, rejectClose) => {
        server.close((error) => (error ? rejectClose(error) : resolveClose()));
      })
  };
}
