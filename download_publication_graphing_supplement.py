#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download a curated official OriginLab publication-graphing supplement.

The base knowledge library already contains the originpro API, Python examples,
and a verified LabTalk axis supplement.  This downloader intentionally focuses
on Origin's graph-formatting model and publication workflow so that the local
library gains useful depth without mirroring the entire Origin Help site.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from download_labtalk_axis_supplement import (
    DocumentRecord,
    DocumentSpec,
    local_paths,
    relative_posix,
    write_document,
)


REQUEST_DELAY_SECONDS = 0.25
RETRY_COUNT = 3
SUPPLEMENT_DIRNAME = "07_PUBLICATION_GRAPHING_SUPPLEMENT"


def doc(category: str, slug_or_url: str, purpose: str, relation: str) -> DocumentSpec:
    if slug_or_url.startswith("http"):
        url = slug_or_url
    else:
        url = f"https://docs.originlab.com/origin-help/{slug_or_url.strip('/')}/"
    return DocumentSpec(category, url, purpose, relation)


DOCUMENTS = [
    # Page / layer / plot object model
    doc(
        "绘图对象层级",
        "page-layer-plot-hierarchy",
        "解释Origin图页、图层、数据绘图和特殊点的层级。",
        "帮助将originpro的GPage、GLayer和Plot对象映射到Origin界面。",
    ),
    doc(
        "绘图对象层级",
        "customize-page-element",
        "图页尺寸、方向、背景、网格和Master Page。",
        "为论文图物理尺寸、统一背景和批量页眉页脚提供依据。",
    ),
    doc(
        "绘图对象层级",
        "customize-layer-element",
        "图层尺寸、背景、裁剪、缩放元素和显示控制。",
        "辅助判断设置应落在图页、图层还是曲线对象。",
    ),
    doc(
        "绘图对象层级",
        "customize-plot-element",
        "曲线、符号、柱形、标签等数据绘图元素总览。",
        "补足originpro Plot对象之外的Origin格式化概念。",
    ),
    doc(
        "绘图对象层级",
        "compare-pageview-modes",
        "比较Draft、Window、Page和Print视图的速度与精度。",
        "避免把屏幕预览差异误判为最终导出质量问题。",
    ),
    doc(
        "绘图对象层级",
        "plot-details-controls",
        "Plot Details全部绘图级标签页的官方入口。",
        "作为originpro不能直接暴露的高级格式设置索引。",
    ),

    # Plot Details controls
    doc(
        "Plot Details曲线格式",
        "pd-dialog-sym-tab",
        "符号形状、大小、边框、填充、透明度和按列映射。",
        "核对散点和线加符号图的Plot属性及模板设置。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-line-tab",
        "连线方式、线型、宽度、颜色、透明度和曲线下填充。",
        "核对折线、轨迹、填充区域和箭头的高级格式。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-plotlevel-display-tab",
        "控制曲线元素显示、双轴归属和绘制范围。",
        "用于多Y轴和按范围显示数据的图形自动化设计。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-spacing-tab",
        "柱、条、直方图等图形的宽度、间距和重叠设置。",
        "补充originpro对柱形图几何参数的高级控制背景。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-errbar-tab",
        "误差棒方向、线宽、端帽、透明度和填充区域。",
        "核对误差棒列加入图层后的论文格式设置。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-label2-tab",
        "现代数据标签来源、数值格式、位置、旋转和防重叠。",
        "补充曲线标签的Origin侧完整控制。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-dropline-tab",
        "垂线、投影线和指定点位置设置。",
        "用于峰值标记、棒棒糖图和辅助投影线。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-group-tab",
        "分组曲线的颜色、符号、线型、增量和子组规则。",
        "是批量多曲线统一风格与组内递增的核心参考。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-colormap-tab",
        "色阶、调色板、级别、缺失值和颜色映射。",
        "用于热图、等值线、曲面和彩色散点的颜色控制。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-colorlist-tab",
        "分组数据绘图的颜色列表。",
        "核对组内颜色递增和自定义色盲友好列表。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-patternlist-tab",
        "分组图的图案列表。",
        "用于黑白印刷和颜色以外的组别编码。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dlg-shape-list-tab",
        "分组或索引符号的形状列表。",
        "用于通过符号形状表达第二分类变量。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dlg-interior-list-tab",
        "符号内部样式列表。",
        "用于空心、实心和内部图案递增。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-pattern-tab",
        "柱形、面积和误差区域的填充图案、颜色与透明度。",
        "用于期刊黑白打印及置信区间填充。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-contourfill-tab",
        "等值线图的填充、缺失值和边界控制。",
        "补充二维等值线及矩阵科研图的格式化依据。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-dialog-contourlines-tab",
        "等值线线条、主次线和标签关联设置。",
        "补充等值线线宽、颜色与级别显示控制。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-subset-tab",
        "按行、范围或条件绘制数据子集。",
        "用于大数据抽样显示和局部绘图。",
    ),
    doc(
        "Plot Details曲线格式",
        "pd-line-style-list-tab",
        "分组曲线的线型递增列表。",
        "用于颜色与线型双编码及黑白出版。",
    ),

    # Dataset-driven formatting
    doc(
        "按数据驱动样式",
        "customize-plotcolor",
        "Origin颜色选择、索引、映射和递增方式总览。",
        "为originpro颜色值、调色板和模板选择提供官方语义。",
    ),
    doc(
        "按数据驱动样式",
        "plotcolor-datasetcontrol",
        "使用数据列控制线、符号或填充颜色。",
        "用于按实验条件或数值变量动态着色。",
    ),
    doc(
        "按数据驱动样式",
        "plotattribute-datasetcontrol",
        "使用数据列控制大小、形状、线宽、透明度等属性。",
        "用于气泡图、多变量散点和分类科研图。",
    ),
    doc(
        "按数据驱动样式",
        "match-modifiers-by",
        "多曲线间按X值、行号或索引匹配样式修饰列。",
        "避免不同曲线长度或X值不一致时错误套用样式。",
    ),
    doc(
        "按数据驱动样式",
        "plotsetup-editdisplayrange",
        "编辑曲线在图层中的显示数据范围。",
        "区分裁剪显示与修改源数据。",
    ),
    doc(
        "按数据驱动样式",
        "specific-plot-element",
        "单独修改特殊数据点或绘图元素。",
        "用于突出峰值、异常点或关键工况。",
    ),

    # Templates and themes
    doc(
        "模板与主题",
        "graph-template-basics",
        "Origin图模板的用途、存储位置和基本工作流。",
        "指导originpro new_graph(template=...)优先复用论文模板。",
    ),
    doc(
        "模板与主题",
        "graph-template-elements",
        "列出图模板保存的图页、图层、轴、对象和曲线属性。",
        "判断哪些格式可固化到OTP/OTPU而无需每次脚本重设。",
    ),
    doc(
        "模板与主题",
        "system-templates",
        "Origin内置系统模板与用户覆盖机制。",
        "避免直接修改安装目录模板，并理解同名用户模板优先级。",
    ),
    doc(
        "模板与主题",
        "graph-template-gallery",
        "模板库的添加、搜索、分类、克隆和数据结构检查。",
        "帮助管理供originpro调用的用户模板和克隆模板。",
    ),
    doc(
        "模板与主题",
        "template-center",
        "Origin官方在线模板中心。",
        "作为可选模板扩充入口，不自动下载未知第三方模板。",
    ),
    doc(
        "模板与主题",
        "ofiletype-template",
        "OTW/OTP/OTM及Unicode模板文件类型说明。",
        "区分工作簿、图形和矩阵模板文件。",
    ),
    doc(
        "模板与主题",
        "graphing-batch-plotting",
        "基于克隆模板、复制列和复制工作表的批量绘图。",
        "为外部Python批量创建一致图件提供Origin侧方案。",
    ),
    doc(
        "模板与主题",
        "graph-format-theme",
        "图格式、主题与模板的作用差异。",
        "决定重复绘图时应使用模板、主题还是脚本属性。",
    ),
    doc(
        "模板与主题",
        "customizeorigin-theme",
        "Origin主题类型和复用机制。",
        "理解图主题、系统递增列表和导出对话框主题。",
    ),
    doc(
        "模板与主题",
        "themeref-themeorganizer",
        "主题管理器和系统递增列表。",
        "用于管理颜色、线型、符号列表以及批量应用图主题。",
    ),
    doc(
        "模板与主题",
        "theme-reference",
        "主题编辑、保存、筛选和系统主题参考入口。",
        "为后续细化主题自动化提供官方索引。",
    ),
    doc(
        "模板与主题",
        "copypaste-format",
        "在图页、图层、曲线和对象间复制粘贴格式。",
        "用于快速统一既有图件而不重建数据和图层。",
    ),

    # Legends, annotations, labels, and reference lines
    doc(
        "图例标注与误差",
        "legend-colorscale",
        "数据图例、分类图例、逐点图例和色标总览。",
        "为自动重建图例和多图层图例选择正确对象类型。",
    ),
    doc(
        "图例标注与误差",
        "legend-catedata",
        "分类变量图例的生成、排序和映射属性。",
        "用于颜色、形状、大小等分类映射的自动图例。",
    ),
    doc(
        "图例标注与误差",
        "pts-pts-legend",
        "逐点图例及其标签来源和排序。",
        "用于每个点代表不同试样或工况的图件。",
    ),
    doc(
        "图例标注与误差",
        "colorscale",
        "色标对象、刻度、标题、位置和独立色标。",
        "用于热图、等值线和映射散点的色标控制。",
    ),
    doc(
        "图例标注与误差",
        "box-legend",
        "箱线图组件图例。",
        "用于统计图中箱体、须线、中位数等组件说明。",
    ),
    doc(
        "图例标注与误差",
        "legend-manualcontrol",
        "图例对象结构、替换语法、符号、文字和高级自定义。",
        "在高级API不足时提供经官方说明的LabTalk图例语义。",
    ),
    doc(
        "图例标注与误差",
        "bubblescale",
        "气泡尺寸比例尺。",
        "用于符号大小映射的定量说明。",
    ),
    doc(
        "图例标注与误差",
        "legendupdate-dlg",
        "更新或重建当前层及整页图例。",
        "区分Update和Reconstruct并支持多图层整页图例。",
    ),
    doc(
        "图例标注与误差",
        "pd-dialog-legendtitles-tab",
        "图例翻译模式、自动更新、标题和整页图例设置。",
        "用于从列长名称、单位和注释自动生成稳定图例。",
    ),
    doc(
        "图例标注与误差",
        "add-datalabel-errbars",
        "数据标签与误差棒功能总入口。",
        "帮助设计源工作表的Label和Error列。",
    ),
    doc(
        "图例标注与误差",
        "labelling-datapoint",
        "为全部或指定数据点添加标签。",
        "用于自动选择标签来源、数值格式、偏移和旋转。",
    ),
    doc(
        "图例标注与误差",
        "creating_annotation",
        "Annotation工具的选点、引线和动态替换。",
        "用于精确标注峰值、拐点和关键数据点。",
    ),
    doc(
        "图例标注与误差",
        "add-errbar-to-graph",
        "向2D/3D图添加X/Y误差棒的多种方式。",
        "指导originpro工作表列设计和绘图数据指定。",
    ),
    doc(
        "图例标注与误差",
        "create-textlabel",
        "文本标签、特殊字符、变量链接和LabTalk格式。",
        "用于标题、说明文字、公式和动态元数据标签。",
    ),
    doc(
        "图例标注与误差",
        "attachment-scaling-object",
        "对象附着到Page、Layer Frame或Layer and Scales的差异。",
        "避免合并图层或改变轴范围后标注漂移、缩放错误。",
    ),
    doc(
        "图例标注与误差",
        "ref-textlabel-drawingobjects",
        "文本、图例、标注和绘图对象属性页索引。",
        "作为对象位置、边框、填充、引线和脚本属性入口。",
    ),
    doc(
        "图例标注与误差",
        "insert-axis-related-objects",
        "快速添加直线、参考线和统计参考位置。",
        "补充轴补充包之外的辅助线工作流。",
    ),
    doc(
        "图例标注与误差",
        "axesref-reflines",
        "参考线位置、样式、填充和标签格式。",
        "用于阈值、均值、规范上下限和区域着色。",
    ),

    # Multi-panel and layer management
    doc(
        "多图层与组合图",
        "graphref-arrangelayers",
        "按行列排列图层、设置间距和边距。",
        "用于多面板论文图的图层几何布局。",
    ),
    doc(
        "多图层与组合图",
        "graphref-layermanage",
        "添加、排列、链接和选择图层的管理入口。",
        "用于双Y轴、多面板和共享坐标轴图。",
    ),
    doc(
        "多图层与组合图",
        "graphref-mergegraph",
        "将多个图页合并为多面板图。",
        "说明元素缩放、图层链接、边距、间距和标签。",
    ),
    doc(
        "多图层与组合图",
        "graphref-extractlayer",
        "把多图层图拆分为独立图页。",
        "用于批量重排或单独导出已有面板。",
    ),
    doc(
        "多图层与组合图",
        "graphref-mergegraphstolayout",
        "把多个图页合并到Layout页面。",
        "用于保留独立图页并生成综合版面。",
    ),
    doc(
        "多图层与组合图",
        "graphref-scalerprop-dialog",
        "合并和缩放时控制图层元素比例。",
        "避免字体、符号、线宽在面板缩放时失衡。",
    ),
    doc(
        "多图层与组合图",
        "layern-dialog",
        "图层内容、曲线顺序、分组和移除。",
        "对应originpro向图层添加/重排曲线后的Origin侧管理。",
    ),
    doc(
        "多图层与组合图",
        "graphref-plotsetup-dialog",
        "Plot Setup数据范围、图层和绘图类型分配。",
        "帮助理解复杂XYY、误差棒和多图层数据映射。",
    ),

    # Export and publication
    doc(
        "出版与导出",
        "export-publish-graphs",
        "导出、布局、Master Page、打印和嵌入总入口。",
        "作为论文图交付工作流的官方索引。",
    ),
    doc(
        "出版与导出",
        "expgraph-to-image",
        "图页和Layout导出为矢量或位图文件。",
        "选择PNG/TIFF/PDF/SVG/EMF并理解尺寸、DPI和批量导出。",
    ),
    doc(
        "出版与导出",
        "expgraph-format-comprison",
        "比较各种矢量与位图导出格式。",
        "为期刊投稿、Office嵌入和后期编辑选择格式。",
    ),
    doc(
        "出版与导出",
        "simple-expgraph-dailog",
        "快速Export Graph as Image对话框。",
        "用于单图快速导出和预览。",
    ),
    doc(
        "出版与导出",
        "expgraph-dailog",
        "高级Export Graph对话框总参考。",
        "对应批量导出、命名、范围和覆盖策略。",
    ),
    doc(
        "出版与导出",
        "settings-in-expgraph-dailog",
        "高级导出设置的完整属性树。",
        "核对分辨率、尺寸、颜色、透明度、抗锯齿和格式专属设置。",
    ),
    doc(
        "出版与导出",
        "export-margin_offsets",
        "导出边界和偏移。",
        "用于精确裁边并避免图注或对象被截断。",
    ),
    doc(
        "出版与导出",
        "paste-embed-ole",
        "在Word、PowerPoint等应用中粘贴或嵌入Origin图。",
        "用于可编辑OLE与静态矢量图之间的选择。",
    ),
    doc(
        "出版与导出",
        "expgraph-layout-window",
        "Layout页面的创建、链接、排列和导出。",
        "用于图、表、图片混合的复合版面。",
    ),
    doc(
        "出版与导出",
        "master-page-layout",
        "Master Page批量添加公共对象和背景。",
        "用于项目内统一Logo、页眉页脚和声明。",
    ),
    doc(
        "出版与导出",
        "printing",
        "Origin打印工作流入口。",
        "保留完整出版流程的官方参考。",
    ),
    doc(
        "出版与导出",
        "https://docs.originlab.com/x-function/ref/expgraph/",
        "expGraph X-Function命令行、变量、格式和示例。",
        "当originpro save_fig不足时，为op.lt_exec调用官方导出命令提供依据。",
    ),
]


