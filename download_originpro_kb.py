#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
OriginPro / originpro 官方资料离线下载器

功能：
1. 下载 OriginLab 官方 Python 文档，并保存原始 HTML。
2. 将文档转换为适合 Codex 检索的 Markdown。
3. 下载 OriginLab 官方 Python-Samples GitHub 仓库并解压。
4. 从 PyPI 下载当前 originpro wheel/sdist，便于 Codex 检查实际包源码。
5. 生成 INDEX.md、manifest.json 和最终 ZIP 知识库。

运行：
    py -3 download_originpro_kb.py
或：
    python download_originpro_kb.py

可选：
    python download_originpro_kb.py --output D:\KnowledgeBases\OriginPro_Codex_KB
    python download_originpro_kb.py --max-python 250 --max-external 120 --max-api 500
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Optional


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/150 Safari/537.36 "
    "OriginPro-Codex-KB-Downloader/1.0"
)

DEFAULT_TIMEOUT = 45
REQUEST_DELAY_SECONDS = 0.20

GITHUB_ZIP_URLS = [
    "https://github.com/originlab/Python-Samples/archive/refs/heads/main.zip",
    "https://codeload.github.com/originlab/Python-Samples/zip/refs/heads/main",
]

PYPI_JSON_URL = "https://pypi.org/pypi/originpro/json"


@dataclass
class PageRecord:
    collection: str
    title: str
    source_url: str
    html_file: str
    markdown_file: str
    status: str
    error: str = ""


class LinkAndTextParser(HTMLParser):
    """Extract links, page title and readable Markdown-like text."""

    BLOCK_START = {
        "p": "\n\n",
        "div": "\n",
        "section": "\n\n",
        "article": "\n\n",
        "header": "\n\n",
        "footer": "\n\n",
        "main": "\n\n",
        "nav": "\n",
        "br": "\n",
        "tr": "\n",
        "table": "\n\n",
        "blockquote": "\n\n> ",
        "hr": "\n\n---\n\n",
    }

    SKIP_TAGS = {"script", "style", "noscript", "svg"}

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[str] = []
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.in_title = False
        self.skip_depth = 0
        self.pre_depth = 0
        self.code_depth = 0
        self.list_stack: list[str] = []
        self.current_href: Optional[str] = None
        self.current_link_text: list[str] = []
        self.heading_level: Optional[int] = None

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        attrs_dict = dict(attrs)

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return

        if tag == "title":
            self.in_title = True
        elif re.fullmatch(r"h[1-6]", tag):
            self.heading_level = int(tag[1])
            self.parts.append("\n\n" + "#" * self.heading_level + " ")
        elif tag == "pre":
            self.pre_depth += 1
            self.parts.append("\n\n```text\n")
        elif tag == "code":
            self.code_depth += 1
            if not self.pre_depth:
                self.parts.append("`")
        elif tag in ("ul", "ol"):
            self.list_stack.append(tag)
            self.parts.append("\n")
        elif tag == "li":
            marker = "1. " if self.list_stack and self.list_stack[-1] == "ol" else "- "
            self.parts.append("\n" + "  " * max(0, len(self.list_stack) - 1) + marker)
        elif tag == "a":
            href = attrs_dict.get("href")
            if href:
                absolute = urllib.parse.urljoin(self.base_url, href)
                self.links.append(absolute)
                self.current_href = absolute
                self.current_link_text = []
        elif tag in self.BLOCK_START:
            self.parts.append(self.BLOCK_START[tag])

    def handle_endtag(self, tag: str):
        tag = tag.lower()

        if tag in self.SKIP_TAGS:
            if self.skip_depth:
                self.skip_depth -= 1
            return
        if self.skip_depth:
            return

        if tag == "title":
            self.in_title = False
        elif re.fullmatch(r"h[1-6]", tag):
            self.heading_level = None
            self.parts.append("\n")
        elif tag == "pre":
            if self.pre_depth:
                self.pre_depth -= 1
            self.parts.append("\n```\n\n")
        elif tag == "code":
            if self.code_depth:
                self.code_depth -= 1
            if not self.pre_depth:
                self.parts.append("`")
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.parts.append("\n")
        elif tag == "a" and self.current_href:
            text = "".join(self.current_link_text).strip()
            if text:
                self.parts.append(f" ({self.current_href})")
            self.current_href = None
            self.current_link_text = []

    def handle_data(self, data: str):
        if self.skip_depth:
            return

        if self.in_title:
            self.title_parts.append(data)

        if self.pre_depth:
            cleaned = data.replace("\r\n", "\n").replace("\r", "\n")
        else:
            cleaned = re.sub(r"[ \t\f\v]+", " ", data)
            cleaned = re.sub(r"\n+", " ", cleaned)

        if cleaned:
            self.parts.append(cleaned)
            if self.current_href is not None:
                self.current_link_text.append(cleaned)

    @property
    def title(self) -> str:
        value = " ".join(self.title_parts)
        return re.sub(r"\s+", " ", value).strip()

    @property
    def markdown(self) -> str:
        value = "".join(self.parts)
        value = html.unescape(value)
        value = re.sub(r"[ \t]+\n", "\n", value)
        value = re.sub(r"\n[ \t]+", "\n", value)
        value = re.sub(r"\n{4,}", "\n\n\n", value)
        value = re.sub(r" {2,}", " ", value)
        return value.strip() + "\n"


