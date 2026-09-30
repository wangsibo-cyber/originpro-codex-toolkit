#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download and index the official OriginLab LabTalk axis reference supplement."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup, NavigableString, Tag


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/150 Safari/537.36 "
    "OriginPro-Codex-LabTalk-Axis-Supplement/1.0"
)
DEFAULT_TIMEOUT = 60
REQUEST_DELAY_SECONDS = 0.25


@dataclass(frozen=True)
class DocumentSpec:
    category: str
    url: str
    purpose: str
    relation: str


@dataclass
class DocumentRecord:
    category: str
    title: str
    official_url: str
    final_url: str
    html_path: str
    markdown_path: str
    tables_path: str
    purpose: str
    relation: str
    status: str
    error: str = ""


DOCUMENTS = [
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/",
        "LabTalk语言参考总入口。",
        "确定对象、命令、函数和系统变量的官方检索入口。",
    ),
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/command-reference/",
        "LabTalk命令参考目录。",
        "查找可通过op.lt_exec()执行的命令。",
    ),
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/object-reference/",
        "LabTalk对象模型说明。",
        "理解Layer、Axis、Label和System对象的属性访问方式。",
    ),
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/alphabetical-listing-of-commands/",
        "LabTalk命令字母索引。",
        "定位轴控制相关命令。",
    ),
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/alphabetical-listing-of-objs/",
        "LabTalk对象字母索引。",
        "定位Layer.Axis及其下级对象。",
    ),
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/system-vars/",
        "系统变量概念和轴范围快捷变量。",
        "说明X1/X2/X3、Y1/Y2/Y3等会话变量。",
    ),
    DocumentSpec(
        "LabTalk总参考",
        "https://docs.originlab.com/labtalk/ref/sys-var-list/",
        "完整系统变量表。",
        "核实@TLC、@TKP、@TKS、@ETE、@SSS、@LUQ等全局设置。",
    ),
    DocumentSpec(
        "Axis命令",
        "https://docs.originlab.com/labtalk/ref/axis-cmd/",
        "axis命令语法、读写选项和示例。",
        "用于op.lt_exec()中的轴对话框访问和部分轴参数设置。",
    ),
    DocumentSpec(
        "Layer对象",
        "https://docs.originlab.com/labtalk/ref/layer-obj/",
        "Layer对象属性。",
        "核实layer.tickstyle、tickL、tickW、sauto及图层定位。",
    ),
    DocumentSpec(
        "Layer.Axis对象",
        "https://docs.originlab.com/labtalk/ref/layer-axis-obj/",
        "单轴范围、刻度、线条、显示和标签入口。",
        "复杂坐标轴格式的首要LabTalk对象参考。",
    ),
    DocumentSpec(
        "Layer.Axis.Label对象",
        "https://docs.originlab.com/labtalk/ref/layer-axis-label-obj/",
        "单轴刻度标签字体、格式、旋转、前后缀等属性。",
        "补充originpro高级API未覆盖的刻度标签格式。",
    ),
    DocumentSpec(
        "Layer.Axis对象",
        "https://docs.originlab.com/labtalk/ref/layer-axis-grid-obj/",
        "轴网格线对象。",
        "核实主次网格线显示和样式。",
    ),
    DocumentSpec(
        "Layer.Axis对象",
        "https://docs.originlab.com/labtalk/ref/layer-axis-arrow-obj/",
        "轴箭头对象。",
        "核实轴起点、终点箭头设置。",
    ),
    DocumentSpec(
        "Layer.Axis对象",
        "https://docs.originlab.com/labtalk/ref/layer-axis-break-obj/",
        "单个轴断点对象。",
        "核实轴断点的范围和样式属性。",
    ),
    DocumentSpec(
        "Layer.Axis对象",
        "https://docs.originlab.com/labtalk/ref/layer-axis-breaks-obj/",
        "多轴断点集合对象。",
        "核实轴断点数量和集合访问。",
    ),
    DocumentSpec(
        "System.Axis和System.Tick",
        "https://docs.originlab.com/labtalk/ref/system-axis-obj/",
        "全局轴默认设置。",
        "区分单图轴设置与Origin全局默认设置。",
    ),
    DocumentSpec(
        "System.Axis和System.Tick",
        "https://docs.originlab.com/labtalk/ref/system-tick-obj/",
        "全局刻度与刻度标签默认设置。",
        "核实全局刻度长度、最大刻度数和科学计数显示。",
    ),
    DocumentSpec(
        "Axis Title",
        "https://docs.originlab.com/labtalk/ref/label-cmd/",
        "Label命令及轴标题快捷选项。",
        "核实通过LabTalk创建和修改轴标题文本的命令语法。",
    ),
    DocumentSpec(
        "Axis Title",
        "https://docs.originlab.com/labtalk/guide/creating-and-accessing-graphical-objs/",
        "图形文本和图例对象脚本示例。",
        "轴标题本质为图形文本对象，属性写法可复用。",
    ),
    DocumentSpec(
        "坐标轴总览",
        "https://docs.originlab.com/origin-help/graphaxes/",
        "Origin图形坐标轴帮助入口。",
        "将GUI选项与LabTalk对象属性相互核对。",
    ),
    DocumentSpec(
        "坐标轴总览",
        "https://docs.originlab.com/origin-help/axes-ref/",
        "Axis对话框参考总入口。",
        "定位一般和特殊图形的各轴设置页。",
    ),
    DocumentSpec(
        "坐标轴总览",
        "https://docs.originlab.com/origin-help/general-axis-dialog/",
        "一般2D/3D图的Axis对话框结构。",
        "说明上下左右轴、3D轴和多图层的设置范围。",
    ),
    DocumentSpec(
        "坐标轴总览",
        "https://docs.originlab.com/origin-help/show-tab-in-axis-dialog/",
        "Axis对话框Show页。",
        "核实上下左右轴显示和左右Y轴独立缩放。",
    ),
    DocumentSpec(
        "Scale设置",
        "https://docs.originlab.com/origin-help/axis-displayrange-control/",
        "轴范围、自动缩放和固定范围。",
        "解释From、To和Rescale模式的实际行为。",
    ),
    DocumentSpec(
        "Scale设置",
        "https://docs.originlab.com/origin-help/axesref-scale/",
        "一般图形的Scale页。",
        "区分By Increment、By Counts、By Custom Positions和Anchor Tick。",
    ),
    DocumentSpec(
        "Tick Labels",
        "https://docs.originlab.com/origin-help/axesref-ticklabels/",
        "刻度标签类型、格式和显示选项。",
        "核实小数、科学计数、工程计数、公式和前后缀。",
    ),
    DocumentSpec(
        "Axis Title",
        "https://docs.originlab.com/origin-help/axesref-title/",
        "轴标题文本、字体、字号、旋转和位置。",
        "核实轴标题GUI行为和模板替换字符串。",
    ),
    DocumentSpec(
        "Line and Ticks",
        "https://docs.originlab.com/origin-help/axesref-lineticks/",
        "轴线及主次刻度方向、长度、颜色和粗细。",
        "解释LabTalk位掩码属性对应的视觉含义。",
    ),
    DocumentSpec(
        "特殊刻度",
        "https://docs.originlab.com/origin-help/axesref-specialticks/",
        "轴起点、终点和任意位置的特殊刻度。",
        "研究强制端点刻度及其标签的GUI保障方式。",
    ),
    DocumentSpec(
        "System.Axis和System.Tick",
        "https://docs.originlab.com/origin-help/options-dialog-axis-tab/",
        "Origin全局Options Axis页。",
        "核实最大刻度数、尾随零、科学计数和轴标题单位全局规则。",
    ),
    DocumentSpec(
        "特殊图形和First Tick",
        "https://docs.originlab.com/origin-help/axesdialog-scale-tab/",
        "特殊图形的Scale页。",
        "核实Increment、Major/Minor Ticks、First Tick和按数据集设刻度。",
    ),
    DocumentSpec(
        "特殊图形和First Tick",
        "https://docs.originlab.com/origin-help/axesdialog-titleformat-tab/",
        "特殊图形的Title and Format页。",
        "核实特殊图形轴标题、轴线和主次刻度格式。",
    ),
]


