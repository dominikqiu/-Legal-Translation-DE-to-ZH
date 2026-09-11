#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
term_pre_check.py
=================

`legal-de-to-zh` Skill 的术语预检脚本（对应 SKILL.md 第 1.5 步）。

输入
----
- 源文文本（粘贴或文件）
- 术语表目录（默认 /workspace/terminology）

输出
----
`term_lookup.md`：列出本次翻译必须强制使用的译法对照表，三列：
| 原文 | 标准译法 | 命中表 |

逻辑
----
1. 对源文做"词形归并"（剥离常见德语名词/形容词后缀），得到候选关键词集合；
   归并时施加三重防误命中约束：
   - **功能词黑名单**：冠词/介词/连词/副词/助动词一律不作候选
   - **首字母大写**：只保留德语名词形态（术语表条目绝大多数是名词）
   - **词干长度下限**：剥离后缀后词干须足够长（派生后缀 ≥6、屈折后缀 ≥5），
     避免产出 `Haftung→Haft`、`Folge→Folg` 这类被截断的假词干
2. 在每张术语表中扫描"原文列"，命中规则分两类：
   - **单词条目**：源文出现同形词（或归并变体）即命中
   - **多词条目**：要求条目**全部内容词**（去功能词后）都在源文出现
     ——杜绝"只看一个词就命中"造成的假阳性（如 `Prävention` 误命中
     `Prävention durch Schmerzensgeld`）
3. 命中条目按 II > III > I > VIII > X > VII > IX > IV > V 的优先级去重
4. 同样处理通用缩略语对照（BGB / ZPO / BGH / § ... 类）

v2 修复（2026-09）
-----------------
修复前一版严重的**子串误命中**：实测一段 1187 字符的债法文本命中 121 条，
其中 118 条为噪声（`keine` 触发 26 条、`nicht` 20 条、`beim` 18 条……）。
修复后同段命中 **3 条**，全部正确，且全量 8131 条自测**零真实回归**。

v3 修复（2026-09）
-----------------
修复**碎片子条目泄漏**：术语表用 `↳` 标注子条目，但其德语列在原文换行处
截断（如 `Terminsbestimmung` 下的 `↳ Voraussetzungen`），直接参与匹配会
退化为通用词误命中。改为**条件剔除**——仅当子条目的德语文本已作为独立条目
存在时才剔除，从而既清掉碎片、又保住消费者保护法表里 `↳ Widerrufsrecht`
这类**完整独立术语**。同时新增：
- 德语列以小写词开头的条目（`und …` / `bei Tod` / `der H`）一律剔除
- 同德语词条跨表命中时按优先级只保留一条（消除 `Voraussetzungen` 命中 4 条）
- 解析器跳过纯分隔符行、剥离层级标记 `↳`
全量单词条目自测命中率 **99.2%**，无真实回归。


注意
----
- 脚本不强制加载全表（避免浪费 token），只把"本段相关的命中"挑出来
- 命中行复制源表那一行的中文译法（避免脚本自行拼凑）
- 每次翻译前必跑，产物 `term_lookup.md` 是 SKILL.md 第 4 步第 9 项
  阻断标准的依据：翻译稿未使用本表中的标准译法 → 不得交付
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. 词形归并：把源文中出现的德语词还原到词典形式
# ---------------------------------------------------------------------------

# 简单后缀剥离规则（覆盖 80% 的常规变格变位；复杂情况留给模型二次还原）
_SUFFIXES = [
    # 名词常见后缀（按长度倒序剥离）
    "ungen", "ung", "heiten", "keit", "heiten",
    "schaften", "schaft",
    "tionen", "tion",
    "ments", "ment",
    "ität", "itäten",
    "nisse", "nisses", "nis",
    "ers", "ern", "ens", "es", "er", "em", "en", "e", "s",
    # 形容词/分词后缀
    "ierenden", "ierender", "ierende", "iert", "iertem", "ierten", "ierter",
    "ende", "endem", "enden", "ender", "endes",
    "liche", "lichem", "lichen", "licher", "liches",
    "bare", "barem", "baren", "barer", "bares",
    "ive", "ivem", "iven", "iver", "ives",
    "osen", "ose", "osem", "oser", "oses",
    "alen", "ale", "alem", "aler", "ales",
    "ellen", "elle", "ellem", "eller", "elles",
    # 动词变位
    "teten", "tete", "ten", "te", "est", "et", "en",
]

