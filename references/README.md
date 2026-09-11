# 德语法学著作汉译 Skill（`legal-de-to-zh`）

> Translate German legal texts (BGB civil law, legal history, legal methodology) into Chinese using curated glossaries from 《德国债法分则案例研习》and *Recht als Wissenschaft*. Includes a proofreading workflow for verifying and aligning translations against the source (边码 / 脚注编号 / 漏译 / 错译 / 杜撰).

本目录收录 `legal-de-to-zh` Skill 配套的**外部术语表资产包**。**自 v6.8 起，这些词表的权威副本位于 skill 目录内的 `references/`**（随 skill 分发，符合 Claude Skill 三级 progressive disclosure 规范）；`/workspace/terminology/` 为**用户可见的工作副本 / 源目录**，内容与 `references/` 一致。Skill 主文件为 `references/` 同级目录下的 `SKILL.md`。

---

## 一、本 Skill 是做什么的

`legal-de-to-zh` 是一个面向德语法学文本汉译的工程化技能。它把"凭感觉翻译"这个长期困扰法律翻译的隐患抽掉，代之以一套**术语表至上**的强制流程：

- 翻译前必须先加载对应的术语表文件
- 术语表命中即用，**不得擅自更改**
- 未命中才推衍，首次出现必加原文
- 跨表冲突按"方法论表优先"裁决
- 所有新术语单独成产物，等用户复核后再并入术语表本体

这套规则把翻译的可控性和可追溯性提到最高 —— 译稿每一处偏离都能在术语表里找到出处。

## 二、核心特点

### 1. 九张部门法术语表（I–V、VII–X）+ 核心速查（VI）+ 两份通用资源

**部门法术语表**（分题材加载）：

| 术语表 | 题材 | 加载规则 |
|---|---|---|
| **I** | BGB 民法教义学（债法分则 + 合同法） | 默认加载 |
| **II** | 法学方法论与法律史 | 含 `Auslegung / Methodenlehre / Rechtsgeschichte / Analogie` 等时加载 |
| **III** | 法学方法论入门 | 方法论入门 / 关键词索引体例加载 |
| **IV** | 德国消费者保护法 | 含 `Verbraucher / Widerruf / AGB / Fernabsatz` 等时加载 |
| **V** | 德国民事诉讼法（**穆泽拉克基线重建**，3541 条） | 含 `Klage / Berufung / Revision / Zwangsvollstreckung` 等时加载 |
| **VII** | 德国商法（**双来源合并**，1417 条） | 含 `Kaufmann / Handelsgewerbe / Firma / Kommissionär / Handelsvertreter / Vertragshändler / Frachtgeschäft / Prokura / Handelsregister` 等时加载 |
| **VIII** | 德国债法总论（Medicus） | 含 `Schuldverhältnis / Erfüllung / Leistungsstörung / Unmöglichkeit / Verzug / Rücktritt / Aufrechnung / Schuldübernahme / Gläubigerverzug / c.i.c.` 等债法总论概念时加载 |
| **IX** | 德国公司与合伙法（Windbichler） | 含 `Aktiengesellschaft / Aktie / GmbH / Hauptversammlung / Vorstand / Aufsichtsrat / OHG / KG / Kommanditist / GbR / Umwandlung / Konzern` 等公司或合伙组织内容时加载 |
| **X** | 德国家庭法（Wellenhofer） | 含 `Ehe / Eheschließung / Scheidung / Güterstand / Zugewinnausgleich / Unterhalt / Versorgungsausgleich / elterliche Sorge / Umgangsrecht / Kindeswohl / Abstammung / Vaterschaft / Adoption / Vormundschaft / Betreuung / FamFG` 等家庭法内容时加载 |

**核心速查**（不属于部门法术语表序列；始终加载，无需题材判定）：

| 资源 | 题材 | 加载规则 |
|---|---|---|
| **术语表 VI 核心速查** | 高频 19 条核心术语（F 块硬编码） | **任何文本一律加载**（译名冲突时优先于一切部门法表） |

**通用资源**（不属于部门法术语表序列；适用于所有部门法文本）：