UNRESOLVED_QUESTIONS = [
    "Layer.Axis对象页没有明确说明ticklength、mticklength、tickthickness和"
    "mtickthickness的单位；GUI Line and Ticks页以pt显示，但对象属性单位需本机验证。",
    "一般图形GUI称Anchor Tick，特殊图形GUI称First Tick；在线对象页只公开"
    "layer.axis.firstTick，官方页面未明确声明两个GUI字段是否在所有图型中完全等价。",
    "Layer.Axis.majorTicks和GUI By Counts都可能被Origin调整，不能当作严格刻度数量保证。",
    "Special Ticks页能在GUI强制显示Axis Begin/Axis End，但未在本批对象参考中找到"
    "稳定的单轴LabTalk属性用于直接写入该Show状态。",
]


VERSION_SPECIFIC_PROPERTIES = [
    {
        "property": "layer.axis.label.pt",
        "introduced": "Origin 2024b",
        "target_status": "本机OriginPro 2024b可用，仍需运行验证。",
    },
    {
        "property": "layer.axis.IndivScale",
        "introduced": "Origin 2023",
        "target_status": "本机OriginPro 2024b可用。",
    },
    {
        "property": "layer.axis.link",
        "introduced": "Origin 2023b",
        "target_status": "本机OriginPro 2024b可用；不支持3D。",
    },
    {
        "property": "layer.axis.label.scientificnotation*",
        "introduced": "Origin 2022b",
        "target_status": "本机OriginPro 2024b可用。",
    },
]