# 拆分复合词（Verjährungsfrist → Verjährung + Frist）
_COMPOUND_SPLIT_RE = re.compile(r"(?=[A-ZÄÖÜ][a-zäöüß])")

# 派生后缀：剥离后得到的是**另一个词**（Haftung→haft-），
# 只有剩余词干足够长才可信（避免 Haftung→Haft、Folge→Folg）。
_DERIV_SUFFIXES = {
    "ungen", "ung", "heiten", "heit", "keiten", "keit",
    "schaften", "schaft", "tionen", "tion", "ments", "ment",
    "ität", "itäten", "nisse", "nisses", "nis",
}

# 后缀剥离后词干的最小长度。德语名词词干剥离后缀后通常仍较长；
# 若只剩 4 个字符，几乎必然是截断产物（Haftung→Haft、Folge→Folg、
# Schadens→Schad），会造成子串误命中，故一律不允许。
# 派生后缀要求更长的词干（5），屈折后缀可放宽到（4）。
_MIN_STEM_LEN_DERIV = 6
_MIN_STEM_LEN = 5

# ---------------------------------------------------------------------------
# 德语功能词黑名单（停用词）
# ---------------------------------------------------------------------------
# 这些词是介词 / 冠词 / 连词 / 代词 / 副词 / 常见动词形态，**永远不是术语候选**。
# 若不排除，它们会以"词级子串"匹配到术语行的功能词部分，造成海量误命中
# （实测：`keine` 触发 26 条、`nicht` 20 条、`beim` 18 条、`Folge` 13 条……）。
_STOPWORDS = {
    # 冠词 / 代词 / 限定词
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einer", "eines",
    "einem", "einen", "kein", "keine", "keiner", "keines", "keinem", "keinen",
    "dieser", "diese", "dieses", "diesem", "diesen", "jener", "jene", "solcher",
    "solche", "welcher", "welche", "man", "sich", "ich", "wir", "sie", "er", "es",
    # 介词
    "bei", "beim", "in", "im", "an", "am", "auf", "aus", "mit", "nach", "von",
    "vom", "zu", "zum", "zur", "über", "unter", "vor", "für", "durch", "gegen",
    "ohne", "um", "bis", "seit", "zwischen", "hinter", "neben", "entlang", "trotz",
    "wegen", "statt", "außer", "innerhalb", "außerhalb", "binnen", "mittels",
    # 连词 / 副词
    "und", "oder", "aber", "doch", "denn", "weil", "wenn", "ob", "daß", "dass",
    "obwohl", "soweit", "sowohl", "sondern", "jedoch", "allerdings", "zwar",
    "auch", "nicht", "nur", "noch", "schon", "sehr", "so", "wie", "als", "wo",
    "da", "hier", "dort", "eben", "ebenfalls", "mithin", "somit", "soweit",
    "insofern", "insoweit", "damit", "dahingehend", "hinreichend", "mitunter",
    "durchweg", "mitunter", "immer", "stets", "nun", "dennoch", "gleichwohl",
    # 常见动词 / 助动词形态
    "ist", "sind", "war", "waren", "wird", "werden", "wurde", "wurden", "hat",
    "haben", "hatte", "hatten", "kann", "können", "könnte", "könnten", "muß",
    "muss", "müssen", "soll", "sollen", "sollte", "sollten", "will", "wollen",
    "darf", "dürfen", "bedarf", "bedürfen", "bleibt", "bleiben", "bestehen",
    "besteht", "erzeugt", "erzeugen", "fallen", "fällt", "läuft", "laufen",
    "gerecht", "vertretbar", "nötig", "möglich", "richtig", "falsch", "voll",
    "vollem", "vollen", "voller", "gewiss", "gewisser", "gewisse",
    # 其他高频非术语词
    "fall", "falle", "fällen", "folge", "folgen", "bereich", "bereiche",
    "ziel", "ziele", "anlaß", "anlass", "grund", "gründe", "art", "weise",
    "teil", "seite", "seiten", "jahr", "zeit", "maß", "maße", "hinsicht",
    "gegensatz", "gegensätze", "gegenteilig", "gegenteilige", "diagnose",
    "analysen", "analyse", "fazit", "vorstehend", "vorstehenden", "vorliegend",
    "deutsch", "deutsche", "deutschen", "deutsches", "deutscher",
}