| 资源 | 题材 | 加载规则 |
|---|---|---|
| **通用缩略语对照** | 文献 / 法院 / 法案 / 期刊名缩写 | **任何文本一律加载**（脚注中最高频成分） |
| **中德法学翻译_逻辑关系语料库** | 转折 / 因果 / 总结 等译例 | 第1步与第2步翻译时按需参看 |

### 2. 表间冲突：方法论表优先
优先级（铁则 6）：

> **II（法学方法论与法律史） > III（法学方法论入门） > I（BGB 民法教义学·债法分则） > VIII（债法总论） > X（家庭法） > VII（商法） > IX（公司与合伙法） > IV（消费者保护法） > V（民事诉讼法）**

核心速查（VI，F 块）优先于一切部门法表；**通用资源（通用缩略语对照 + 逻辑关系语料库）不参与该裁决链**，与所有部门法术语表都无冲突关系。

### 3. 翻译工作流

```
入流判别 ──── 用户仅含「校对」 → 跳校对工作流
   │
   ▼
第0步 准备工作 + 通读定位
第1步 术语检索（加载部门法术语表 + 通用资源 + 检索 + 变格变位 + 冲突裁决）
第1.5 术语预检（term_pre_check.py 生成 term_lookup.md）+ 未收录术语清单
第2步 翻译正文（30字硬拆句、禁破折号夹注）
第3步 脚注处理（四型：A纯文献 / B实译 / C混合 / D纯引文）
第4步 阻断标准（9项：含第9项 term_post_check.py 术语预检对照，任一未达标即不得交付）
```

### 4. 文风铁律

- **单句 ≤ 30 字**（硬性强制，超过即拆分）
- **禁破折号夹注**（德语大量使用的夹注式破折号直接打断中文语流，正文中成对夹注式破折号应为 0 处）
- **直陈为主**，主语动词前置，"鉴于"→"考虑到"
- **去文言虚词**：用"首先 / 此外 / 在此"而非"首当 / 除此而外 / 于此"
- **去口语**：禁用语气词、儿化音、生活化表述
- **逻辑关系三细则**：`Denn` 与让步嵌套时省略、`damit` 双义判别、总结标记节制

### 5. 校对工作流（独立）
当用户提示词**仅含「校对」意图**、且无显式翻译指令时，Skill 自动跳过翻译工作流、跳转至校对工作流，逐条核对边码、漏译、错译、脚注编号、杜撰。"翻译"与"校对"切成两套互不污染的工作流。

## 三、本目录资产清单

> **v6.8 结构变更**：自 v6.8 起，全部术语表已迁入 skill 目录内的 `references/`（随 skill 分发，符合 Claude Skill 三级 progressive disclosure 规范）。本 `/workspace/terminology/` 目录保留为**用户可见的工作副本 / 源目录**，内容与 `references/` 一致。下表即为两份目录共有的资产清单。

```
terminology/   （同步镜像于 <skill>/references/ ）
├── README.md                                  ← 本文件
│
├── 【部门法术语表 I–V、VII–X】
│
├── 术语表I_BGB民法教义学.md         ( 35.8 KB)   BGB 债法分则 / 物权 / 合同 / 民法总论
├── 术语表II_法学方法论与法律史.md    (  5.5 KB)   解释方法 / 法律史 / Rechtsfortbildung
├── 术语表III_法学方法论入门.md      ( 12.3 KB)   《法学方法论入门》关键词索引
├── 术语表IV_德国消费者保护法.md     ( 24.5 KB)   消法 / UWG / 远程销售 / 团体诉讼
├── 术语表V_德国民事诉讼法.md       (208.7 KB)   穆泽拉克《基础教程》术语索引基线 + 原表 V 校正独有条目
├── 术语表VII_德国商法.md            ( 70.2 KB)   双来源：案例研习版 318 条 + 卡纳利斯版 1099 条（均两列）
├── 术语表VIII_德国债法总论.md      ( 22.9 KB)   债法总论（Medicus）：给付障碍 / 清偿 / 解除 / 迟延 / 损害赔偿
├── 术语表IX_德国公司与合伙法.md    ( 29.9 KB)   公司与合伙法（Windbichler）：AG / GmbH / 合伙 / 改组 / 康采恩
├── 术语表X_德国家庭法.md          ( 16.9 KB)   家庭法（Wellenhofer）：婚姻 / 离婚 / 扶养 / 父母照顾 / 亲子关系 / 照管
│
├── 【核心速查 · 始终加载（F 块硬编码于 SKILL.md 上下文）】
│
├── 术语表VI_核心速查.md            (  2.2 KB)   高频 19 条术语速查（避免上下文压缩时遗漏）
│
├── 【通用资源 · 不属于部门法术语表序列】
│   ├── 通用缩略语对照.md              ( 10.0 KB)   文献 / 法院 / 法案 / 期刊名缩写（任何文本必查）
│   ├── 关键术语区分.md                (  3.1 KB)   extensiv/ausdehnend、Wort/Wortlaut、Gesetz/Recht 等五组区分
│   └── 中德法学翻译_逻辑关系语料库.md  (  6.8 KB)   Denn / damit / 让步 / 总结 等译例
└── 【待整理物料 · 不入检索】          （v6.8 起已移除，不再随 skill 分发）
```

