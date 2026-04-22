---
title: ObsidianToWiki Multimodal Support Plan
status: draft
updated: 2026-04-17
summary: 面向图片、语音、视频的多模态支持落地方案，按 P0 / P1 / P2 拆分目录改造、脚本清单、处理链路和实施顺序。
---

# ObsidianToWiki Multimodal Support Plan

## 1. Goal

这份方案的目标不是一次性把图片、语音、视频做成“大而全”的多模态平台，而是在当前系统已有的文本型摄入和项目记忆体系上，补出一条可渐进落地、可维护、可回写的多模态处理链路。

这条链路需要满足 4 个要求：

1. 原始媒体文件能安全进入系统
2. 媒体文件能生成标准来源笔记
3. 解析结果能继续沉淀到项目页、个人页、共享页
4. 整个过程仍然遵守当前 wiki 的输入层、记忆层、自动化层分离原则

## 2. Scope

本次方案覆盖三类媒体：

- 图片
- 语音
- 视频

本次方案不包含：

- 实时流媒体
- 在线会议自动接入
- 大规模多媒体内容管理平台能力
- embedding / 向量检索层设计

## 3. Design Principles

### 3.1 先入库，再解析，再沉淀

不要把“接收媒体文件”和“自动理解内容”绑定成一步。正确顺序应当是：

1. 文件进入系统
2. 生成来源笔记和状态字段
3. 运行媒体解析
4. 将解析结果回写为结构化知识

### 3.2 原始媒体文件不可改写

和 `01_inbox/raw/` 的规则一致，原始媒体文件只做存档，不做覆盖式改写。

### 3.3 多模态也必须走来源状态机

图片、语音、视频都不应该绕过当前系统的来源状态机。它们应该和 PDF / 文档一样，有统一的来源登记、解析状态、衍生页面链路。

### 3.4 解析结果是中间资产，不是最终知识

OCR 文本、语音转写、关键帧摘要、时间轴片段，都只是中间资产。最终长期知识仍应写入项目页、个人页、共享页或输出页。

### 3.5 默认走用户自己的 LLM / API 解析能力

这套系统的职责不是把 OCR / ASR / 视频理解硬编码成某一个本地工具链，而是：

1. wiki 负责入库、来源登记、状态管理、回写、索引、治理
2. 用户自己的多模态 LLM / API 负责识别、理解、提取

本地工具链可以存在，但只能作为可选兜底，不应成为默认主路径。

## 4. Target Processing Flow

```text
原始媒体文件
    ->
raw 入库
    ->
来源笔记创建
    ->
媒体类型识别
    ->
解析任务
图片: 用户 LLM / API 做 OCR / caption / 内容理解
语音: 用户 LLM / API 做 ASR / 分段摘要
视频: 用户 LLM / API 做音轨转写 / 时间轴摘要 / 关键帧理解
    ->
中间产物写入 scratch
    ->
来源笔记更新状态
    ->
沉淀到项目页 / 个人页 / 共享页 / outputs
```

## 5. Directory Changes

### 5.1 `01_inbox/raw/`

当前 `raw` 已经存在，但多模态落地后建议按角色和媒体类型细分。

建议结构：

```text
01_inbox/raw/
├─ personal/
│  ├─ images/
│  ├─ audio/
│  └─ video/
├─ projects/
│  └─ <project-slug>/
│     ├─ images/
│     ├─ audio/
│     └─ video/
└─ imports/
```

说明：

- `personal/` 放个人素材
- `projects/<project-slug>/` 放项目相关媒体
- `imports/` 放暂时还没明确归属的导入内容

### 5.2 `01_inbox/scratch/`

建议为多模态中间产物加子目录：

```text
01_inbox/scratch/
├─ ocr/
├─ transcripts/
├─ keyframes/
└─ summaries/
```

说明：

