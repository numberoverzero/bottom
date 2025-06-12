#!/usr/bin/env python
import fnmatch
import os
import pathlib
import subprocess
import sys

exclude = [
    "examples/migration/v2.2.0.py",
    "examples/migration/v3.0.0.py",
]
roots = [
    "src",
    "docs",
    "tests",
    "examples",
]

# glob
top = (pathlib.Path(os.path.dirname(os.path.realpath(__file__))) / "..").resolve()
files = []
for root in roots:
    dir = (top / root).resolve()
    assert dir.is_dir() and dir.exists()
    for path in dir.rglob("*.py"):
        path = str(path.relative_to(top))
        if not any(fnmatch.fnmatch(path, pat) for pat in exclude):
            files.append(path)
# info
yellow, bold, clear = "\033[93m", "\033[1m", "\033[0m"
print(f"{yellow}{bold}WARN{clear} workaround until https://github.com/astral-sh/ty/issues/176 is resolved")
for file in files:
    print(f"  check {file}")
print(f"  ({len(files)} files)")
# check
ty = top / ".venv/bin/ty"
args = [ty, "check", "-v", *[str(f) for f in files]]
subprocess.run(args, check=True, stdout=sys.stdout, stderr=sys.stderr, text=True)