> **v6.8 变更**：原 `_物料待整理_不入检索/`（德国物权法 OCR 原始 2001 条，德中双列错位）已从 skill 中移除，不再随 skill 分发。物权法文本请以术语表 I（BGB 民法教义学）与常规法律词典交叉核验。

### 术语表规模

| 术语表 | 主词条 | 子词条 | 合计 |
|---|---:|---:|---:|
| I BGB 民法教义学 | — | — | 799 |
| II 法学方法论与法律史 | — | — | 88 |
| III 法学方法论入门 | 105 | 75 | 180 |
| IV 德国消费者保护法 | 306 | 180 | 486 |
| V 德国民事诉讼法 | 2909 | 632 | 3541 |
| VII 德国商法 | 来源一 167 / 来源二 — | 来源一 151 / 来源二 — | **1417**（318 + 1099） |
| VIII 德国债法总论 | — | — | 515 |
| IX 德国公司与合伙法 | — | — | 729 |
| X 德国家庭法 | — | — | 386 |
| **术语表合计** | | | **8160** |

> **注意**：I–VII 的主词条/子词条结构来自原书索引标目；VIII–X 为 OCR 清洗后的平面词表（不分主/子词条，按德语字母排序）。物权法暂缓入库（见目录底部说明）。
>
> **术语表 VII 为双来源合并表的特例**：文件内分「来源一」「来源二」两节，节内各自排序，**两节均为两列**（`德文 | 中文`）。两来源规范化同形的 75 条德语词只在来源一保留；另有 20 条译法差异并列于来源二节首，**两节之间不互相裁决**（实务文本取来源一，学理／教科书文本取来源二）。

**通用资源**（不计入部门法术语表规模）：

| 资源 | 条数 |
|---|---:|
| 通用缩略语对照 | 92 |
| 逻辑关系语料库 | —（按译例计） |

**核心速查**（独立于术语表 I–VII，始终加载）：

| 资源 | 条数 |
|---|---:|
| 术语表 VI 核心速查 | 19（高频易错，每次翻译必看） |

## 四、术语表格式规范

### 4.1 概念词条表（I–V、VII–X）

两列 Markdown 表（**v6.7 起全库统一**；按用户要求，词表仅保留"中德准确对照"内容，原书页码／边码／「所属／参见」列／「译法提示」列一律不收录）：

```
| 德文 | 中文 |
|------|------|
| **Anwartschaftsrecht** | 期待权 |
| ↳ Anwartschaft | 期待 |
```

- 主词条用 `**粗体**`（平面词表 VIII–X 除外）
- 子词条用 `↳` 前缀缩进
- 按德文首字母 A–Z 排序（Ä→A, Ö→O, Ü→U）

### 4.2 通用缩略语对照（通用资源层）
三列 Markdown 表：

```
| 缩写 | 德文全称 | 中文含义 |
|------|----------|----------|
| BGB | Bürgerliches Gesetzbuch | 《民法典》 |
```

### 4.3 逻辑关系语料库
按转折 / 因果 / 总结三类组织，含德语原文 → 中文译文 → 译法要点三段式样例。

## 五、使用方式

