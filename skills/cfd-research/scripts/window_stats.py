"""Calculate scalar statistics in a covered time window of a numeric CSV."""
import argparse
import csv
import hashlib
import io
import json
import math
from bisect import bisect_left, bisect_right
from pathlib import Path


def stats(path, time_col, value_col, start, end):
    if not all(map(math.isfinite, (start, end))) or start >= end:
        raise ValueError("window must have finite, increasing bounds")
    if time_col == value_col:
        raise ValueError("time and value must be distinct columns")
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    headers = reader.fieldnames or []
    if any(headers.count(name) != 1 for name in (time_col, value_col)):
        raise ValueError("each selected column must appear exactly once")
    times, values = [], []
    for row in reader:
        try:
            t, y = float(row[time_col]), float(row[value_col])
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid numeric data at line {reader.line_num}") from exc
        if not math.isfinite(t) or not math.isfinite(y):
            raise ValueError(f"non-finite data at line {reader.line_num}")
        if times and t <= times[-1]:
            raise ValueError(f"time repeats or reverses at line {reader.line_num}")
        times.append(t)
        values.append(y)
    if len(times) < 2 or start < times[0] or end > times[-1]:
        raise ValueError("input does not cover the requested window")

    def endpoint(t):
        i = bisect_left(times, t)
        if times[i] == t:
            return values[i]
        fraction = (t - times[i-1]) / (times[i] - times[i-1])
        return values[i-1] * (1 - fraction) + values[i] * fraction

    left, right = bisect_right(times, start), bisect_left(times, end)
    t = [start, *times[left:right], end]
    y = [endpoint(start), *values[left:right], endpoint(end)]
    dt = [b - a for a, b in zip(t, t[1:])]
    time_mean = math.fsum((step / (end-start)) * (a/2 + b/2)
                          for step, a, b in zip(dt, y, y[1:]))
    low, high = min(y), max(y)
    return {
        "file": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
        "time_column": time_col, "value_column": value_col, "window": [start, end],
        "endpoint_values": [y[0], y[-1]], "method": "piecewise linear",
        "input_rows": len(times), "integration_intervals": len(dt),
        "max_source_interval_in_window": max(times[i+1] - times[i] for i in range(left-1, right)),
        "time_mean": time_mean, "min": low, "max": high,
        "midrange": low/2 + high/2, "peak_to_peak": high-low,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--time", required=True)
    parser.add_argument("--value", required=True)
    parser.add_argument("--window", nargs=2, type=float, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(stats(args.csv, args.time, args.value, *args.window),
                         ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, csv.Error, OverflowError) as exc:
        parser.exit(1, f"{exc}\n")