def normalized_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url.strip())
    path = parsed.path.rstrip("/").lower()
    return urllib.parse.urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", "")
    )


def load_existing_urls(kb_root: Path) -> dict[str, list[str]]:
    sources = [
        kb_root / "manifest.json",
        kb_root / "06_LABTALK_AXIS_SUPPLEMENT" / "manifest_labtalk_axis.json",
    ]
    result: dict[str, list[str]] = {}
    for path in sources:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in payload.get("documents", []):
            for key in ("official_url", "final_url", "url"):
                url = item.get(key)
                if not url:
                    continue
                result.setdefault(normalized_url(url), []).append(path.as_posix())
    return result


def download_with_retry(root: Path, spec: DocumentSpec) -> DocumentRecord:
    record: DocumentRecord | None = None
    for attempt in range(1, RETRY_COUNT + 1):
        record = write_document(root, spec)
        if record.status == "ok":
            return record
        if attempt < RETRY_COUNT:
            time.sleep(1.5 * attempt)
    assert record is not None
    return record


def record_from_existing(root: Path, spec: DocumentSpec) -> DocumentRecord | None:
    """Reuse a complete local snapshot so interrupted runs resume quickly."""
    html_path, markdown_path, tables_path = local_paths(root, spec.url)
    if not all(path.exists() and path.stat().st_size > 0 for path in (
        html_path,
        markdown_path,
        tables_path,
    )):
        return None
    try:
        lines = markdown_path.read_text(encoding="utf-8").splitlines()
        title = lines[0].removeprefix("# ").strip() if lines else spec.url
        actual_prefix = "- 实际下载地址："
        final_url = next(
            (
                line[len(actual_prefix):].strip()
                for line in lines[:12]
                if line.startswith(actual_prefix)
            ),
            spec.url,
        )
    except OSError:
        return None
    return DocumentRecord(
        category=spec.category,
        title=title,
        official_url=spec.url,
        final_url=final_url,
        html_path=relative_posix(html_path, root),
        markdown_path=relative_posix(markdown_path, root),
        tables_path=relative_posix(tables_path, root),
        purpose=spec.purpose,
        relation=spec.relation,
        status="ok",
    )