1. **加载 Skill**：由 CodeBuddy Code 自动加载 `legal-de-to-zh`
2. **指定翻译任务**：提交德语法律文本或 `.docx`
3. **Skill 自动执行**：入流判别 → 加载部门法术语表 + 通用资源 → 检索 → 翻译 → 自检
4. **交付产物**：
   - 翻译正稿（`.md` 或 `.docx`）
   - 未收录术语清单（两列 Markdown 表，新术语**黄色高亮**）
   - 校对工作流结果（如触发校对）

## 六、扩展规则

### 新术语并入
翻译中出现的新术语进入"未收录术语清单"产物。**用户需另行下达指令**才并入对应术语表本体，Skill 不会自行改动术语表。

### 术语表更新流程
1. 用户提供新术语源（如 `.docx` 词义对照表、CSV 等）
2. Skill 解析 → 与现有术语表去重 → 生成新术语表 `.md`
3. 更新 SKILL.md 中的术语表索引与统计
4. 用户确认后，术语表正式生效

## 七、来源

1. 《德国债法分则案例研习》（第八版），Hans-Josef Wieling / Thomas Finkenauer 著，冯洁语 译
2. Jan Schröder, *Recht als Wissenschaft*, 2. Aufl. 2012
3. 《法学方法论入门》书末「关键词索引」
4. 《德国消费者保护法》书末「关键词索引」（OCR 校正版）
5. 穆泽拉克（Musielak）《德国民事诉讼法基础教程》（Grundkurs ZPO）书末「术语索引」（OCR 校正版，2 153 条 → 清洗后 2 120 条可用）—— 术语表 V 的**基线来源**；原表 V（旧《德国民事诉讼法》关键词索引）经校正的 1 427 条独有条目并入，合计 3 541 条
6. 《德国合同法》（第 2 版）书末「关键词索引」（OCR 校正版）→ 已并入术语表 I 补充
7. **通用缩略语对照** —— 通用资源层（不属于部门法术语表序列）。整合自上述来源的缩略语对照，并补充 Brüssel I-VO、Rom I-VO 等欧盟立法简称。独立存放于 `/workspace/terminology/通用缩略语对照.md`
8. 梅迪库斯《德国债法总论》书末「关键词索引」（OCR 校正版，573→526 条）—— 术语表 VIII
9. 克里斯蒂娜·温德比西勒《德国公司与合伙法（第24版）》书末「关键词索引」（OCR 校正版，755→729 条）—— 术语表 IX
10. 玛丽娜·韦伦霍菲尔《德国家庭法》（第6版）书末「关键词索引」（OCR 校正版，405→386 条）—— 术语表 X
11. 卡纳利斯《德国商法》（杨继 译，法律出版社 2006 年版）书末「术语索引」（OCR 原始 1776 条 → 机械清洗保留 1617 条 → 逐条语义补全并与来源一去重后收录 **1099 条**）—— 并入术语表 VII 作为**来源二**

## 八、版本