def request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )


def fetch(url: str) -> tuple[bytes, str, str]:
    with urllib.request.urlopen(request(url), timeout=DEFAULT_TIMEOUT) as response:
        return (
            response.read(),
            response.geturl(),
            response.headers.get_content_charset() or "utf-8",
        )


def decode(body: bytes, charset: str) -> str:
    for encoding in (charset, "utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


def safe_component(value: str) -> str:
    value = urllib.parse.unquote(value)
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value) or "_"


def local_paths(root: Path, url: str) -> tuple[Path, Path, Path]:
    parsed = urllib.parse.urlsplit(url)
    parts = [safe_component(part) for part in parsed.path.strip("/").split("/") if part]
    if not parts or parsed.path.endswith("/"):
        parts.append("index")
    elif "." in parts[-1]:
        parts[-1] = parts[-1].rsplit(".", 1)[0]
    host = safe_component(parsed.netloc.lower())
    relative = Path(host, *parts)
    return (
        root / "01_HTML" / relative.with_suffix(".html"),
        root / "02_MARKDOWN" / relative.with_suffix(".md"),
        root / "03_EXTRACTED_REFERENCE" / "tables" / relative.with_suffix(".tables.json"),
    )


def clean_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s*\n\s*\n+", "\n\n", value)
    return value.strip()


def inline_markdown(node: Tag | NavigableString, base_url: str) -> str:
    if isinstance(node, NavigableString):
        return re.sub(r"\s+", " ", str(node))
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if name == "br":
        return "<br>"
    if name == "code":
        code_text = clean_text(node.get_text(" ", strip=True)).replace("`", "\\`")
        return f"`{code_text}`"
    if name == "a":
        text = clean_text("".join(inline_markdown(child, base_url) for child in node.children))
        href = node.get("href", "")
        if text and href:
            return f"[{text}]({urllib.parse.urljoin(base_url, href)})"
        return text
    if name in {"strong", "b"}:
        text = clean_text("".join(inline_markdown(child, base_url) for child in node.children))
        return f"**{text}**" if text else ""
    if name in {"em", "i"}:
        text = clean_text("".join(inline_markdown(child, base_url) for child in node.children))
        return f"*{text}*" if text else ""
    if name == "img":
        alt = clean_text(node.get("alt", ""))
        src = node.get("src", "")
        return f"![{alt}]({urllib.parse.urljoin(base_url, src)})" if src else alt
    return "".join(inline_markdown(child, base_url) for child in node.children)


