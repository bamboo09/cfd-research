"""Ablate one comparison convention at a time, using the same two force series."""
import csv
import json
import sys
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skills/cfd-research/scripts"))
from window_stats import stats

START, END = 1, 4


def scenario(group, omitted):
    path = HERE / f"input/runs/{group}.csv"
    with path.open(newline="") as f:
        data = [(float(r["t_s"]), float(r["F_mN"])) for r in csv.DictReader(f)]
    start, end = START, END
    if omitted == "window":
        start, end = data[0][0], data[-1][0]
    result = stats(path, "t_s", "F_mN", start, end)
    mean_mn = result["time_mean"]
    if omitted == "time_weight":
        inside = [y for t, y in data if start < t < end]
        mean_mn = mean([*result["endpoint_values"], *inside])
    speed = 0.030 if omitted == "common_reference" and group == "B" else 0.020
    reference_n = 0.5 * 1000 * speed**2 * 0.001
    return mean_mn * 1e-3 / reference_n


if __name__ == "__main__":
    output = {}
    for omitted in ("none", "window", "time_weight", "common_reference"):
        a, b = (scenario(g, omitted) for g in "AB")
        output[omitted] = {"A": a, "B": b, "B_minus_A": b-a}
    print(json.dumps(output, indent=2))