- v1.0（基础）：术语表 I–II + 翻译铁则五条
- v2.0（流程化）：第0–4步工作流 + 校对工作流
- v3.0（资产化）：术语表拆分为外部文件，引入 IV–V
- v4.0（精细化）：30字硬拆句、四型脚注、8项阻断标准、铁则六条、方法论表优先
- v5.0（缩略语独立）：术语表 VI 独立成表，覆盖文献 / 法院 / 法案 / 期刊缩写
- v6.0（商法入表 + 缩略语升级）：术语表 VII 独立成表；通用缩略语对照从术语表 VI 升级为与逻辑关系语料库同级的**通用资源**，理由是其对所有部门法通用，与部门法术语表性质不同
- v6.1（核心速查入表 + 脚本化）：新增**术语表 VI 核心速查**（18 条高频易错术语，硬编码于 SKILL.md 上下文始终加载）；新增 `scripts/term_pre_check.py` 与 `scripts/term_post_check.py` 两个 Python 脚本，配合 SKILL.md 第 1.5 步与第 4 步第 9 项，将术语检索从"全表加载"优化为"本段命中"，节省 ~50% token
- v6.2（债法总论 + 公司与合伙法入表）：新增**术语表 VIII（德国债法总论，526 条）**与**术语表 IX（德国公司与合伙法，730 条）**两张 OCR 清洗校正词表；表间优先级扩展为 II > III > I > VIII > VII > IX > IV > V；物权法 2001 条 OCR 因德中错位暂缓入库（存档于 `_物料待整理_不入检索/`）
- v6.3（家庭法入表）：新增**术语表 X（德国家庭法，386 条，Wellenhofer 第6版）**；表间优先级扩展为 II > III > I > VIII > X > VII > IX > IV > V；物权法目标编号顺延为 XI
- v6.8（结构合规重构）：对照《The Complete Guide to Building Skills for Claude》规范对 Skill 做全面审查与精简。**术语表迁入 skill 目录内的 `references/`**（随 skill 分发，符合三级 progressive disclosure），`/workspace/terminology/` 保留为用户可见的工作副本；`SKILL.md` 路径引用由绝对路径改为相对路径 `references/...`。**外置参考速查**：「关键术语区分」5 张表移入 `references/关键术语区分.md`，「F 块高频核心术语速查」权威载体为 `references/术语表VI_核心速查.md`，SKILL.md 仅保留硬编码摘要（19 条快照）。**去重精简**：术语表清单、优先级链、脚注规则各只保留一处权威定义（其余改为 `见 §X` 交叉引用）；工作流重构为「§0 单一入口 + 首步判别分流出 §1 翻译工作流 / §2 校对工作流」；90 行内嵌校对 Python 代码移入 `scripts/verify_translation.py`（新增边码/压缩段落/脚注三项一键初筛）与 `scripts/README.md`（offset 定位法参考实现）。**frontmatter**：description 补入 WHEN 触发短语（"翻译这段德语法律文本"/"translate this German legal text"/"校对这篇译文"等）。**规模**：SKILL.md 875 行 / 3899 词 → 703 行 / 3128 词（降至规范建议的 5000 词上限的 63%）。三个脚本全部回归测试通过。**移除待整理物料**：原 `_物料待整理_不入检索/`（德国物权法 OCR 原始 2001 条）从 skill 中删除，不再随 skill 分发（物权法文本改以术语表 I 与常规法律词典交叉核验）。**条数不变，全库仍为 8 160 条。**
- v6.7（V 表整体替换 + 全表「仅中德对照」清洗）：**术语表 V 推倒重建**——以穆泽拉克《德国民事诉讼法基础教程》书末「术语索引」（2 153 条，OCR 清洗后 2 120 条可用）为基线，并入原表 V 经校正的 1 427 条独有条目，合计 **3 541 条**（2 909 主 + 632 子）；其中 91 条核心主词条译名经人工核定校正，修复合并引入的「子词条义污染主词条」问题（如 Urteil→判决、Prozess→诉讼、Beweis→证据、Gerichtsstand→审判籍）。同时按用户要求「**词表仅为中德准确对照，不保留原书出现位置等内容**」对十张表全面清洗：剥离页码／边码／`ff.` 引用／「（见：X）」交叉引用、删除「所属／参见／译法提示」冗余列、无管道行归一为两列管道行；VII 来源一由四列压为两列并剔除 2 条垃圾行与 1 条纯参见指针（321→318）；VIII 修复 162 条德文字符级 OCR 损坏 + 59 条中文错配，删除 11 条不可复原碎片（526→515）；I 表补剥 6 处单 `f.` 页码残留与 2 处 `305a f` 残尾、修复 `Ü bermittlungsirrtum` 词中断裂、拆分 2 条「词条粘连」行（复原 `elektronische Form`、`gemischte Verträge` 两个独立词条）。`Verurteilung` 单独出现一律译「判决／裁判」的判别规则写入术语表 VI 与 SKILL.md F 块（VI 增至 19 条）；IX 表 `Kontrollierte Familiengesellschaft` 经用户核定译为「被控制的家族公司」；V 表删除 2 条 OCR 拼接残条。**公网语义核查**（借 Duden／Rechtswörterbuch／判例文献逐条核验德语词形规范性）：修复 VIII/IX/X 三表 38 处 umlaut 损坏（Kiindigung→Kündigung、Griindung→Gründung、Patientenverfiigung→Patientenverfügung 等）、合并 IX 表两条 Holzmiiller 残条为规范词条 Holzmüller-Doktrin、修复 V/IV/I 表 5 处 OCR 缺字、清除 I/V 表 17 处德文列引号污染。全库终检 **8 160 条、0 重复、0 损伤、0 页码残留、0 引号污染**（勘误详见「九、术语表勘误记录」第 8–15 条）
- v6.6（语句组织模块重构 + 勘误续）：针对 Klöhn 文第 819 页实译中暴露的「**规则达标而文本变坏**」问题，重构 SKILL.md 文风规范「句式」小节——原「单句 ≤30 字，无论是否需要保留德语嵌套结构」只有阈值（目的地）而无方法（路线图），导致压字数的路径退化为就近切断句法成分。新增 **S1 拆句四条底线**（残句禁令／拆分点限定／压缩优先于断开／过度拆句反向检测）、**S2 分层句长阈值**（论证句 ≤30 字、含完整法条引用串的句子 ≤45 字、脚注文献目录行不受限）、**S3 虚拟条件式不得改设问**、**S4 限定语回指须前置为定语**、**S5 断句正确性优先于句数**；并将「过度拆句反向检测」接入第 4 步阻断标准第 7 项，使短句纪律由单向约束变为**双向约束**。同步修订术语表 VIII 两条待观察词条（详见「九、术语表勘误记录」第 6–7 条）
- v6.5（术语表勘误）：在两次实译（Looschelders/Erm 文 B 部分、Klöhn 文第 819 页）中查出 **5 条** OCR 损坏或错译词条，已就地修订（详见下方「九、术语表勘误记录」）。条数与结构不变，仅修正译名；其中 `Überweisung`、`Verbotsgesetz` 统一为高位表 I 的既有正确译法，消除了两处跨表冲突
- v6.4（商法·双来源合并）：卡纳利斯《德国商法》（杨继译）书末术语索引 1776 条并入**术语表 VII** 作为**来源二**——沿用既有 OCR 清洗流水线（step0 机械清洗去纯参见指针与右缘残尾 → 字母切 7 块 → 逐块语义补全「德语前缀＋中文互证」→ 规范形去重 → 与来源一去重 → 按德语字母排序 → QA 断言），以「**宁缺毋滥**」口径收录 **1099 条**，合计 1420 条；来源一（案例研习版）原有 321 条节结构与内容未改动。20 条跨来源译法差异以非表格形式并列于来源二节首（不被检索脚本抓取），并新增 SKILL.md 加载规则第 14 条
- v6.0（商法入表）：术语表 VII 独立成表，覆盖 HGB 商事组织 / 行纪 / 代理商 / 买卖 / 商号