def make_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json,application/zip,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        },
    )


def fetch_bytes(url: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[bytes, str, str]:
    """Return bytes, final URL and content type."""
    req = make_request(url)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read()
        final_url = response.geturl()
        ctype = response.headers.get_content_type()
        return body, final_url, ctype


def decode_html(body: bytes, content_type: str = "") -> str:
    # OriginLab currently serves UTF-8. These fallbacks make the downloader safer.
    for encoding in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def safe_url(url: str) -> str:
    """Normalize URL for crawl de-duplication."""
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme.lower()
    host = parsed.netloc.lower()

    # Consolidate historical OriginLab API links onto the current docs host.
    if host in {"www.originlab.com", "originlab.com"} and parsed.path.startswith(
        "/python/doc/originpro/"
    ):
        host = "docs.originlab.com"
        path = parsed.path.replace("/python/doc/originpro/", "/originpro/", 1)
    else:
        path = parsed.path

    path = re.sub(r"/+", "/", path)
    if not path:
        path = "/"
    if path.lower().endswith(("/index.html", "/index.htm")):
        path = path[: path.rfind("/") + 1]

    # Fragments are never needed for fetching. Most query strings are UI state.
    return urllib.parse.urlunsplit((scheme, host, path, "", ""))


def is_document_url(url: str, host: str, path_prefix: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc.lower() != host.lower():
        return False
    if not parsed.path.startswith(path_prefix):
        return False

    excluded = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
        ".css", ".js", ".map", ".xml", ".json", ".pdf", ".zip",
        ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm",
    )
    if parsed.path.lower().endswith(excluded):
        return False

    # Keep Doxygen and documentation pages only.
    ext = Path(parsed.path).suffix.lower()
    return ext in {"", ".html", ".htm"} or parsed.path.endswith("/")


def url_to_relative_path(url: str, suffix: str) -> Path:
    parsed = urllib.parse.urlsplit(url)
    path = parsed.path
    if path.endswith("/"):
        path += "index"
    else:
        path = path.rsplit(".", 1)[0] if "." in Path(path).name else path

    cleaned_parts = []
    for part in Path(path.lstrip("/")).parts:
        part = urllib.parse.unquote(part)
        part = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", part)
        cleaned_parts.append(part or "_")

    if not cleaned_parts:
        cleaned_parts = ["index"]

    return Path(parsed.netloc, *cleaned_parts).with_suffix(suffix)


def write_page(
    output_root: Path,
    collection: str,
    source_url: str,
    final_url: str,
    body: bytes,
    content_type: str,
) -> tuple[str, str, str]:
    text = decode_html(body, content_type)
    parser = LinkAndTextParser(final_url)
    parser.feed(text)
    title = parser.title or Path(urllib.parse.urlsplit(final_url).path).name or final_url

    html_rel = Path("01_HTML") / url_to_relative_path(final_url, ".html")
    md_rel = Path("02_MARKDOWN") / url_to_relative_path(final_url, ".md")

    html_path = output_root / html_rel
    md_path = output_root / md_rel
    html_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    html_path.write_text(text, encoding="utf-8")

    header = (
        f"# {title}\n\n"
        f"- Collection: `{collection}`\n"
        f"- Source: {source_url}\n"
        f"- Final URL: {final_url}\n"
        f"- Retrieved: {datetime.now(timezone.utc).isoformat()}\n\n"
        "---\n\n"
    )
    md_path.write_text(header + parser.markdown, encoding="utf-8")

    return title, html_rel.as_posix(), md_rel.as_posix()


def crawl_collection(
    output_root: Path,
    collection: str,
    seeds: Iterable[str],
    allowed_host: str,
    allowed_prefix: str,
    max_pages: int,
    workers: int,
) -> list[PageRecord]:
    queue = deque(safe_url(seed) for seed in seeds)
    seen: set[str] = set()
    records: list[PageRecord] = []

    print(
        f"\n[{collection}] 最多下载 {max_pages} 页，"
        f"{workers} 路并发，自动复用已下载页面"
    )

    def fetch_or_reuse(url: str) -> tuple[PageRecord, list[str], bool]:
        html_rel = Path("01_HTML") / url_to_relative_path(url, ".html")
        md_rel = Path("02_MARKDOWN") / url_to_relative_path(url, ".md")
        html_path = output_root / html_rel
        md_path = output_root / md_rel

        try:
            if html_path.is_file() and md_path.is_file():
                text = html_path.read_text(encoding="utf-8")
                parser = LinkAndTextParser(url)
                parser.feed(text)
                record = PageRecord(
                    collection=collection,
                    title=parser.title or Path(urllib.parse.urlsplit(url).path).name or url,
                    source_url=url,
                    html_file=html_rel.as_posix(),
                    markdown_file=md_rel.as_posix(),
                    status="ok",
                )
                return record, parser.links, True

            body, final_url, ctype = fetch_bytes(url)
            final_url = safe_url(final_url)

            if "html" not in ctype and not final_url.lower().endswith((".html", ".htm", "/")):
                raise ValueError(f"非HTML内容：{ctype}")

            title, saved_html_rel, saved_md_rel = write_page(
                output_root, collection, url, final_url, body, ctype
            )
            parser = LinkAndTextParser(final_url)
            parser.feed(decode_html(body, ctype))
            record = PageRecord(
                collection=collection,
                title=title,
                source_url=url,
                html_file=saved_html_rel,
                markdown_file=saved_md_rel,
                status="ok",
            )
            time.sleep(REQUEST_DELAY_SECONDS)
            return record, parser.links, False
        except Exception as exc:
            record = PageRecord(
                collection=collection,
                title="",
                source_url=url,
                html_file="",
                markdown_file="",
                status="error",
                error=f"{type(exc).__name__}: {exc}",
            )
            return record, [], False

    with ThreadPoolExecutor(max_workers=workers) as executor:
        while queue and len(seen) < max_pages:
            batch: list[str] = []
            while queue and len(seen) + len(batch) < max_pages and len(batch) < workers:
                url = safe_url(queue.popleft())
                if url in seen or url in batch:
                    continue
                if not is_document_url(url, allowed_host, allowed_prefix):
                    continue
                batch.append(url)

            if not batch:
                continue

            for url in batch:
                seen.add(url)
                print(f"  {len(seen):>4}/{max_pages}: {url}")

            results = list(executor.map(fetch_or_reuse, batch))
            for record, links, reused in results:
                records.append(record)
                if record.status != "ok":
                    print(f"      ERROR: {record.source_url}: {record.error}")
                    continue
                if reused:
                    print(f"      CACHED: {record.source_url}")
                for link in links:
                    normalized = safe_url(link)
                    if (
                        normalized not in seen
                        and is_document_url(normalized, allowed_host, allowed_prefix)
                    ):
                        queue.append(normalized)

    return records


def download_file(urls: Iterable[str], dest: Path) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    errors = []

    for url in urls:
        try:
            print(f"下载：{url}")
            body, final_url, _ = fetch_bytes(url, timeout=120)
            dest.write_bytes(body)
            return final_url
        except Exception as exc:
            errors.append(f"{url} -> {type(exc).__name__}: {exc}")

    raise RuntimeError("所有下载地址均失败：\n" + "\n".join(errors))


def safe_extract_zip(archive_path: Path, destination: Path) -> None:
    """Extract a ZIP only when every member stays inside destination."""
    destination_root = destination.resolve()
    with zipfile.ZipFile(archive_path) as zf:
        for member in zf.infolist():
            member_path = (destination / member.filename).resolve()
            try:
                member_path.relative_to(destination_root)
            except ValueError as exc:
                raise ValueError(f"ZIP包含不安全路径：{member.filename}") from exc
        zf.extractall(destination)


def download_and_extract_samples(output_root: Path) -> dict:
    archive_dir = output_root / "03_OFFICIAL_CODE_ARCHIVES"
    archive_path = archive_dir / "Python-Samples-main.zip"
    extracted_root = output_root / "04_OFFICIAL_PYTHON_SAMPLES"

    final_url = download_file(GITHUB_ZIP_URLS, archive_path)

    if extracted_root.exists():
        shutil.rmtree(extracted_root)
    extracted_root.mkdir(parents=True, exist_ok=True)

    safe_extract_zip(archive_path, extracted_root)

    return {
        "status": "ok",
        "source": final_url,
        "archive": archive_path.relative_to(output_root).as_posix(),
        "extracted_to": extracted_root.relative_to(output_root).as_posix(),
    }


def download_originpro_package(output_root: Path) -> dict:
    package_dir = output_root / "05_ORIGINPRO_PYPI_PACKAGE"
    package_dir.mkdir(parents=True, exist_ok=True)

    body, final_url, ctype = fetch_bytes(PYPI_JSON_URL)
    metadata = json.loads(body.decode("utf-8"))
    version = metadata["info"]["version"]
    files = metadata.get("urls", [])

    # Prefer a universal wheel, then any wheel, then source archive.
    def priority(item):
        name = item.get("filename", "")
        packagetype = item.get("packagetype", "")
        if packagetype == "bdist_wheel" and "py3-none-any" in name:
            return 0
        if packagetype == "bdist_wheel":
            return 1
        if packagetype == "sdist":
            return 2
        return 99

    chosen = sorted(files, key=priority)
    downloaded = []

    for item in chosen:
        if priority(item) > 2:
            continue
        url = item["url"]
        filename = item["filename"]
        dest = package_dir / filename
        file_final_url = download_file([url], dest)
        expected_sha256 = item.get("digests", {}).get("sha256", "")
        actual_sha256 = hashlib.sha256(dest.read_bytes()).hexdigest()
        if expected_sha256 and actual_sha256 != expected_sha256:
            dest.unlink(missing_ok=True)
            raise ValueError(f"SHA256校验失败：{filename}")
        downloaded.append(
            {
                "filename": filename,
                "packagetype": item.get("packagetype", ""),
                "source": file_final_url,
                "sha256": expected_sha256,
                "sha256_verified": bool(expected_sha256),
            }
        )
        # One wheel plus one sdist is sufficient.
        if (
            any(x["packagetype"] == "bdist_wheel" for x in downloaded)
            and any(x["packagetype"] == "sdist" for x in downloaded)
        ):
            break

    (package_dir / "PYPI_METADATA.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    extracted_wheels = []
    for item in downloaded:
        if item["packagetype"] != "bdist_wheel":
            continue
        wheel_path = package_dir / item["filename"]
        extracted_dir = package_dir / f"{wheel_path.stem}_EXTRACTED"
        if extracted_dir.exists():
            shutil.rmtree(extracted_dir)
        extracted_dir.mkdir(parents=True, exist_ok=True)
        safe_extract_zip(wheel_path, extracted_dir)
        extracted_wheels.append(extracted_dir.relative_to(output_root).as_posix())

    return {
        "status": "ok",
        "version": version,
        "metadata_source": final_url,
        "downloaded": downloaded,
        "extracted_wheels": extracted_wheels,
    }


def create_start_here(output_root: Path) -> None:
    content = """# OriginPro / originpro Codex 本地知识库

## 推荐检索顺序

1. `00_START_HERE.md`
2. `02_MARKDOWN/docs.originlab.com/externalpython/`
3. `02_MARKDOWN/docs.originlab.com/python/examples/graphing/`
4. `02_MARKDOWN/docs.originlab.com/originpro/annotated.md`
5. `04_OFFICIAL_PYTHON_SAMPLES/`
6. `05_ORIGINPRO_PYPI_PACKAGE/`

## Codex使用原则

- 本项目采用 **外部 Python + `originpro`** 驱动 OriginPro。
- 优先使用 `originpro` 高级API，不要默认改用旧版 `PyOrigin` 或底层 `OriginExt`。
- 写代码前，先在本地API文档中核对类、方法名、参数和返回值；不要猜测API。
- 外部Python调试阶段保持Origin窗口可见。
- 用 `try/finally` 或异常钩子确保 `op.exit()` 被调用，避免残留Origin进程。
- 绘图优先使用自定义 `.otp/.otpu` 模板，以保证论文图件风格统一。
- API无法完成的格式设置，可以在核对官方示例后使用 `op.lt_exec()` 调用LabTalk。
- 所有最终脚本应明确：
  - 数据输入路径；
  - Origin模板路径；
  - 图层、曲线、坐标轴和图例设置；
  - 输出图片格式、尺寸和DPI；
  - `.opju`工程保存路径；
  - 异常退出与Origin进程清理。

## 建议给Codex的固定指令

> 在编写或修改OriginPro绘图代码前，先检索当前目录中的OriginLab官方离线资料。项目采用外部Python调用`originpro`。不得凭记忆虚构API；类、方法、属性和参数必须能在`02_MARKDOWN/docs.originlab.com/originpro/`或官方示例代码中找到依据。优先复用`04_OFFICIAL_PYTHON_SAMPLES/`中的写法。开发阶段显示Origin窗口，并确保异常情况下也执行`op.exit()`。复杂格式设置只有在高级API不足时才使用`op.lt_exec()`。

## 目录说明

- `01_HTML`：官方网页原始HTML快照。
- `02_MARKDOWN`：由网页转换的Codex友好文本。
- `03_OFFICIAL_CODE_ARCHIVES`：官方代码仓库压缩包。
- `04_OFFICIAL_PYTHON_SAMPLES`：官方示例代码解压目录。
- `05_ORIGINPRO_PYPI_PACKAGE`：PyPI发布包和元数据。
- `INDEX.md`：全部文档索引及来源网址。
- `manifest.json`：下载状态、时间、错误记录。
"""
    (output_root / "00_START_HERE.md").write_text(content, encoding="utf-8")


def create_index(output_root: Path, records: list[PageRecord], metadata: dict) -> None:
    ok = [r for r in records if r.status == "ok"]
    errors = [r for r in records if r.status != "ok"]

    lines = [
        "# OriginPro Codex知识库索引",
        "",
        f"- 生成时间（UTC）：{metadata['created_utc']}",
        f"- 成功保存网页：{len(ok)}",
        f"- 下载失败网页：{len(errors)}",
        "",
        "## 文档",
        "",
    ]

    current = None
    for record in sorted(ok, key=lambda r: (r.collection, r.title, r.source_url)):
        if record.collection != current:
            current = record.collection
            lines.extend([f"### {current}", ""])
        title = record.title.replace("\n", " ").strip() or record.source_url
        lines.append(
            f"- [{title}]({record.markdown_file}) — {record.source_url}"
        )

    if errors:
        lines.extend(["", "## 下载失败记录", ""])
        for record in errors:
            lines.append(f"- `{record.source_url}`：{record.error}")

    (output_root / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_zip(output_root: Path) -> Path:
    zip_path = output_root.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in output_root.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(output_root.parent))
    return zip_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="下载OriginPro originpro官方资料并生成Codex离线知识库。"
    )
    parser.add_argument(
        "--output",
        default=str(Path.cwd() / "OriginPro_Codex_KB"),
        help="输出目录，默认：当前目录/OriginPro_Codex_KB",
    )
    parser.add_argument("--max-python", type=int, default=300)
    parser.add_argument("--max-external", type=int, default=120)
    parser.add_argument("--max-api", type=int, default=500)
    parser.add_argument(
        "--workers",
        type=int,
        default=6,
        help="并发下载线程数，默认：6",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="完成后不生成总ZIP。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.workers < 1 or args.workers > 16:
        raise ValueError("--workers 必须在 1 到 16 之间")
    output_root = Path(args.output).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    create_start_here(output_root)

    all_records: list[PageRecord] = []
    component_status = {}

    collections = [
        {
            "collection": "Origin Python documentation",
            "seeds": [
                "https://docs.originlab.com/python/",
                "https://docs.originlab.com/python/examples/",
                "https://docs.originlab.com/python/examples/graphing/",
                "https://docs.originlab.com/python/documentation-for-originpro-package/",
            ],
            "host": "docs.originlab.com",
            "prefix": "/python/",
            "max_pages": args.max_python,
        },
        {
            "collection": "External Python documentation",
            "seeds": [
                "https://docs.originlab.com/externalpython/",
                "https://docs.originlab.com/externalpython/external-python-code-samples/",
            ],
            "host": "docs.originlab.com",
            "prefix": "/externalpython/",
            "max_pages": args.max_external,
        },
        {
            "collection": "originpro API reference",
            "seeds": [
                "https://docs.originlab.com/originpro/",
                "https://docs.originlab.com/originpro/annotated.html",
                "https://docs.originlab.com/originpro/classes.html",
            ],
            "host": "docs.originlab.com",
            "prefix": "/originpro/",
            "max_pages": args.max_api,
        },
    ]

    for spec in collections:
        records = crawl_collection(
            output_root=output_root,
            collection=spec["collection"],
            seeds=spec["seeds"],
            allowed_host=spec["host"],
            allowed_prefix=spec["prefix"],
            max_pages=spec["max_pages"],
            workers=args.workers,
        )
        all_records.extend(records)

    try:
        component_status["official_samples"] = download_and_extract_samples(output_root)
    except Exception as exc:
        component_status["official_samples"] = {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(f"\n官方示例仓库下载失败：{exc}")

    try:
        component_status["originpro_pypi"] = download_originpro_package(output_root)
    except Exception as exc:
        component_status["originpro_pypi"] = {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
        }
        print(f"\noriginpro PyPI包下载失败：{exc}")

    metadata = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_root),
        "workers": args.workers,
        "collections": [
            {
                "name": spec["collection"],
                "seeds": spec["seeds"],
                "allowed_host": spec["host"],
                "allowed_prefix": spec["prefix"],
                "max_pages": spec["max_pages"],
            }
            for spec in collections
        ],
        "components": component_status,
        "pages": [asdict(record) for record in all_records],
    }

    create_index(output_root, all_records, metadata)
    (output_root / "manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    zip_path = None
    if not args.no_zip:
        zip_path = make_zip(output_root)

    print("\n完成。")
    print(f"知识库目录：{output_root}")
    if zip_path:
        print(f"知识库压缩包：{zip_path}")
    print("首先打开：00_START_HERE.md")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n用户中止。")
        raise SystemExit(130)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
