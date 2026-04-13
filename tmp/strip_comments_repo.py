import io
import os
import re
import subprocess
import tokenize
from pathlib import Path

ROOT = Path(r"D:/Bios")

EXTS_CLIKE = {".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".java", ".c", ".cpp", ".h", ".hpp"}
EXTS_HTML = {".html", ".htm"}
EXTS_PY = {".py"}

EXCLUDE_PARTS = {"venv", "node_modules", ".git", "static/react", "dist", "build"}


def tracked_files(root: Path):
    proc = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True, check=True)
    for rel in proc.stdout.splitlines():
        rel_norm = rel.replace('\\', '/').lower()
        if any(part in rel_norm for part in EXCLUDE_PARTS):
            continue
        yield root / rel


def strip_py_comments(src: str) -> str:
    out = []
    tokgen = tokenize.generate_tokens(io.StringIO(src).readline)
    for tok in tokgen:
        ttype, tstr, _, _, _ = tok
        if ttype == tokenize.COMMENT:
            continue
        out.append((ttype, tstr))
    return tokenize.untokenize(out)


def strip_clike_comments(src: str) -> str:
    out = []
    i = 0
    n = len(src)
    in_line = False
    in_block = False
    in_str = False
    str_char = ''
    escape = False

    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ''

        if in_line:
            if ch == '\n':
                in_line = False
                out.append(ch)
            i += 1
            continue

        if in_block:
            if ch == '*' and nxt == '/':
                in_block = False
                i += 2
            else:
                if ch == '\n':
                    out.append('\n')
                i += 1
            continue

        if in_str:
            out.append(ch)
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == str_char:
                in_str = False
            i += 1
            continue

        if ch in ('"', "'", '`'):
            in_str = True
            str_char = ch
            out.append(ch)
            i += 1
            continue

        if ch == '/' and nxt == '/':
            in_line = True
            i += 2
            continue

        if ch == '/' and nxt == '*':
            in_block = True
            i += 2
            continue

        out.append(ch)
        i += 1

    return ''.join(out)


def strip_html_comments(src: str) -> str:
    return re.sub(r"<!--.*?-->", "", src, flags=re.DOTALL)


def main():
    changed = 0
    touched = 0

    for fp in tracked_files(ROOT):
        ext = fp.suffix.lower()
        if ext not in EXTS_PY and ext not in EXTS_CLIKE and ext not in EXTS_HTML:
            continue
        touched += 1
        try:
            original = fp.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            original = fp.read_text(encoding='latin-1')

        if ext in EXTS_PY:
            updated = strip_py_comments(original)
        elif ext in EXTS_HTML:
            updated = strip_html_comments(original)
        else:
            updated = strip_clike_comments(original)

        if updated != original:
            fp.write_text(updated, encoding='utf-8', newline='')
            changed += 1

    print(f"Touched {touched} files, changed {changed} files.")


if __name__ == '__main__':
    main()
