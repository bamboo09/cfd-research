"""Build an independent input directory from the SU2 v8.3.0 public release."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = "https://raw.githubusercontent.com/su2code"
CODE = f"{BASE}/SU2/v8.3.0"
DATA = f"{BASE}/TestCases/v8.3.0/navierstokes/poiseuille"
FILES = {
    "lam_poiseuille.cfg": (f"{CODE}/TestCases/navierstokes/poiseuille", "612e645ceede94241d4dfb13b7e66351c3824230b5ccef60b4ca63f7c1957573"),
    "profile_poiseuille.cfg": (f"{CODE}/TestCases/navierstokes/poiseuille", "b0f58b037a9d4bd49c7f9060a5d95047e9aa748e6afe2ac421998c8954988f0e"),
    "inlet_poiseuille.dat": (DATA, "9b43d3a95028c078f2f4f4043b77abcb5e1c44b5e5dea11cd7ed08db85ea2ae1"),
    "mesh_poiseuille_51x51.su2": (DATA, "faa14290a66d0fcec308c7c15dfb52113cf54b98d881dea5d852f6723b90fd3c"),
    "config_template.cfg": (CODE, "96598587fabc7fb43b338dc006031c82d6546573fd7dac4c4e6d2ac380e53745"),
}


def prepare(target):
    if target.exists():
        raise FileExistsError(f"choose a new directory: {target}")
    with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
        work = Path(tmp) / "input"
        work.mkdir()
        for name, (base, digest) in FILES.items():
            raw = subprocess.check_output(["curl", "-fsSL", "--retry", "2", "--max-time", "60",
                                           f"{base}/{name}"])
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError(f"upstream content changed: {name}")
            if name == "config_template.cfg":
                # Same template excerpt each agent received, one-based lines 1062–1091.
                (work / "format_excerpt.txt").write_bytes(b"".join(raw.splitlines(True)[1061:1091]))
            else:
                (work / name).write_bytes(raw)
        shutil.copyfile(HERE / "task.txt", work / "task.txt")
        work.rename(target)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    prepare(parser.parse_args().destination)
