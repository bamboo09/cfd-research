"""Save or compare the files of a CFD input tree. Store the manifest outside it."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def snapshot(root):
    result = {}

    def visit(directory):
        for path in directory.iterdir():
            key = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[key] = {"link": os.readlink(path)}
            elif path.is_dir():
                visit(path)
            elif path.is_file():
                digest = hashlib.sha256()
                with path.open("rb") as data:
                    for block in iter(lambda: data.read(1024 * 1024), b""):
                        digest.update(block)
                result[key] = {"sha256": digest.hexdigest(), "mode": path.stat().st_mode & 0o777}
            else:
                raise ValueError(f"unsupported file type: {path}")

    visit(root)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["save", "diff"])
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        root = args.root.resolve(strict=True)
        if args.manifest.resolve().is_relative_to(root):
            raise ValueError("place manifest outside scanned input tree")
        files = snapshot(root)
        if args.action == "save":
            with args.manifest.open("x", encoding="utf-8") as f:
                json.dump(files, f, sort_keys=True, indent=2, ensure_ascii=False)
                f.write("\n")
        else:
            before = json.loads(args.manifest.read_text(encoding="utf-8"))
            changes = {
                "added": sorted(files.keys() - before.keys()),
                "removed": sorted(before.keys() - files.keys()),
                "changed": sorted(k for k in files.keys() & before.keys() if files[k] != before[k]),
            }
            print(json.dumps(changes, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(1, f"{exc}\n")
