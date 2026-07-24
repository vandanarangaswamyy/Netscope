from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from netprobe import __version__
from netprobe.probes import ProbeResult, diagnose


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netprobe",
        description="Diagnose network paths for the Netscope reliability lab.",
    )
    parser.add_argument("--version", action="version", version=f"netprobe {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)
    diagnose_parser = subparsers.add_parser("diagnose", help="Run DNS, TCP, HTTP, latency, route, and rejection checks.")
    diagnose_parser.add_argument("--target", default="http://localhost:8080", help="Base URL or host:port to diagnose.")
    diagnose_parser.add_argument("--prometheus-url", default="http://localhost:9090", help="Prometheus base URL.")
    diagnose_parser.add_argument("--samples", type=int, default=3, help="Number of latency samples to collect.")
    diagnose_parser.add_argument("--timeout", type=float, default=2.0, help="Per-check timeout in seconds.")
    diagnose_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def render_text(results: list[ProbeResult]) -> str:
    lines = []
    for result in results:
        lines.append(f"[{result.status.upper()}] {result.name}: {result.message}")
        for key, value in result.details.items():
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def exit_code(results: list[ProbeResult]) -> int:
    return 1 if any(result.status == "fail" for result in results) else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "diagnose":
        if args.samples <= 0:
            parser.error("--samples must be greater than zero")
        if args.timeout <= 0:
            parser.error("--timeout must be greater than zero")

        results = diagnose(
            args.target,
            prometheus_url=args.prometheus_url,
            samples=args.samples,
            timeout_seconds=args.timeout,
        )
        if args.json:
            print(json.dumps([asdict(result) for result in results], indent=2, sort_keys=True))
        else:
            print(render_text(results))
        return exit_code(results)

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
