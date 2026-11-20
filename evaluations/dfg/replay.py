"""Rebuild a published DFG cycle from the authors' archive or replay the bundled excerpt."""
import argparse
import csv
import hashlib
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "skills/cfd-research/scripts"))
from window_stats import stats

ARCHIVE_SHA = "a193c85f19966f5fd0935dfa92f30d646ea33b06dbf9942b74dcf67365ce6f6e"
MEMBER = "bdforces_q2_lv6_dt3"
START = 8.535625  # Phase offset in authors' plot_bench2.plt, drag_Q2_all.
CYCLE = HERE / "cycle.csv"


def extract(archive):
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError("unexpected archive digest")
    with zipfile.ZipFile(archive) as data:
        lines = data.read(MEMBER).decode("ascii").splitlines()
    if lines[0].split() != ["#", "timestep", "time", "bdc", "horiz", "vert"]:
        raise ValueError("unexpected source columns")
    rows = [line.split() for line in lines[1:] if line.strip()]
    times = [float(row[1]) for row in rows]
    lift = [float(row[4]) for row in rows]
    if any(a >= b for a, b in zip(times, times[1:])) or any(r[2] != "2" for r in rows):
        raise ValueError("unexpected time or boundary ordering")
    minima = [i for i in range(1, len(rows)-1) if lift[i-1] > lift[i] <= lift[i+1]]
    i0 = times.index(START)
    if i0 not in minima:
        raise ValueError("published origin is not a local lift minimum")
    i1 = minima[minima.index(i0)+1]
    with CYCLE.open("w", newline="") as out:
        writer = csv.writer(out, lineterminator="\n")
        writer.writerow(["time_s", "CD", "CL"])
        writer.writerows((r[1], r[3], r[4]) for r in rows[i0:i1+1])


def replay():
    with CYCLE.open(newline="") as f:
        rows = list(csv.DictReader(f))
    t0, t1 = (float(row["time_s"]) for row in (rows[0], rows[-1]))
    cd = stats(CYCLE, "time_s", "CD", t0, t1)
    cl = stats(CYCLE, "time_s", "CL", t0, t1)
    # Author table: Exemplary Results, Level 6, nominal k=1/200.
    published = {"CD_midrange": 3.1884, "CL_midrange": -0.0173, "St": 0.30188}
    computed = {"CD_midrange": cd["midrange"], "CL_midrange": cl["midrange"],
                "St": 0.1 / (t1 - t0)}  # St = D/(T*Umean), Umean = 1.
    return {"archive_sha256": ARCHIVE_SHA, "archive_member": MEMBER,
            "cycle_sha256": cd["sha256"], "rows": len(rows), "window_s": [t0, t1],
            "published": published, "computed": computed,
            "computed_minus_published": {k: v - published[k] for k, v in computed.items()},
            "time_means": {"CD": cd["time_mean"], "CL": cl["time_mean"]},
            "CL_peak_to_peak": cl["peak_to_peak"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="re-extract cycle.csv from this verified zip")
    args = parser.parse_args()
    if args.archive:
        extract(args.archive)
    print(json.dumps(replay(), indent=2))
