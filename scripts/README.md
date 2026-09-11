# scripts/ · 术语预检 / 后置校验 / 校对辅助脚本

本目录包含 `legal-de-to-zh` Skill 调用的三个 Python 脚本。

| 脚本 | 调用时机 | 输入 | 输出 | 目的 |
|---|---|---|---|---|
| `term_pre_check.py` | **翻译工作流 第 1.5 步**（术语检索之后、翻译正文之前） | 源文文本 / 文件 | `term_lookup.md` | 列出本次翻译**必须使用**的标准译法 |
| `term_post_check.py` | **翻译工作流 第 4 步第 9 项**（阻断标准） | `term_lookup.md` + 中文译稿 | `term_diff.md` | 列出译稿中**未采用**标准译法的疑似条目 |
| `verify_translation.py` | **校对工作流 第 1–3 步** | 中文译稿 | 控制台报告 | 边码缺失 / 压缩段落 / 脚注引用-定义 三项一键初筛 |

> **为什么需要脚本？**
>
> 直接把术语表全部加载进上下文，需要 ~18 万 token，但实际翻译一段 400 字的文本时只命中 20–50 条。`term_pre_check.py` 把"整张表"压缩为"本段相关命中"，节省 token；`term_post_check.py` 在交付前把"知道却没用"的术语挑出来，避免"知道-做到"鸿沟（详见 SKILL.md 第 4 步第 9 项）。"代码是确定性的，语言解释不是"——凡是能用脚本机械判定的检查（边码对撞、脚注计数），一律交给脚本。

---

## 1. term_pre_check.py

### 用法

```bash
# 直接传源文（适合短文）
python3 scripts/term_pre_check.py "Der Anspruch ist wegen Unmöglichkeit ausgeschlossen." -o term_lookup.md

# 从文件读（适合长文）
python3 scripts/term_pre_check.py /path/to/source.txt -o term_lookup.md

# 只扫特定术语表（如确知题材为 BGB 教义学）
python3 scripts/term_pre_check.py source.txt \
    --include 术语表I_BGB民法教义学.md \
    -o term_lookup.md
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `source`（位置参数） | 必填 | 源文文本或文件路径 |
| `--dir` | 自动定位：skill 内 `references/`（优先）；回退 `/workspace/terminology` | 术语表所在目录 |
| `--out` / `-o` | `term_lookup.md` | 产物文件路径 |
| `--include` | 全扫 | 限定只扫的术语表文件名列表 |

### 产物格式

```markdown
# 术语预检结果（term_lookup.md）

| 原文 | 标准译法 | 命中表 |
|------|---------|--------|
| Unmöglichkeit | **不能** | 术语表I_BGB民法教义学.md |
| Anspruch | **请求权** | 术语表I_BGB民法教义学.md |
...
```

按 II > III > I > VIII > X > VII > IX > IV > V 优先级排序（与方法论表优先原则一致；术语表 VI 核心速查为 F 块，译名冲突时优先于一切部门法表）。

### 内部实现要点

- **零依赖**：纯 Python 标准库，可直接 `python3` 跑
- **词形归并**：剥离常见后缀（`-ung` / `-en` / `-e` / `-t` / `-iert` / 形容词/分词变格），并对**首字母大写复合词**（如 `Verjährungsfrist`）做拆分。归并时施加三重防误命中约束：①功能词黑名单（冠词/介词/连词/副词/助动词）；②首字母大写过滤（只保留名词形态）；③词干长度下限（派生后缀 ≥6、屈折后缀 ≥5，拦截 `Haftung→Haft`、`Folge→Folg` 这类截断假词干）
- **匹配规则**：单词条目——源文出现同形词（或归并变体）即命中；**多词条目——要求条目全部内容词（去功能词后）都在源文出现**（杜绝"只看一个词就命中"，如 `Prävention` 误命中 `Prävention durch Schmerzensgeld`）
- **子条目条件剔除**：术语表用 `↳` 标注子条目，用法不一致——有的是换行截断的**碎片**（`↳ Voraussetzungen`），有的是**完整独立术语**（`↳ Widerrufsrecht`）。仅当子条目德语文本已作为独立条目存在时才剔除，兼顾去噪与防漏检
- **碎片剔除**：德语列以小写词开头的条目（`und …` / `bei Tod` / `der H`）一律剔除（真实术语以大写名词/缩写/§ 开头）
- **跨表去重**：同一德语词条在多表命中时，按优先级只保留一条（消除 `Voraussetzungen` 命中 4 条的情形）
- **缩写白名单**：`GbR`/`OHG`/`KG`/`AG`/`GmbH`/`KGaA`/`ALR` 等专项保留（不受 `<4` 长度规则影响）；刻意排除 `BGB`/`ZPO`/`§`/`ff` 等"处处出现"的法典缩写
- **多表头兼容**：自动处理 2 列（术语表 I/IV/V）、3 列（缩略语对照）、4 列（术语表 III/VII）、5 列（术语表 III 边码）的 Markdown 表格
- **表格清洗**：跳过纯分隔符行（`---`）、剥离层级标记（`↳`）
- **优先级去重**：同一中文译法只保留优先级最高的那条来源

> **v2 修复（2026-09）**：修复前一版严重的子串误命中问题。实测一段 1187 字符债法文本，修复前命中 121 条（其中 118 条为噪声：`keine` 触发 26 条、`nicht` 20 条、`beim` 18 条），修复后同段命中 **3 条且全部正确**。
>
> **v3 修复（2026-09）**：修复碎片子条目泄漏（`↳ und Voraussetzungen` 等）与跨表重复命中；全量单词条目自测命中率 **99.2%**，无真实回归。

---

## 2. term_post_check.py

### 用法

```bash
python3 scripts/term_post_check.py \
    --translation /path/to/译文.md \
    --source /path/to/原文.txt \
    --lookup term_lookup.md \
    -o term_diff.md
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--translation` | 必填 | 中文译稿文件路径 |
| `--lookup` | `term_lookup.md` | 预检产物 |
| `--source` | （可选） | 原文文件；提供后可判断"原文中是否真出现该德语词" |
| `--out` / `-o` | `term_diff.md` | 产物文件路径 |

### 产物格式

```markdown
| 原文 | 标准译法 | 命中表 | 译稿出现次数 | 处置 |
|------|---------|--------|-------------|------|
| Unmöglichkeit | **不能** | 术语表I_BGB民法教义学.md | 0 | ❌ 源文含此词但译稿未使用标准译法 |
| Anspruch | **请求权** | 术语表I_BGB民法教义学.md | 3 | ✓ |
...
```

返回码：0 = 无疑似未采用；1 = 至少一条 ❌。

### 局限

- 仅做字符串包含检查，对**形近词 / 同形异义**无能为力（如 "Wort" 与 "Worte"）
- 短译法（`法` `物`）自动跳过——避免假阳性
- 译文脚注中的拉丁语法谚可能与正文冲突；如出现误报，请人工复核

---

## 3. verify_translation.py

### 用法

```bash
# 含边码范围检查
python3 scripts/verify_translation.py /path/to/译文.md --start 756 --end 932