- `ocr/` 放图片识别文本或图片理解中间结果
- `transcripts/` 放语音和视频转写
- `keyframes/` 放视频关键帧或相关中间结果
- `summaries/` 放分段摘要、时间轴摘要等临时产物

### 5.3 项目目录

项目内部建议继续沿用现有结构，不额外新建一套复杂媒体目录。原则是：

- 原始媒体文件进项目 `sources/`
- 来源笔记进项目 `source-notes/`
- 解析中间产物优先进全局 `01_inbox/scratch/`

这样可以保持项目目录简洁。

## 6. Metadata Changes

多模态来源笔记建议增加以下字段。

### Core fields

- `media_type: image | audio | video | document`
- `parse_status: 待处理 | 处理中 | 已转写 | 已提取 | 已摘要 | 已沉淀 | 失败`
- `source_hash`
- `source_path`
- `derived_pages`
- `recommended_targets`

### Optional fields

- `duration_seconds`
- `language`
- `speaker_count`
- `frame_count`
- `has_ocr_text`
- `has_transcript`
- `has_keyframes`
- `review_due`

### Error tracking fields

- `parse_error`
- `last_parse_attempt`

## 7. Media-Specific Handling

## 7.1 Image

### Input examples

- 截图
- 白板照片
- 架构图
- 界面设计图
- 拍照保存的文档页

### Processing goals

- 提取图片文字
- 理解图片表达的结构和语义
- 给出一句话说明
- 在适合时沉淀成结构化知识

### Expected outputs

- OCR 文本
- 图片说明 / caption
- 关键标签
- 适合沉淀到哪个页面的建议

### Most suitable final destinations

- 项目 `架构.md`
- 项目 `来源.md`
- 项目 `决策.md`
- 个人知识页
- 输出分析页

## 7.2 Audio

### Input examples

- 会议录音
- 访谈录音
- 灵感口述备忘
- 课程音频

### Processing goals

- 语音转写
- 按时间或语义分段
- 提取关键决策 / 任务 / 风险 / 观点

### Expected outputs

- transcript 文本
- 分段摘要
- action items
- 决策候选

### Most suitable final destinations

- 项目 `任务.md`
- 项目 `决策.md`
- 项目 `风险.md`
- 个人方法论页
- 输出简报页

## 7.3 Video

### Input examples

- 产品演示录像
- 培训视频
- 会议录像
- 教程视频
- 屏幕录制

### Processing goals

- 抽取音轨并转写
- 关键帧提取
- 基于关键帧和转写生成时间轴摘要

### Expected outputs

- transcript
- keyframes
- timeline summary
- 关键步骤 / 关键结论 / 风险点

### Most suitable final destinations

- 项目 `架构.md`
- 项目 `概览.md`
- 项目 `来源.md`
- 输出分析页
- 共享教程页

## 8. P0 / P1 / P2 Roadmap

## P0: 先让多模态“能进入系统、能被登记、能继续处理”

### Goal

让图片、语音、视频像 PDF 一样至少可以进入系统，并被当成正式来源管理。

### Directory work

- 调整 `01_inbox/raw/` 子目录结构
- 调整 `01_inbox/scratch/` 子目录结构
- 保持项目 `sources/` 和 `source-notes/` 结构不变

### Schema work

- 给来源笔记补 `media_type`
- 给来源笔记补 `parse_status`
- 给来源笔记补多模态可选字段

### Script work

建议新增或改造：

1. `ingest_source.py`
   增加媒体类型识别和媒体文件入库能力
2. `schema_lib.py`
   增加多模态来源字段校验
3. `lint_wiki.py`
   增加多模态来源状态检查

### Expected output

- 图片 / 语音 / 视频能正式入库
- 来源笔记能登记媒体类型和处理状态
- 系统知道哪些媒体还没被解析

## P1: 让多模态“能被解析并产出可用中间资产”

### Goal

补齐媒体解析链路，让系统不只存文件，还能得到 OCR、转写、关键帧和摘要。
这里的“解析器”默认应当理解为用户自己的多模态 LLM / API，而不是固定为本地工具。