def table_data(table: Tag) -> dict:
    rows = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["th", "td"], recursive=False):
            text = clean_text(cell.get_text(" ", strip=True))
            cells.append(text)
        if cells:
            rows.append(cells)
    if not rows:
        return {"headers": [], "rows": []}
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    first_has_th = bool(table.find("tr") and table.find("tr").find("th"))
    headers = rows[0] if first_has_th else [f"Column {i + 1}" for i in range(width)]
    body = rows[1:] if first_has_th else rows
    return {"headers": headers, "rows": body}


def table_markdown(table: Tag) -> str:
    data = table_data(table)
    headers = data["headers"]
    if not headers:
        return ""

    def escape(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(escape(cell) for cell in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in data["rows"]:
        lines.append("| " + " | ".join(escape(cell) for cell in row) + " |")
    return "\n".join(lines)


def block_markdown(node: Tag | NavigableString, base_url: str) -> str:
    if isinstance(node, NavigableString):
        return clean_text(str(node))
    if not isinstance(node, Tag):
        return ""
    name = node.name.lower()
    if re.fullmatch(r"h[1-6]", name):
        level = int(name[1])
        return f"{'#' * level} {clean_text(inline_markdown(node, base_url))}"
    if name == "p":
        return clean_text(inline_markdown(node, base_url))
    if name == "pre":
        code = node.get_text("\n", strip=False).strip("\n")
        return f"```labtalk\n{code}\n```"
    if name == "table":
        return table_markdown(node)
    if name in {"ul", "ol"}:
        lines = []
        ordered = name == "ol"
        for index, li in enumerate(node.find_all("li", recursive=False), start=1):
            text = clean_text(inline_markdown(li, base_url))
            if text:
                lines.append(f"{index}. {text}" if ordered else f"- {text}")
        return "\n".join(lines)
    if name == "blockquote":
        text = clean_text(inline_markdown(node, base_url))
        return "\n".join(f"> {line}" for line in text.splitlines())
    if name == "hr":
        return "---"
    if name in {"script", "style", "noscript", "svg", "nav", "header", "footer", "form"}:
        return ""
    blocks = []
    for child in node.children:
        converted = block_markdown(child, base_url)
        if converted:
            blocks.append(converted)
    return "\n\n".join(blocks)


def html_to_markdown(html_text: str, final_url: str) -> tuple[str, str, list[dict]]:
    soup = BeautifulSoup(html_text, "lxml")
    for selector in (
        "script",
        "style",
        "noscript",
        "svg",
        "nav",
        "header",
        "footer",
        "form",
        ".mw-editsection",
        ".printfooter",
    ):
        for element in soup.select(selector):
            element.decompose()

    title_tag = soup.find("h1") or soup.find("title")
    title = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else final_url
    content = (
        soup.select_one("#mw-content-text")
        or soup.select_one(".mw-parser-output")
        or soup.find("main")
        or soup.find("article")
        or soup.body
        or soup
    )
    tables = [table_data(table) for table in content.find_all("table")]
    markdown = block_markdown(content, final_url)
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
    return title, markdown, tables


def relative_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def write_document(root: Path, spec: DocumentSpec) -> DocumentRecord:
    html_path, markdown_path, tables_path = local_paths(root, spec.url)
    retrieved = datetime.now(timezone.utc).isoformat()
    try:
        body, final_url, charset = fetch(spec.url)
        html_text = decode(body, charset)
        title, markdown_body, tables = html_to_markdown(html_text, final_url)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        tables_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html_text, encoding="utf-8")
        markdown_header = (
            f"# {title}\n\n"
            f"- 官方来源：{spec.url}\n"
            f"- 实际下载地址：{final_url}\n"
            f"- 下载时间：{retrieved}\n"
            f"- 文档用途：{spec.purpose}\n"
            f"- 与originpro的关系：{spec.relation}\n"
            f"- 分类：{spec.category}\n\n"
            "---\n\n"
        )
        markdown_path.write_text(markdown_header + markdown_body + "\n", encoding="utf-8")
        tables_path.write_text(
            json.dumps(
                {
                    "title": title,
                    "official_url": spec.url,
                    "final_url": final_url,
                    "tables": tables,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
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
    except Exception as exc:
        return DocumentRecord(
            category=spec.category,
            title="",
            official_url=spec.url,
            final_url="",
            html_path="",
            markdown_path="",
            tables_path="",
            purpose=spec.purpose,
            relation=spec.relation,
            status="error",
            error=f"{type(exc).__name__}: {exc}",
        )


def write_index(root: Path, records: Iterable[DocumentRecord]) -> None:
    records = list(records)
    lines = [
        "# OriginPro LabTalk坐标轴补充索引",
        "",
        "- 目标版本：OriginPro 2024b",
        "- 资料来源：仅OriginLab官方站点",
        "- 使用顺序：优先originpro高级API；仅在API不足时使用经核实的LabTalk属性。",
        "",
    ]
    categories = []
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
                    f"- 官方URL：{record.official_url}",
                    f"- 用途：{record.purpose}",
                    f"- 下载状态：{status}",
                    "",
                ]
            )

    lines.extend(
        [
            "## 代码示例",
            "",
            "- `04_CODE_EXAMPLES/test_axis_range.py`：轴范围与固定缩放。",
            "- `04_CODE_EXAMPLES/test_axis_ticks_direction.py`：主次刻度方向与位掩码。",
            "- `04_CODE_EXAMPLES/test_axis_endpoint_ticks.py`：端点刻度和自定义位置。",
            "- `04_CODE_EXAMPLES/test_axis_tick_labels.py`：刻度标签字体与数字格式。",
            "- `04_CODE_EXAMPLES/test_axis_title.py`：轴标题内容与字体。",
            "- `04_CODE_EXAMPLES/verify_axis_properties.py`：读取并核对关键属性。",
            "- `04_CODE_EXAMPLES/MANUAL_VISUAL_CHECKLIST.md`：人工视觉验收清单。",
            "",
        ]
    )
    (root / "INDEX_LABTALK_AXIS.md").write_text("\n".join(lines), encoding="utf-8")


def write_manifest(root: Path, records: Iterable[DocumentRecord]) -> None:
    records = list(records)
    manifest = {
        "download_time": datetime.now(timezone.utc).isoformat(),
        "origin_version_target": "OriginPro 2024b",
        "documents": [asdict(record) for record in records],
        "unresolved_questions": UNRESOLVED_QUESTIONS,
        "verified_properties": [],
        "version_specific_properties": VERSION_SPECIFIC_PROPERTIES,
    }
    (root / "manifest_labtalk_axis.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="下载OriginLab官方LabTalk坐标轴资料并生成本地补充知识库。"
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
    supplement_root = kb_root / "06_LABTALK_AXIS_SUPPLEMENT"
    supplement_root.mkdir(parents=True, exist_ok=True)
    records = []
    total = len(DOCUMENTS)
    for index, spec in enumerate(DOCUMENTS, start=1):
        print(f"{index:>2}/{total} {spec.url}")
        record = write_document(supplement_root, spec)
        records.append(record)
        if record.status != "ok":
            print(f"    ERROR: {record.error}")
        time.sleep(REQUEST_DELAY_SECONDS)
    write_index(supplement_root, records)
    write_manifest(supplement_root, records)
    ok = sum(record.status == "ok" for record in records)
    errors = len(records) - ok
    print(f"完成：成功 {ok}，失败 {errors}")
    print(supplement_root)
    return 0 if errors == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