# 不做边码范围检查（仅查压缩段落 + 脚注）
python3 scripts/verify_translation.py /path/to/译文.md
```

### 参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `translation`（位置参数） | 必填 | 中文译稿 `.md` 路径 |
| `--start` | 无 | 边码范围起点（如 756）；缺省则跳过对撞 |
| `--end` | 无 | 边码范围终点（如 932） |

### 输出示例

```
[边码] 范围内共 7 段，命中 1，缺失 6
       缺失：[757, 758, 759, 760, 761, 762]
[压缩段落] 残留 1 处：['757–760']
[脚注] 引用 2 | 定义 1 | 缺失定义 1 | 未被引用 0
       缺失定义：['2']
```

### 对应 SKILL.md 的位置

- 边码对撞 → 校对工作流 第 1 步
- 压缩段落 → 校对工作流 第 2 步
- 脚注引用/定义 → 校对工作流 第 3 步

> **局限**：本脚本仅能"缩小范围"（机械可判定的部分）；"漏译 / 错译 / 杜撰"的判断必须逐段人工对照原文（第 7 步）。

---

## 4. offset 定位法参考实现（校对工作流 第 6 步）

脚注编号对齐回原书用的参考代码（offset 定位法）。这是"内容 → 编号"的映射，不是重译。

```python
# 脚注编号 offset 定位法（校对工作流 第6步）
import re, json

text = open('译文.md', encoding='utf-8').read()
lines = text.split('\n')

# 译文脚注定义
defs = {}
for l in lines:
    m = re.match(r'^\[\^([^\]]+)\]:\s?(.*)$', l)
    if m: defs[m.group(1)] = m.group(2)

# 提取某部分正文脚注（按出现顺序）
b = None
for i, l in enumerate(lines):
    if l.startswith('# 某部分标题'):   # 如 '# 公约第一部分'
        b = i; break
order, seen = [], set()
for l in lines[b:]:
    if re.match(r'^\[\^', l): continue
    for m in re.finditer(r'\[\^([^\]]+)\]', l):
        mk = m.group(1)
        if mk not in seen: seen.add(mk); order.append(mk)

# 原文脚注基准 {编号: 内容}
orig = {int(k): v for k, v in json.load(open('_orig_fns.json', encoding='utf-8')).items()}

def norm(s):
    s = s.lower()
    s = re.sub(r'-\s*', '', s)
    s = re.sub(r'[\s.,;:()\[\]\"„“«»]', '', s)
    return s

orig_norm = {}
for num, v in orig.items(): orig_norm.setdefault(norm(v), num)

# 算 offset，offset != 0 即缺口/错位
for i, mk in enumerate(order):
    onum = orig_norm.get(norm(defs.get(mk, '')))
    if onum and onum != i + 1:
        print(f'位置{i+1} 标记{mk} 原文{onum} offset{onum-(i+1):+d}  ← 此处有缺口')
```

---

## 5. 在校对工作流中的位置

```
第1–3步：verify_translation.py   ← 本脚本登场（边码/压缩段落/脚注初筛）
   ↓
第4步：目录结构核对（人工）
第5步：最终验证报告（人工）
第6步：offset 定位法（见上方 §4 参考实现，人工 + 脚本）
第7步：漏译/错译/杜撰筛查（人工对照原文）
第8步：案例对应检测（人工）
```

详见 SKILL.md §2「校对工作流」。

---

## 6. 在翻译工作流中的位置

```
第0步：准备工作（提取原文 / 定位来源）
   ↓
第1步：术语检索（人工查表）
   ↓
第1.5步：term_pre_check.py   ← 本脚本登场
   ↓ 生成 term_lookup.md
第2步：翻译正文（按 term_lookup.md 中的标准译法）
   ↓
第3步：脚注
   ↓
第4步：阻断标准（含第 9 项：term_post_check.py）   ← 本脚本登场
   ↓ 生成 term_diff.md
交付
```

详见 SKILL.md §1「翻译工作流」第 1.5 步与第 4 步第 9 项。