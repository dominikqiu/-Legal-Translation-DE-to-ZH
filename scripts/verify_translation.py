#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校对辅助：边码 / 压缩段落 / 脚注 三项自动检查
（对应 SKILL.md「校对工作流」第 1、2、3 步）

用法：
    python3 scripts/verify_translation.py 译文.md --start 756 --end 932
    python3 scripts/verify_translation.py 译文.md            # 不做边码范围检查

输出：
    - 缺失边码清单（按范围）
    - 压缩段落残留（**NNN–NNN** 且跨度 > 1）
    - 脚注引用/定义对撞结果（缺失定义、未被引用的定义）

局限：本脚本仅能"缩小范围"，最终判断（漏译/错译/杜撰）必须逐段人工对照原文。
"""
import argparse
import re
import sys
from pathlib import Path


def check_page_refs(text: str, start: int | None, end: int | None) -> None:
    """边码检查：提取 **NNN** 加粗边码，与 [start, end] 全集对撞。"""
    found = set()
    for m in re.finditer(r"\*\*(\d{3})\*\*", text):
        n = int(m.group(1))
        if start is None or end is None or start <= n <= end:
            found.add(n)
    if start is not None and end is not None:
        missing = sorted(set(range(start, end + 1)) - found)
        print(f"[边码] 范围内共 {end - start + 1} 段，命中 {len(found)}，缺失 {len(missing)}")
        if missing:
            print(f"       缺失：{missing}")
    else:
        print(f"[边码] 检出 {len(found)} 个加粗边码（未指定范围，跳过对撞）")


def check_compressed(text: str) -> None:
    """压缩段落检查：**NNN–NNN** 且 end - start > 1。"""
    bad = []
    for m in re.finditer(r"\*\*(\d{3})[–-](\d{3})\*\*", text):
        s, e = int(m.group(1)), int(m.group(2))
        if e - s > 1:
            bad.append(f"{s}–{e}")
    print(f"[压缩段落] 残留 {len(bad)} 处" + (f"：{bad}" if bad else ""))


def check_footnotes(text: str) -> None:
    """脚注检查：引用集合 vs 定义集合。"""
    body_refs = {}
    for line in text.split("\n"):
        for m in re.finditer(r"\[\^([^\]]+)\]", line):
            if not line[: m.start()].rstrip().endswith("]:"):
                body_refs[m.group(1)] = True
    defs = {m.group(1): True for m in re.finditer(r"(?m)^\[\^([^\]]+)\]:", text)}
    missing = sorted(set(body_refs) - set(defs))
    unused = sorted(set(defs) - set(body_refs))
    print(
        f"[脚注] 引用 {len(body_refs)} | 定义 {len(defs)} | "
        f"缺失定义 {len(missing)} | 未被引用 {len(unused)}"
    )
    if missing:
        print(f"       缺失定义：{missing}")
    if unused:
        print(f"       未被引用：{unused}")


def main() -> int:
    ap = argparse.ArgumentParser(description="校对辅助：边码/压缩段落/脚注三项检查")
    ap.add_argument("translation", help="中文译稿 .md 路径")
    ap.add_argument("--start", type=int, default=None, help="边码范围起点（如 756）")
    ap.add_argument("--end", type=int, default=None, help="边码范围终点（如 932）")
    args = ap.parse_args()

    path = Path(args.translation)
    if not path.is_file():
        print(f"[ERR] 文件不存在：{path}", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")

    check_page_refs(text, args.start, args.end)
    check_compressed(text)
    check_footnotes(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
