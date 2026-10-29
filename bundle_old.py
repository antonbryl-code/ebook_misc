#!/usr/bin/env python3
"""Bundle a folder of Typst sources into an EPUB-style zipped file.

Layout of the resulting archive:

    mimetype                 (first entry, stored uncompressed, no extra field)
    META-INF/container.xml   (rootfile -> content/<entry point>)
    content/...              (the source folder, recursively)

Usage:
    python bundle.py FOLDER ENTRY_POINT [-o OUTPUT_NAME.epubst]

ENTRY_POINT is a path to the root .typ file, relative to FOLDER.
"""

import argparse
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.sax.saxutils import quoteattr

EPUBST_MIMETYPE = b"application/epubst+zip"

CONTAINER_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path={full_path} media-type="text/vnd.typst"/>
  </rootfiles>
</container>
"""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder", type=Path, help="folder with the Typst sources")
    p.add_argument("main_file", type=Path,
                   help="main .typ file, relative to the folder")
    p.add_argument("-o", "--output", type=Path,
                   help="output path (default: <folder name>.epubst next to the folder)")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    folder = args.folder.resolve()
    if not folder.is_dir():
        sys.exit(f"error: {args.folder} is not a directory")

    if args.main_file.is_absolute():
        sys.exit("error: main_file must be a path relative to the folder")
    main_file_abs = (folder / args.main_file).resolve()
    try:
        main_file_rel = main_file_abs.relative_to(folder)
    except ValueError:
        sys.exit("error: main file must be inside the folder")
    if not main_file_abs.is_file():
        sys.exit(f"error: main file {main_file_rel} does not exist")
    if main_file_abs.suffix.lower() != ".typ":
        sys.exit("error: main_file must be a .typ file")

    output_file_name = (args.output or folder.parent / f"{folder.name}.epubst").resolve()
    if output_file_name.suffix.lower() != ".epubst":
        output_file_name = output_file_name.with_name(output_file_name.name + ".epubst")

    main_file_in_zip = PurePosixPath("content", *main_file_rel.parts).as_posix()
    container_xml = CONTAINER_TEMPLATE.format(
        full_path=quoteattr(main_file_in_zip),
    )

    with zipfile.ZipFile(output_file_name, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. mimetype: must be first, uncompressed, no extra field.
        info = zipfile.ZipInfo("mimetype")
        info.compress_type = zipfile.ZIP_STORED
        zf.writestr(info, EPUBST_MIMETYPE)

        # 2. META-INF/container.xml
        zf.writestr("META-INF/container.xml", container_xml)

        # 3. The source folder, renamed to "content"
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.resolve() == output_file_name:
                continue
            rel = path.relative_to(folder)
            arcname = PurePosixPath("content", *rel.parts).as_posix()
            zf.write(path, arcname)

    print(f"Wrote {output_file_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
