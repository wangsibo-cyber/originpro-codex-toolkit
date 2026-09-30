# OriginPro / originpro 工作区规则

## 本地知识库

- 知识库路径：优先使用用户指定路径；否则使用当前项目的 `OriginPro_Codex_KB/`。禁止沿用发布者电脑的盘符。
- 在其他项目中工作时，只要用户提供该路径，先检索此知识库，再编写或修改 OriginPro 绘图代码。
- 推荐检索顺序：
  1. `OriginPro_Codex_KB/00_START_HERE.md`
  2. 论文格式、模板、图例、多面板或导出：
     `OriginPro_Codex_KB/07_PUBLICATION_GRAPHING_SUPPLEMENT/PUBLICATION_GRAPHING_QUICK_REFERENCE.md`
  3. 坐标轴：
     `OriginPro_Codex_KB/06_LABTALK_AXIS_SUPPLEMENT/LABTALK_AXIS_QUICK_REFERENCE.md`
     和 `VERIFICATION_REPORT.md`
  4. `OriginPro_Codex_KB/02_MARKDOWN/docs.originlab.com/originpro/`
  5. `OriginPro_Codex_KB/02_MARKDOWN/docs.originlab.com/externalpython/`
  6. `OriginPro_Codex_KB/04_OFFICIAL_PYTHON_SAMPLES/`
  7. `OriginPro_Codex_KB/05_ORIGINPRO_PYPI_PACKAGE/`

## OriginPro 绘图

- 本项目使用 Windows 外部 Python 通过 `originpro` 调用 OriginPro。
- API 名称、类、方法、属性和参数必须在本地 API Reference、官方示例或本机验证报告中得到确认，不得凭记忆虚构。
- 优先使用 `originpro` 高级 API；不要默认使用旧版 `PyOrigin` 或底层 `OriginExt`。
- 调试阶段调用 `op.set_show(True)`，保持 Origin 可见。
- 外部 Python 脚本必须在 `finally` 中调用 `op.exit()`，避免残留 Origin 进程。
- 论文图优先基于项目提供的 `.otp/.otpu` 模板生成。
- 只有高级 API 无法实现时，才使用 `op.lt_exec()` 调用 LabTalk，并在代码注释中说明原因。
- Origin 直接导出遇到中文路径问题时，先写入 ASCII 临时目录，成功后再复制到最终目录。
- 输出脚本必须显式配置数据路径、模板路径、图片路径、图像尺寸/DPI和 OPJU 保存路径。

### OriginPro论文绘图与出版格式规则

- 线、符号、分组、颜色映射、图例、标注、误差棒、模板/主题、多图层和导出，
  优先检索 `OriginPro_Codex_KB/07_PUBLICATION_GRAPHING_SUPPLEMENT/`。
- 必须区分 Page、Layer、Plot 和图形对象的属性归属。
- Origin Help中的GUI选项用于确认功能语义，不得据此猜测Python API或LabTalk属性。
- 大量重复视觉格式优先固化到 `.otp/.otpu` 模板或图主题。
- 图例更新必须区分 Update 与 Reconstruct；多图层图应明确使用每层图例还是整页图例。
- 文本、标注和参考线必须明确附着到 Page、Layer Frame 或 Layer and Scales。
- 多面板图必须明确行列数、边距、层间距、轴链接和元素缩放方式。
- 导出必须明确最终格式、物理尺寸或像素宽度、DPI、背景、裁边和覆盖策略。
- 最终交付必须包含OPJU及至少一张实际导出并视觉检查过的PNG/TIFF/PDF。

### OriginPro LabTalk 轴控制规则

- 复杂坐标轴格式设置优先检索 `OriginPro_Codex_KB/06_LABTALK_AXIS_SUPPLEMENT/`。
- 不得猜测 LabTalk 对象属性或数值枚举。
- `majorTicks`、GUI **By Counts** 等“数量”设置不应解释为严格保证。
- 强制端点刻度时，必须检查 From、To、Increment、Anchor Tick 和自定义刻度位置之间的关系；任意非整除范围优先显式使用 `TicksByData$`。
- 刻度方向必须区分主刻度和次刻度；不得混用 `layer.axis.ticks` 位掩码与 `layer.tickstyle` 枚举。
- 必须区分单轴设置、图层设置和 Origin 会话/全局设置。
- 只有官方文档或本机验证脚本确认后，才能将属性写入正式绘图代码。
- 标题字体/粗体使用官方文本转义 `\f:`、`\b()`，字号使用 `fsize`；不得猜测 `xb.font`、`xb.bold`。
- `layer.axis.label.italic` 未获对象文档支持且本机读回为 `NaN`，不得使用。
- `xt.show`、`yr.show` 曾在发布者的 OriginPro 2024b 环境验证；这不代表使用者本机已验证，正式使用前需重新检查。
- `originpro` 高级 API 不能实现时，才使用 `op.lt_exec()`。