## 九、术语表勘误记录

> 词条在实译中被 `term_pre_check.py` 命中、但译名明显为 OCR 损坏或错译时，按铁则 2（偏离加注原文）在译稿中标注，并在此登记。**修订权属用户**——经用户确认后方就地改写术语表本体。
> 修订原则：**条数与结构不变，只改译名**；能与更高位阶表取得一致的，优先统一到高位表译法，以消除跨表冲突。

| # | 术语表 | 词条 | 原译（错） | 现译 | 类型 | 发现于 | 依据 |
|---|---|---|---|---|---|---|---|
| 1 | VII 德国商法 | Dispositives Recht | ~~处分性法律~~ | **任意法** | 错译 | Looschelders/Erm 文 B 部分 | dispositives Recht 指可由当事人另行约定排除的规范，与「处分」(Verfügung) 无关 |
| 2 | IX 公司与合伙法 | Rechtsschein | ~~法律表~~ | **权利外观** | OCR 右缘截断 | 同上 | 「权利外观」残为「法律表」；表 VII 已作「权利外观」 |
| 3 | VIII 债法总论 | Überweisung | ~~汇人~~ | **转账** | OCR 错字（款→人） | 同上 | 统一为表 I（位阶更高）既有译法「转账」，消除跨表冲突 |
| 4 | VIII 债法总论 | Verbotsgesetz | ~~禁引法~~ | **禁止性法律** | OCR／识别错误 | Klöhn 文第 819 页 | 「禁止性法律」残为「禁引法」；表 I 已作「禁止性法律」 |
| 5 | V 民事诉讼法 | ↳ bei Verurteilung | ~~在判处发出意思表示时强制700执行\*~~ | **在判决作出意思表示时强制执行** | 错译＋OCR 残留 | Klöhn 文第 819 页（`Verurteilung`） | Verurteilung 为「判决／判令（被告为给付）」，与「判处」（Strafe／刑罚裁量）无关；顺带清除行尾 OCR 残留「700」与「\*」。修订后全库 `Verurteilung` 仅此 1 处命中 |