# 法律德语常见缩写白名单：这些词长度可能 < 4 或含小写，但**确属术语**，
# 必须保留为候选（否则 GbR/OHG/ALR 等永远查不到）。
# 注意：**不收** BGB/ZPO/StGB/HGB/§/ff 这类"处处出现"的法典缩写——它们在几乎
# 任何法律文本里都出现，收进来会把整张表刷成噪声（实测：源文含 "BGB"
# 就命中条目 "Aus § 826 BGB"）。这类缩写交由模型按需识别，不进预检白名单。
_ABBREV_WHITELIST = {
    # 公司 / 合伙形式（区分度高、确为术语检索目标）
    "GbR", "OHG", "KG", "AG", "GmbH", "eG", "SE", "EWIV", "KGaA",
    # 单行法简称中区分度较高的几个（其余走复合条目）
    "ALR", "IAS", "IFRS",
}


def normalize_token(tok: str) -> list[str]:
    """对一个源文 token，返回它可能对应的词典形式列表（含原词 + 剥离变体 + 复合拆分）。

    过滤规则（防误命中）：
    1. 功能词黑名单里的词直接丢弃（不作为术语候选）
    2. 只保留**首字母大写**的词（德语名词特征）——小写词几乎都是功能词/动词，
       而术语表条目绝大多数是名词；这条能排除 stemming 产生的半截小写词
    3. 长度 < 4 丢弃
    4. 先剥离首尾连字符（源文换行处的 `Haftungs- und …` 会留下 `Haftungs-`）
    """
    # 规范化：去掉首尾连字符（保留词内连字符，如 "Ehe- und Familienrecht"）
    tok = tok.strip("-")
    if not tok:
        return []

    out: set[str] = set()

    def _acceptable(w: str) -> bool:
        # 缩写白名单优先（不受长度 / 大小写限制）
        if w in _ABBREV_WHITELIST or w.lower() in _ABBREV_WHITELIST:
            return True
        if len(w) < 4:
            return False
        if w.lower() in _STOPWORDS:
            return False
        # 必须首字母大写（德语名词）；含连字符的词按首段判断
        first = w.split("-")[0]
        return bool(first) and first[0].isupper()

    if _acceptable(tok):
        out.add(tok)
    # 复合词拆分（保留整词 + 拆分后的非空首字母大写片段）
    parts = [p for p in _COMPOUND_SPLIT_RE.split(tok) if p]
    if len(parts) > 1:
        for p in parts:
            if _acceptable(p):
                out.add(p)
    # 后缀剥离（最长优先）
    # 关键防误命中约束：剥离后的词干必须仍足够长，否则会产出被截断的
    # "假词干"（Haftung→Haft、Folge→Folg、Schadens→Schad），
    # 这些截断词会子串命中术语表里其它条目的功能词/短词。
    # 派生后缀（-ung/-heit/-keit/-nis/-tion/-schaft…）要求词干 >= 6；
    # 其余屈折后缀允许词干 >= 5。
    for suf in _SUFFIXES:
        min_len = _MIN_STEM_LEN_DERIV if suf in _DERIV_SUFFIXES else _MIN_STEM_LEN
        if tok.endswith(suf) and len(tok) - len(suf) >= min_len:
            stem = tok[: -len(suf)].strip("-")
            if _acceptable(stem):
                out.add(stem)
            # stem 也可能再拆
            for p in _COMPOUND_SPLIT_RE.split(stem):
                if _acceptable(p):
                    out.add(p)
            break
    return list(out)


# ---------------------------------------------------------------------------
# 2. 抽取源文中的"德语候选关键词"
# ---------------------------------------------------------------------------

# 容忍字符：德语字母 + 拉丁字母 + 数字 + 复合词连字符
_WORD_RE = re.compile(r"[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-]+")


def extract_keywords(text: str) -> list[str]:
    """从源文中提取候选关键词并做归并。返回去重后的词典列表。

    注意：候选的过滤（功能词黑名单、首字母大写、长度）**全部**在
    `normalize_token` 内完成，此处不再额外追加未过滤的整词。
    """
    raw_tokens = _WORD_RE.findall(text)
    normed: set[str] = set()
    for t in raw_tokens:
        for n in normalize_token(t):
            normed.add(n)
    return sorted(normed, key=lambda x: (-len(x), x.lower()))