def write_index(root: Path, records: list[DocumentRecord]) -> None:
    lines = [
        "# OriginPro论文绘图与格式化补充索引",
        "",
        "- 资料来源：仅OriginLab官方文档。",
        "- 作用：补充现有originpro API、Python示例和LabTalk坐标轴资料。",
        "- 推荐：先用originpro高级API；复杂格式优先固化到OTP/OTPU模板；",
        "  只有API和模板不足时才使用经官方文档或本机验证确认的LabTalk。",
        "",
    ]
    categories: list[str] = []
    for record in records:
        if record.category not in categories:
            categories.append(record.category)
    for category in categories:
        lines.extend([f"## {category}", ""])
        for record in (item for item in records if item.category == category):
            status = "ok" if record.status == "ok" else f"error: {record.error}"
            title = record.title or record.official_url
            lines.extend(
                [
                    f"### {title}",
                    "",
                    f"- 本地Markdown：`{record.markdown_path or '未生成'}`",
                    f"- 原始HTML：`{record.html_path or '未生成'}`",
                    f"- 表格JSON：`{record.tables_path or '未生成'}`",
                    f"- 官方URL：{record.official_url}",
                    f"- 用途：{record.purpose}",
                    f"- 与originpro的关系：{record.relation}",
                    f"- 下载状态：{status}",
                    "",
                ]
            )
    (root / "INDEX_PUBLICATION_GRAPHING.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def write_manifest(
    root: Path,
    kb_root: Path,
    records: list[DocumentRecord],
    duplicate_audit: list[dict],
) -> None:
    counts = Counter(record.status for record in records)
    categories = Counter(record.category for record in records)
    manifest = {
        "download_time": datetime.now(timezone.utc).isoformat(),
        "origin_version_target": "current online Origin Help; local OriginPro 2024b",
        "scope": (
            "Curated OriginLab publication graphing and formatting supplement; "
            "not a full Origin Help mirror."
        ),
        "kb_root": str(kb_root),
        "document_count": len(records),
        "status_counts": dict(counts),
        "category_counts": dict(categories),
        "documents": [asdict(record) for record in records],
        "duplicate_audit": duplicate_audit,
        "notes": [
            "All target URLs are on docs.originlab.com.",
            "Existing originpro/Python and LabTalk-axis pages are not re-downloaded.",
            "GUI documentation explains semantics; it does not by itself prove a LabTalk property.",
            "Version-dependent commands must still be checked against the local API or verified scripts.",
        ],
    }
    (root / "manifest_publication_graphing.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "03_EXTRACTED_REFERENCE" / "DUPLICATE_AUDIT.json").write_text(
        json.dumps(duplicate_audit, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_topic_map(root: Path, records: list[DocumentRecord]) -> None:
    topic_map: dict[str, list[dict]] = {}
    for record in records:
        topic_map.setdefault(record.category, []).append(
            {
                "title": record.title,
                "markdown_path": record.markdown_path,
                "official_url": record.official_url,
                "purpose": record.purpose,
                "relation": record.relation,
                "status": record.status,
            }
        )
    output = root / "03_EXTRACTED_REFERENCE" / "TOPIC_MAP.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(topic_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="下载OriginLab官方论文绘图、格式化和导出补充资料。"
    )
    parser.add_argument(
        "--kb-root",
        default=str(Path.cwd() / "OriginPro_Codex_KB"),
        help="现有OriginPro知识库根目录。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kb_root = Path(args.kb_root).expanduser().resolve()
    supplement_root = kb_root / SUPPLEMENT_DIRNAME
    supplement_root.mkdir(parents=True, exist_ok=True)
    (supplement_root / "03_EXTRACTED_REFERENCE").mkdir(parents=True, exist_ok=True)

    existing = load_existing_urls(kb_root)
    duplicate_audit = []
    for spec in DOCUMENTS:
        matches = existing.get(normalized_url(spec.url), [])
        duplicate_audit.append(
            {
                "official_url": spec.url,
                "already_in_existing_manifests": bool(matches),
                "existing_manifest_paths": sorted(set(matches)),
                "action": "download" if not matches else "reviewed_then_download",
            }
        )

    records: list[DocumentRecord] = []
    total = len(DOCUMENTS)
    for index, spec in enumerate(DOCUMENTS, start=1):
        record = record_from_existing(supplement_root, spec)
        was_cached = record is not None
        if was_cached:
            print(f"{index:>2}/{total} [cached] {spec.url}", flush=True)
        else:
            print(
                f"{index:>2}/{total} [{spec.category}] {spec.url}",
                flush=True,
            )
            record = download_with_retry(supplement_root, spec)
        records.append(record)
        if record.status != "ok":
            print(f"    ERROR: {record.error}", flush=True)
        if not was_cached:
            time.sleep(REQUEST_DELAY_SECONDS)

    write_index(supplement_root, records)
    write_manifest(supplement_root, kb_root, records, duplicate_audit)
    write_topic_map(supplement_root, records)
    ok = sum(record.status == "ok" for record in records)
    errors = len(records) - ok
    print(f"完成：目标 {total}，成功 {ok}，失败 {errors}")
    print(supplement_root)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