> 说明：第 5 条在 Klöhn 译稿中先按铁则 2 以「<mark>判处</mark>（Verurteilung）」加注原文处理，经用户裁定「Verurteilung 应译**判决**」后就地修订。
| 6 | VIII 债法总论 | Verarbeitmg und Riicktrit | ~~却工与解除~~ | **加工与解除**（词形修为 Verarbeitung und Rücktritt） | OCR 替换（ung→mg、ü→ii）＋中文错字 | 修订第 5 条时邻近检出，用户一并授权 | 德语侧 `mg`→`ung`、`iick`→`ück` 为典型 OCR 替换；中文「却工」为「加工」之误 |
| 7 | VIII 债法总论 | Veraubnis | ~~婚约~~（德语侧损坏） | **婚约**（词形修为 Verlöbnis） | OCR 缺字（au→ö、缺 l） | 同上 | 中文「婚约」与 Verlöbnis 对应，中文侧本已正确，仅德语侧损坏 |
| 8 | V 民事诉讼法 | Urteil / Prozess / Beweis / Gerichtsstand 等 **91 条主词条** | ~~附条件的判决~~／~~支票诉讼~~／~~否定的事实之证据~~／~~驳回~~ 等 | **判决／诉讼／证据／审判籍** 等 | 合并引入的「子词条义污染主词条」 | v6.7 V 表整体替换 | 穆泽拉克索引的裸主词条被灌入其某一子词条的限定语义（如 `Urteil→附条件的判决`、`Prozess→支票诉讼`），单独检索会误译；经人工核定 91 条主词条译名（OVERRIDE 清单）后校正 |
| 9 | VIII 债法总论 | Aheitnehmer / Centechn / Umwelischiden 等 **162 条** | （德文侧 OCR 损坏） | **Arbeitnehmer / Gentechnik / Umweltschäden** 等（词形修复） | OCR 字符级替换 | v6.7 全表核对 | ä→a、G→C、t→d、ß→ss 等形近字符系统性损坏，逐条字符级还原；含「待观察」原 5 条（Unverhiltnismiissigkeit / Urlaub / Ursiichlichkeit / Valutaverhilinis / Varsatztheorie）一并修复 |
| 10 | VIII 债法总论 | Auskunftspflicht / Wechsel / Rechtsgrund 等 **59 条** | ~~告知党务~~／~~取回权（配错主词）~~／~~法律原因-(效果)引用~~ 等 | **告知义务**／**汇票**／**法律原因** 等 | 中文错配／错字 | v6.7 全表核对 | 中文侧错字与主词错配修复；另删除不可复原的「`第`字残片」与「德中双残」碎片行，526→515 条 |
| 11 | I BGB民法教义学 | Ü bermittlungsirrtum 等 | ~~传达错误~~（德文断裂）；`Einziehungsermächtigung` 行粘连 `elektronische Form` 词条、`Gemeinsames Europäisches Kaufrecht` 行粘连 `gemischte Vertrage` 词条 | **Übermittlungsirrtum**／传达错误；粘连行拆分复原 **elektronische Form**（电子形式）、**gemischte Verträge**（混合合同）两个独立词条 | OCR 词中空格＋词条粘连 | 同上 | 词中断裂复原、粘连行按字母序拆分；同表补剥 6 处单 `f.` 与 2 处 `305a f` 页码残留（`Schadensersatzpflicht des Anfechtenden 333 f` 等），797→799 条 |
| 12 | VIII / IX / X | Kiindigung / Griindung / Patientenverfiigung 等 **38 条** | （德文侧 umlaut 损坏） | **Kündigung / Gründung / Patientenverfügung** 等（词形修复） | OCR umlaut 损坏（ü→ii、ä→ii、ö→i 等） | v6.7 公网语义核查 | 借公网检索（Duden、Rechtswörterbuch、判例文献）逐条核验，确认 Massenschäden、Rücktrittsvorbehalt、Treuhandverhältnis、Gründer、Vergütung、Holzmüller-Doktrin 等为规范德语；VIII 修复 18 处、IX 修复 27 处、X 修复 10 处 umlaut 损坏 |
| 13 | IX 公司与合伙法 | Holzmiiller-DoktrinHolzmiiller / HolzmiillerDoktrinHolzmiiller | ~~判决理论~~（两条 OCR 拼接残条） | **Holzmüller-Doktrin**／霍尔茨米勒原则（合并为一条） | OCR 拼接＋umlaut 损坏 | 同上 | 两条残条系同一词条（1982 BGH 判例确立的股东大会不成立职权原则）的重复损坏，合并还原为规范条目，730→729 条 |
| 14 | V / IV / I | Dispostionsgrundsatz / Grundsatze / Schuldverhaltnis 等 **5 条** | （德文侧 OCR 错误） | **Dispositionsgrundsatz / Grundsätze / Schuldverhältnis** 等 | OCR 缺字／umlaut 缺失 | 同上 | V 表 Dispositionsgrundsatz（补 s）、IV 表 Grundsätze 与 Horizontal-/Vertikalverhältnis（补 umlaut）、I 表 Schuldverhältnis（补 umlaut） |
| 15 | I / V | neutrale Geschäfte / Strohmann / technisch zweitem / Wohnung 等 **17 处** | （德文列中文引号污染） | 清除德文列 `“ ” "` 引号残留 | OCR 引号污染 | 同上 | I 表 5 处、V 表 12 处德文列混入中文全角引号，逐条清除；V 表顺带修正 `u Flucht`→`und Flucht`（u 为 und 缩写误读） |