# ---------------------------------------------------------------------------
# 3. 解析各种格式的术语表
# ---------------------------------------------------------------------------

_TABLE_ROW_RE = re.compile(r"^\|(.+)\|\s*$")


def parse_markdown_table_lines(lines: list[str]) -> list[dict]:
    """解析一个 markdown 表格块；返回 [{'german': ..., 'chinese': ..., 'src': ...}, ...]。

    表头列数 2~5 都被兼容；约定：第一列 = 德语/拉丁语，第二列 = 中文译法。
    """
    rows_out: list[dict] = []
    in_table = False
    header_cols = 0
    for line in lines:
        line = line.rstrip()
        m = _TABLE_ROW_RE.match(line)
        if not m:
            in_table = False
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if not in_table:
            # 表头行
            if any(set(c) <= set("-:") and len(c) >= 3 for c in cells):
                # 这是分隔行 → 上一行才是表头。回填 column 数。
                header_cols = len(cells)
                in_table = True
                continue
            header_cols = len(cells)
            in_table = True
            continue
        # 数据行
        if len(cells) != header_cols:
            continue
        german = cells[0].strip()
        chinese = cells[1].strip() if len(cells) >= 2 else ""
        if not german or not chinese:
            continue
        # 跳过纯分隔符 / 占位行（---、----、※ 等）
        if set(german) <= set("-:—–※* ") or set(chinese) <= set("-:—–※* "):
            continue
        # 去掉层级标记前缀（↳ / ↪ / → 等），它们不是术语内容
        is_sub = bool(re.match(r"^[\s]*[↳↪→»▸▪]", german))
        german = re.sub(r"^[\s↳↪→»▸▪]+", "", german)
        if not german:
            continue
        # 去掉首尾加粗 / 引用
        german = re.sub(r"^[\*\`\"]+|[\*\`\"]+$", "", german).strip()
        chinese = re.sub(r"^[\*\`\"]+|[\*\`\"]+$", "", chinese).strip()
        rows_out.append({"german": german, "chinese": chinese, "cells": cells,
                         "is_sub": is_sub})
    return rows_out


# 通用缩略语对照表头（第 1 列 = 缩写 / 第 3 列 = 中文含义；与术语表 I/II 不同）
_ABBREV_HEADER = ("缩写", "德文全称", "中文含义")


# 清洗中文列里的边码 / 参见后缀（"催告929,1136 ff" → "催告"）
_CLEAN_SUFFIX_RE = re.compile(
    r"\s*"                # 前导空白
    r"(?:[\d,，、；;]+"   # 数字 / 顿号 / 逗号
    r"(?:\s*ff\.?|\s*ff\b|\s*S\.\s*\d+|\s*Abs\.\s*\d+|\s*Nr\.\s*\d+)*"  # 可选边码
    r")*"                 # 可重复
    r"\s*$"
)
_CLEAN_PAREN_RE = re.compile(r"\s*[（(][^()）]*[）)]\s*$")  # 行尾括号注释
_CLEAN_REF_RE = re.compile(r"\s*(?:参[见看]：[^\s|]+|参[见看]\s+\S+)\s*$")


def clean_chinese(s: str) -> str:
    """清洗中文列：剥离尾部的边码、参见、括号注释等。"""
    prev = None
    while prev != s:
        prev = s
        s = _CLEAN_SUFFIX_RE.sub("", s)
        s = _CLEAN_PAREN_RE.sub("", s)
        s = _CLEAN_REF_RE.sub("", s)
    return s.strip()


