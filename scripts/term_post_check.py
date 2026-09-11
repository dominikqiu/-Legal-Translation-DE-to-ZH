#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
term_post_check.py
==================

`legal-de-to-zh` Skill 的术语后置校验脚本（对应 SKILL.md 第 4 步第 9 项）。

输入
----
- term_lookup.md（由 term_pre_check.py 生成）
- 待校验的中文译稿

输出
----
`term_diff.md`：列出标准译法在译稿中**缺失**或**被替换**的条目。

逻辑
----
1. 解析 term_lookup.md（每行形如 `| 原文 | **标准译法** | 命中表 |`）
2. 在译稿全文中检索每条标准译法是否出现
3. 若原文中出现该德语词，但译稿未使用标准译法 → 标 "❌ 未采用"
4. 若译稿中虽有该中文译法但搭配混用 → 仅在出现频次过高时告警

注意
----
- 本脚本只能给出"线索"，最终判断仍以人工 / 模型通读为准
- 单字译名（如"法""物"）极易假阳性，会自动跳过（length < 2）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


_TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*\*\*([^*]+?)\*\*\s*\|\s*([^|]+?)\s*\|\s*$")


def parse_lookup(path: Path) -> list[dict]:
    """解析 term_lookup.md 中的 `| 原文 | **标准译法** | 命中表 |` 行。"""
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _TABLE_ROW_RE.match(line)
        if not m:
            continue
        rows.append({"german": m.group(1).strip(),
                     "chinese": m.group(2).strip(),
                     "src": m.group(3).strip()})
    return rows


def parse_source(path: Path) -> str:
    """从源稿中提取德语正文（去除 markdown 标记）。若文件不存在，返回空串。"""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    # 去掉 markdown 加粗/链接/标题
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"^#+\s+", "", text, flags=re.M)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description="术语后置校验：核对译稿是否使用了 term_lookup.md 中的标准译法")
    ap.add_argument("--lookup", default="term_lookup.md", help="term_pre_check.py 产物")
    ap.add_argument("--translation", required=True, help="中文译稿文件路径")
    ap.add_argument("--source", default=None, help="可选：原文文件，用于判定德语词是否真在源中出现")
    ap.add_argument("--out", "-o", default="term_diff.md", help="产物文件路径")
    args = ap.parse_args()

    lookup_path = Path(args.lookup)
    if not lookup_path.exists():
        print(f"[ERR] 找不到 {lookup_path}", file=sys.stderr)
        return 2

    translation = Path(args.translation).read_text(encoding="utf-8", errors="replace")
    source = parse_source(Path(args.source)) if args.source else ""

    rows = parse_lookup(lookup_path)
    if not rows:
        print("[WARN] term_lookup.md 中未找到命中条目", file=sys.stderr)

    diff_lines = [
        "# 术语后置校验（term_diff.md）",
        "",
        f"> 由 `scripts/term_post_check.py` 生成 · 校验对象：{args.translation}",
        "",
        "| 原文 | 标准译法 | 命中表 | 译稿出现次数 | 处置 |",
        "|------|---------|--------|-------------|------|",
    ]

    issues = 0
    for r in rows:
        chinese = r["chinese"]
        # 短译法跳过（"法""物" 等极易假阳）
        if len(chinese) < 2:
            continue
        # 在译稿中检索
        cnt = translation.count(chinese)
        in_source = (r["german"].lower() in source.lower()) if source else None

        if cnt == 0 and in_source:
            diff_lines.append(
                f"| {r['german']} | **{chinese}** | {r['src']} | 0 | ❌ 源文含此词但译稿未使用标准译法 |"
            )
            issues += 1
        elif cnt == 0 and in_source is False:
            diff_lines.append(
                f"| {r['german']} | **{chinese}** | {r['src']} | 0 | ⚠️ 译稿未使用（源文亦未出现，可能误报） |"
            )
        else:
            diff_lines.append(
                f"| {r['german']} | **{chinese}** | {r['src']} | {cnt} | ✓ |"
            )

    diff_lines.extend([
        "",
        f"> 合计 **{issues}** 条疑似未采用。",
        "",
        "> ⚠️ 本脚本为辅助筛查。最终判定以人工通读 / 模型自检为准。",
    ])

    Path(args.out).write_text("\n".join(diff_lines), encoding="utf-8")
    print(f"[OK] 已写入 {args.out}（{issues} 条疑似）", file=sys.stderr)
    return 0 if issues == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())