### 待观察

#### 1. 已处理（v6.7 关闭）

以下 5 条系第 6、7 条修订时于术语表 VIII 同一字母段（U–V）邻近检出，当时未获授权。**v6.7 全表核对时已获用户授权并一并修复**（并入勘误记录第 9 条），原表保留于下以供追溯：

| 术语表 | 词条 | 原现译 | 修复结果 |
|---|---|---|---|
| VIII 债法总论 | Unverhiltnismiissigkeit | 不成比例 | 词形修为 **Unverhältnismäßigkeit**，译名不变 |
| VIII 债法总论 | Urlaub | ~~体假~~ | 中文修为**休假** |
| VIII 债法总论 | Ursiichlichkeit | 原因关系 | 词形修为 **Ursächlichkeit**，译名不变 |
| VIII 债法总论 | Valutaverhilinis | ~~对价头系~~ | 词形修为 **Valutaverhältnis**、中文修为**对价关系** |
| VIII 债法总论 | Varsatztheorie | ~~艳意说~~ | 词形修为 **Vorsatztheorie**、中文修为**故意说** |

#### 2. 待用户裁定（v6.7 新增，推定重构／译名生硬）

以下条目在 v6.7 清洗中为复原或合并产物，**译名未经用户核定**，暂存待裁定：

| 术语表 | 词条 | 现译 | 说明 |
|---|---|---|---|
| IX 公司与合伙法 | Kontrollierte Familiengesellschaft | 被控制的家族公司 | 经用户核定（2026-09-09）：由「控制的家族合伙/公司」改定 |
| V 民事诉讼法 | Unterbrechung bei Wegfall der Prozessfähigkeit | 诉讼能力消失的情况程序中断 | 语序处理经用户认可，保留现译 |
| V 民事诉讼法 | Unterbrechung bei Wegfall der Vertretungsmacht | 在代理权消失的情况程序中断 | 同上，保留现译 |
| V 民事诉讼法 | Prozessbevollmächtigter Unterbrechung bei Wegfall | （已删除） | OCR 拼接残条，经用户裁定删除 |
| V 民事诉讼法 | Unterbrechung bei Wegfall der Vertretung Zurechnung von Verschulden | （已删除） | 德文为两条目拼接（`…Vertretungsmacht`＋`Zurechnung von Verschulden`），中德明显不对应，经用户裁定删除 |