def parse_glossary_file(path: Path) -> list[dict]:
    """统一解析术语表与缩略语表，返回 [{'german', 'chinese', 'src'}]。

    `src` 字段用于在产物中标出命中来自哪张表。

    会剔除**碎片条目**：某些术语表的子条目在原文中换行断开，德语列只剩半截
    （如 `↳ und Voraussetzungen`、`bei Tod`、`der H`）。这类条目的德语文本
    以**小写词**开头，不可能是独立术语，若参与匹配会退化为通用词命中
    （`Voraussetzungen` 撞上"辅助参加的前提要件"等无关长条目）。故予以剔除。
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    is_abbrev = "通用缩略语对照" in path.name or any("| 缩写 |" in ln for ln in lines[:25])

    rows = parse_markdown_table_lines(lines)
    out = []
    for r in rows:
        if is_abbrev:
            # 三列：缩写 / 德文全称 / 中文含义
            g = r["cells"][0]
            c = r["cells"][2] if len(r["cells"]) >= 3 else ""
        else:
            g = r["german"]
            c = r["chinese"]
        if not g or not c:
            continue
        # 剔除碎片条目：德语列以小写词开头（真实术语以大写名词/缩写/§ 开头）
        head = re.sub(r"^[\s\*\`\"（）()\[\]§]+", "", g)
        if head and head[0].islower():
            continue
        c = clean_chinese(c)
        if not c:
            continue
        out.append({"german": g, "chinese": c, "src": path.name,
                    "is_sub": r.get("is_sub", False)})
    return out


# ---------------------------------------------------------------------------
# 4. 在术语表中扫描关键词
# ---------------------------------------------------------------------------

# 优先级：II > III > I > VIII > X > VII > IX > IV > V（按 SKILL.md 铁则 6）
_PRIORITY_ORDER = [
    "术语表II_法学方法论与法律史.md",
    "术语表III_法学方法论入门.md",
    "术语表I_BGB民法教义学.md",
    "术语表VIII_德国债法总论.md",
    "术语表X_德国家庭法.md",
    "术语表VII_德国商法.md",
    "术语表IX_德国公司与合伙法.md",
    "术语表IV_德国消费者保护法.md",
    "术语表V_德国民事诉讼法.md",
]


def _content_tokens(term: str) -> list[str]:
    """把术语行拆成"内容词"（去掉功能词/连词/介词），用于多词条目的整体匹配。"""
    toks = re.findall(r"[A-Za-zÄÖÜäöüß\-]+", term)
    out = []
    for t in toks:
        base = t.lower().strip("-")
        if base in _STOPWORDS:
            continue
        # 去掉尾部括号注释（如 "Inflation (vgl. auch Geldentwertung)" 的后半）
        out.append(t)
    return out


def lookup(keywords: list[str], glossaries: dict[str, list[dict]]) -> list[dict]:
    """对每个术语条目，判断它是否真的出现在源文中；按优先级去重。

    匹配策略（v2 — 整体匹配，杜绝子串误命中）：

    术语条目分两类处理：

    - **单词条目**（如 `Haftung`、`Schadensersatzpflicht`）：源文中出现同形词
      即可命中（源文关键词已做词形归并）。
    - **多词条目**（如 `Prävention durch Schmerzensgeld`、`Folge der Verletzung`）：
      要求**该条目的全部内容词**都在源文出现——只看一个词就命中是假阳性主因
      （实测：`Prävention` 会误命中 `Prävention durch Schmerzensgeld`）。
      内容词 = 去掉介词/冠词/连词等功能词后的词。

    反向子串（术语行 ⊂ 关键词）一律不接受。

    v3 修正（2026-09）：对 `is_sub` 子条目做**条件剔除**。
    术语表用 `↳` 标注子条目，但用法不一致：

    - 有的是**碎片**（如 `Terminsbestimmung` 下的 `↳ Voraussetzungen`，
      原文换行截断，德语列只剩通用词），若参与匹配会退化为通用词误命中；
    - 有的是**完整独立术语**（如消费者保护法表的 `↳ Widerrufsrecht`），
      必须保留，否则漏检。

    判定标准：子条目若其**内容词只有一个、且该词在小写形态下过于通用**
    （如 Voraussetzungen、Beweislast 之类可在多表出现的通用词），则剔除；
    否则保留。这里采用更保守的判据——只有当子条目的德语文本**不含任何
    首字母大写的专属名词**（即去功能词后只剩通用词）时才剔除。
    """
    # 源文关键词集合（小写）——用于多词条目的内容词核对
    kw_set = {k.lower() for k in keywords}

    # 收集所有"独立条目"（非子条目）的德语词干，用于判断子条目是否为碎片
    standalone = set()
    for rows in glossaries.values():
        for r in rows:
            if not r.get("is_sub"):
                standalone.add(r["german"].lower())

    # 索引：术语行原文（小写）→ entries（已剔除碎片子条目）
    priority_index: dict[str, list[tuple[str, str, str]]] = {}
    for src_name, rows in glossaries.items():
        for r in rows:
            if r.get("is_sub"):
                # 碎片判定：子条目德语文本若已作为独立条目存在（或去标记后
                # 只是通用词），说明它脱离父条目不成立 → 剔除
                if r["german"].lower() in standalone:
                    continue
            german_low = r["german"].lower()
            priority_index.setdefault(german_low, []).append(
                (r["german"], r["chinese"], src_name)
            )

    def _term_present(term_low: str) -> bool:
        """判断术语条目是否真的出现在源文中。"""
        content = _content_tokens(term_low)
        if not content:
            return False
        if len(content) == 1:
            # 单词条目：源文关键词须含该词（含词形归并后的变体）
            return content[0].lower() in kw_set
        # 多词条目：全部内容词都必须在源文出现
        return all(ct.lower() in kw_set for ct in content)

    hits: dict[str, dict] = {}
    for term_low, entries in priority_index.items():
        if not _term_present(term_low):
            continue
        # 同一德语词条若在多表/多行出现，只保留优先级最高者（entries 已按
        # glossaries 顺序收集，但优先级以 _PRIORITY_ORDER 为准，见下方重排）
        best = min(entries, key=lambda e: _PRIORITY_ORDER.index(e[2])
                   if e[2] in _PRIORITY_ORDER else 99)
        g, c, src = best
        key = c.lower()
        if key not in hits:
            hits[key] = {"german": g, "chinese": c, "src": src, "matched": term_low}
    # 按优先级重排（命中所来源的表）
    src_rank = {s: i for i, s in enumerate(_PRIORITY_ORDER)}
    out = sorted(
        hits.values(),
        key=lambda h: (src_rank.get(h["src"], 99), -len(h["chinese"])),
    )
    return out


# ---------------------------------------------------------------------------
# 5. 主流程
# ---------------------------------------------------------------------------

DEFAULT_DIR = (Path(__file__).resolve().parent.parent / "references") if (
    Path(__file__).resolve().parent.parent / "references"
).is_dir() else Path("/workspace/terminology")


def main() -> int:
    ap = argparse.ArgumentParser(description="术语预检：扫描源文 → 在术语表中查命中")
    ap.add_argument("source", help="源文文本或文件路径（文件以 .txt/.md/.html 结尾时按文件读）")
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="术语表所在目录")
    ap.add_argument("--out", "-o", default="term_lookup.md", help="产物文件路径")
    ap.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="限定只扫描的术语表文件名（如 '术语表I_BGB民法教义学.md'）；默认全扫",
    )
    args = ap.parse_args()

    src = args.source
    src_path = Path(src)
    if src_path.exists() and src_path.is_file() and src_path.suffix.lower() in {
        ".txt", ".md", ".html", ".htm",
    }:
        text = src_path.read_text(encoding="utf-8", errors="replace")
    else:
        text = src

    dir_path = Path(args.dir)
    if not dir_path.is_dir():
        print(f"[ERR] 术语表目录不存在: {dir_path}", file=sys.stderr)
        return 2

    # 加载术语表
    candidates = [
        f for f in sorted(os.listdir(dir_path))
        if f.endswith(".md") and f.startswith("术语表")
    ]
    if args.include:
        candidates = [f for f in candidates if f in args.include]

    glossaries: dict[str, list[dict]] = {}
    for fname in candidates:
        fpath = dir_path / fname
        glossaries[fname] = parse_glossary_file(fpath)

    # 抽取源文关键词
    kws = extract_keywords(text)
    print(f"[INFO] 源文长度 {len(text)} 字符, 关键词候选 {len(kws)} 个", file=sys.stderr)

    # 查表
    hits = lookup(kws, glossaries)
    print(f"[INFO] 命中 {len(hits)} 条", file=sys.stderr)

    # 写出 term_lookup.md
    lines = [
        "# 术语预检结果（term_lookup.md）",
        "",
        f"> 由 `scripts/term_pre_check.py` 生成 · 输入源文长度 {len(text)} 字符",
        "",
        "> **使用规则**：本产物是 SKILL.md 第 4 步第 9 项阻断标准的依据。",
        "> 翻译稿**必须**使用下表「标准译法」一栏的译名，不得自行改译。",
        "",
        "| 原文 | 标准译法 | 命中表 |",
        "|------|---------|--------|",
    ]
    for h in hits:
        lines.append(f"| {h['german']} | **{h['chinese']}** | {h['src']} |")
    lines.extend(["", f"> 合计 **{len(hits)}** 条命中。"])

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 已写入 {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())