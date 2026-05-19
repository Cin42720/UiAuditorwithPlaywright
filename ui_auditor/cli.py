from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .static_server import create_static_server


DEMO_SITE_DIR = Path(__file__).resolve().parent / "demo_site"
DEFAULT_OUTPUT_DIR = Path("output/ui-auditor/latest").resolve()
DEMO_OUTPUT_DIR = Path("output/ui-auditor/demo-report").resolve()


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ui-auditor",
        description="Audit a site with Python Playwright and generate HTML/JSON reports.",
    )
    subparsers = parser.add_subparsers(dest="command")

    audit_parser = subparsers.add_parser("audit", help="audit a real site")
    audit_parser.add_argument("url", help="target URL")
    audit_parser.add_argument("--max-pages", type=positive_int, default=5)
    audit_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)

    demo_parser = subparsers.add_parser("demo", help="run the bundled demo audit")
    demo_parser.add_argument("--max-pages", type=positive_int, default=4)
    demo_parser.add_argument("--output", type=Path, default=DEMO_OUTPUT_DIR)
    demo_parser.add_argument("--port", type=int, default=4173)

    serve_parser = subparsers.add_parser("serve-demo", help="serve the bundled demo site")
    serve_parser.add_argument("--port", type=int, default=4173)

    return parser


def run_audit(args: argparse.Namespace) -> int:
    from .auditor import audit_site, normalize_url

    report = audit_site(
        target_url=normalize_url(args.url),
        output_dir=args.output,
        max_pages=args.max_pages,
    )
    print(
        "Audit completed: "
        f"{report['summary']['pagesAudited']} page(s), "
        f"{report['summary']['brokenLinks']} broken link(s), "
        f"{report['summary']['brokenImages']} broken image(s), "
        f"{report['summary']['mobileIssues']} mobile issue(s)."
    )
    print(f"Report: {Path(args.output).resolve() / 'index.html'}")
    return 0


def run_demo(args: argparse.Namespace) -> int:
    from .auditor import audit_site

    server = create_static_server(DEMO_SITE_DIR, port=args.port)
    try:
        report = audit_site(
            target_url=f"{server.url}/index.html",
            output_dir=args.output,
            max_pages=args.max_pages,
        )
        print(
            "Demo audit finished with "
            f"{report['summary']['brokenLinks']} broken link(s), "
            f"{report['summary']['brokenImages']} broken image(s) and "
            f"{report['summary']['mobileIssues']} mobile issue(s)."
        )
        print(f"Open: {Path(args.output).resolve() / 'index.html'}")
        return 0
    finally:
        server.close()


def serve_demo(args: argparse.Namespace) -> int:
    server = create_static_server(DEMO_SITE_DIR, port=args.port)
    print(f"Demo site is ready at {server.url}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        return 0
    finally:
        server.close()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command_names = {"audit", "demo", "serve-demo", "-h", "--help"}
    if argv and argv[0] not in command_names:
        argv.insert(0, "audit")

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "audit":
        return run_audit(args)
    if args.command == "demo":
        return run_demo(args)
    if args.command == "serve-demo":
        return serve_demo(args)

    parser.print_help()
    return 0
