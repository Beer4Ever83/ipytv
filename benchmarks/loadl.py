"""Benchmark loadl on a synthetic playlist and compare runs of two ipytv versions.

Usage:
    python benchmarks/loadl.py run OUTPUT_JSON
    python benchmarks/loadl.py report BASE_LABEL HEAD_LABEL --base BASE_JSON... --head HEAD_JSON...
"""

import argparse
import json
import multiprocessing as mp
import platform
import sys
import time
from pathlib import Path

# 5k channels parse in-process on every OS; 500k use the process pool on every OS.
SIZES = {5_000: 15, 500_000: 3}
REGRESSION_THRESHOLD = 1.05


def make_rows(n: int) -> list[str]:
    rows = ['#EXTM3U x-tvg-url="http://e.com/epg.xml"']
    for i in range(n):
        rows += [
            f'#EXTINF:-1 tvg-id="id{i}" tvg-name="Ch {i}" tvg-logo="http://l/{i}.png" '
            f'group-title="G{i % 10}",Channel {i}',
            "#EXTVLCOPT:http-user-agent=Foo",
            f"http://example.com/stream/{i}.m3u8",
        ]
    return rows


def run(output: str) -> None:
    import ipytv
    from ipytv import playlist

    result = {
        "file": ipytv.__file__,
        "python": platform.python_version(),
        "os": platform.system(),
        "start_method": mp.get_start_method(),
        "cores": mp.cpu_count(),
        "ms": {},
    }
    for n, reps in SIZES.items():
        rows = make_rows(n)
        times = []
        for _ in range(reps):
            start = time.perf_counter()
            pl = playlist.loadl(rows)
            times.append(time.perf_counter() - start)
        if pl.length() != n:
            sys.exit(f"expected {n} channels, got {pl.length()}")
        result["ms"][str(n)] = min(times) * 1000
    Path(output).write_text(json.dumps(result), encoding="utf-8")


def report(base_label: str, head_label: str, base_files: list[str], head_files: list[str]) -> str:
    base = [json.loads(Path(f).read_text(encoding="utf-8")) for f in base_files]
    head = [json.loads(Path(f).read_text(encoding="utf-8")) for f in head_files]
    if {r["file"] for r in base} & {r["file"] for r in head}:
        sys.exit("base and head imported ipytv from the same location: the comparison would be meaningless")
    env = head[0]
    lines = [
        f"## loadl benchmark: {base_label} vs {head_label}",
        "",
        f"{env['os']}, Python {env['python']}, `{env['start_method']}` start method, {env['cores']} cores. "
        f"Best of {len(base)} alternating rounds.",
        "",
        f"| Channels | {base_label} | {head_label} | Change | Speed-up |",
        "|---|---|---|---|---|",
    ]
    for n in SIZES:
        b = min(r["ms"][str(n)] for r in base)
        h = min(r["ms"][str(n)] for r in head)
        ratio = h / b
        change = f"{round((ratio - 1) * 100):+d}%"
        if ratio > REGRESSION_THRESHOLD:
            change += " ⚠ slower"
        lines.append(f"| {n:,} | {b:,.1f} ms | {h:,.1f} ms | {change} | {b / h:.2f}x |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("output")
    report_parser = sub.add_parser("report")
    report_parser.add_argument("base_label")
    report_parser.add_argument("head_label")
    report_parser.add_argument("--base", nargs="+", required=True)
    report_parser.add_argument("--head", nargs="+", required=True)
    args = parser.parse_args()
    if args.command == "run":
        run(args.output)
    else:
        print(report(args.base_label, args.head_label, args.base, args.head), end="")
