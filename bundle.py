#!/usr/bin/env python3
"""Bundle a folder of Typst sources into a .typz file.

A .typz file is a plain zip archive with a .typz extension.

The folder must have a typst.toml at its root that contains a [project] section.

Usage:
    python typz_bundle.py path/to/projectname            # -> ./projectname.typz
    python typz_bundle.py path/to/projectname -o out.typz
"""

import argparse
import sys
import zipfile
from pathlib import Path


def has_project_section(toml_path: Path) -> bool:
    """Return True if any line in the file is exactly "[project]" (ignoring surrounding whitespace)."""
    with toml_path.open("r", encoding="utf-8", errors="replace") as f:
        return any(line.strip() == "[project]" for line in f)


def bundle(src: Path, out: Path) -> int:
    out_resolved = out.resolve()
    count = 0
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.rglob("*")):
            # Never pack the output archive into itself.
            if path.resolve() == out_resolved:
                continue
            arcname = path.relative_to(src).as_posix()
            if path.is_dir():
                # Keep empty directories; non-empty ones are implied by their files.
                if not any(path.iterdir()):
                    zf.writestr(arcname + "/", "")
            elif path.is_file():
                zf.write(path, arcname)
                count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bundle a folder of Typst sources into a .typz (zip) file."
    )
    parser.add_argument("folder", help="Folder containing the Typst project")
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: <foldername>.typz in the current directory)",
    )
    args = parser.parse_args()

    src = Path(args.folder)
    if not src.is_dir():
        print(f"Error: '{src}' is not a directory.", file=sys.stderr)
        return 1

    toml_path = src / "typst.toml"
    if not toml_path.is_file():
        print(f"Error: no typst.toml found at the root of '{src}'.", file=sys.stderr)
        return 1
    if not has_project_section(toml_path):
        print(f"Error: '{toml_path}' has no [project] section.", file=sys.stderr)
        return 1

    out = Path(args.output) if args.output else Path(src.resolve().name + ".typz")

    n = bundle(src, out)
    print(f"Wrote {out} ({n} file{'s' if n != 1 else ''}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())