### Directory work

- 启用 `scratch/ocr/`
- 启用 `scratch/transcripts/`
- 启用 `scratch/keyframes/`
- 启用 `scratch/summaries/`

### Script work

建议新增：

1. `parse_image_source.py`
   负责调用用户 LLM / API，对图片做 OCR、caption、标签提取或内容理解
2. `parse_audio_source.py`
   负责调用用户 LLM / API，对语音做转写、分段摘要、行动项提取
3. `parse_video_source.py`
   负责调用用户 LLM / API，对视频做转写、关键帧理解、时间轴摘要
4. `sync_media_notes.py`
   把解析结果同步回来源笔记 frontmatter 和正文

### Supporting templates

建议补充或调整：

- `source-note.md`
  加入媒体处理状态、解析结果摘要、关键链接

### Expected output

- 图片有 OCR 和图片摘要
- 语音有转写和分段摘要
- 视频有转写、关键帧和时间轴摘要

## P2: 让多模态“能真正沉淀成项目知识和个人知识”

### Goal

让多模态结果不只停留在来源笔记或 scratch，而是进入正式知识层。

### Script work

建议新增：

1. `promote_media_insights.py`
   根据媒体解析结果建议沉淀目标并执行半自动回写
2. `recommend_media_promotions.py`
   给来源笔记写入适合提升到哪里
3. `file_back_media_summary.py`
   把媒体摘要沉淀到项目页、个人页、共享页或 outputs

### Governance work

建议扩展：

- `lint_wiki.py`
  检查“媒体已解析但未沉淀”
- `discover_learning_candidates.py`
  将高价值多模态来源纳入共享候选发现

### Expected output

- 白板照片可进入项目架构页
- 会议录音可进入任务页和决策页
- 产品演示视频可进入项目概览或共享教程页

## 9. Script Checklist

不写代码的前提下，明天实现时可按下面顺序推进。

### P0 script checklist

- 改 `ingest_source.py`
- 改 `schema_lib.py`
- 改 `lint_wiki.py`

### P1 script checklist

- 新增 `parse_image_source.py`
- 新增 `parse_audio_source.py`
- 新增 `parse_video_source.py`
- 新增 `sync_media_notes.py`

### P2 script checklist

- 新增 `promote_media_insights.py`
- 新增 `recommend_media_promotions.py`
- 新增 `file_back_media_summary.py`

## 10. Recommended Execution Order

明天真正开始实现时，建议按这个顺序，不要跳。

1. 先做 P0
2. 先让媒体入库和状态字段打通
3. 再做图片解析
4. 再做语音解析
5. 最后做视频解析
6. 等解析稳定后，再做自动沉淀

原因很简单：

- 图片最容易验证
- 语音次之
- 视频链路最长，最容易把复杂度拉爆

## 11. Risks

- 多模态解析比文本解析更容易引入大体积中间产物
- 视频处理最容易拖慢整套系统
- OCR / ASR 质量会直接影响后续沉淀质量
- 如果过早自动沉淀，容易把低质量内容写进主知识层

## 12. Recommended ADR-Level Decisions

### Decision A

多模态必须继续走“来源笔记 -> 解析 -> 沉淀”链路，而不是直接写正式知识页。

### Decision B

默认不要把某个本地 OCR / ASR 工具写死成唯一实现；应优先设计为“统一协议 + 可替换解析后端”。

### Decision C

解析中间产物统一进入 `01_inbox/scratch/`，不把项目目录塞满中间文件。

### Decision D

自动沉淀必须晚于媒体解析稳定，否则会污染正式知识层。

## 13. Tomorrow Implementation Plan

如果明天开始做，建议按这三步开工：

1. 调整目录和 schema
2. 改造 `ingest_source.py` 让媒体文件可正式入库
3. 先做图片解析链路

做到这一步，就已经完成 P0 并进入 P1 起点。
