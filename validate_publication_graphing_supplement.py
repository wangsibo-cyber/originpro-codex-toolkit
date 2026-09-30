#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the curated OriginPro publication graphing supplement."""

from __future__ import annotations

import argparse
import json
import py_compile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_DOCUMENTS = 80
EXPECTED_CATEGORIES = {
    "绘图对象层级": 6,
    "Plot Details曲线格式": 18,
    "按数据驱动样式": 6,
    "模板与主题": 12,
    "图例标注与误差": 18,
    "多图层与组合图": 8,
    "出版与导出": 12,
}
KEYWORD_CHECKS = {
    "Page-Layer-Plot层级": ("page-layer-plot-hierarchy", "Page"),
    "分组递增": ("pd-dialog-group-tab", "Increment"),
    "颜色映射": ("pd-dialog-colormap-tab", "Colormap"),
    "分类图例": ("legend-catedata", "Categorical"),
    "逐点图例": ("pts-pts-legend", "Point"),
    "对象附着": ("attachment-scaling-object", "Layer and Scales"),
    "图模板": ("graph-template-elements", "template"),
    "主题管理": ("themeref-themeorganizer", "Increment List"),
    "多图合并": ("graphref-mergegraph", "Merge"),
    "导出DPI": ("settings-in-expgraph-dailog", "DPI"),
    "expGraph命令": ("x-function/ref/expgraph", "expGraph"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验OriginPro论文绘图补充知识库。")
    parser.add_argument(
        "--kb-root",
        default=str(Path.cwd() / "OriginPro_Codex_KB"),
        help="知识库根目录。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kb_root = Path(args.kb_root).expanduser().resolve()
    root = kb_root / "07_PUBLICATION_GRAPHING_SUPPLEMENT"
    errors: list[str] = []
    checks: list[tuple[str, bool, str]] = []

    manifest_path = root / "manifest_publication_graphing.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"manifest读取失败: {exc}")
        return 2

    documents = manifest.get("documents", [])
    checks.append((
        "manifest文档数量",
        len(documents) == EXPECTED_DOCUMENTS,
        f"{len(documents)}/{EXPECTED_DOCUMENTS}",
    ))
    urls = [item.get("official_url", "") for item in documents]
    checks.append((
        "官方URL唯一",
        len(urls) == len(set(urls)),
        f"unique={len(set(urls))}",
    ))
    official_only = all(
        url.startswith("https://docs.originlab.com/") for url in urls
    )
    checks.append(("仅OriginLab官方域名", official_only, "docs.originlab.com"))

    category_counts = Counter(item.get("category", "") for item in documents)
    checks.append((
        "分类数量",
        dict(category_counts) == EXPECTED_CATEGORIES,
        json.dumps(dict(category_counts), ensure_ascii=False),
    ))
    statuses = Counter(item.get("status", "") for item in documents)
    checks.append((
        "下载状态",
        statuses == {"ok": EXPECTED_DOCUMENTS},
        json.dumps(dict(statuses), ensure_ascii=False),
    ))

    for item in documents:
        url = item.get("official_url", "")
        for field in ("html_path", "markdown_path", "tables_path"):
            rel = item.get(field, "")
            path = root / rel
            if not rel or not path.exists() or path.stat().st_size == 0:
                errors.append(f"{url}: {field} 缺失或为空: {rel}")
        markdown_path = root / item.get("markdown_path", "")
        if markdown_path.exists():
            text = markdown_path.read_text(encoding="utf-8", errors="replace")
            for marker in (
                "- 官方来源：",
                "- 实际下载地址：",
                "- 下载时间：",
                "- 文档用途：",
                "- 与originpro的关系：",
            ):
                if marker not in text[:3000]:
                    errors.append(f"{url}: Markdown缺少元数据 {marker}")
            if len(text) < 300:
                errors.append(f"{url}: Markdown内容过短 ({len(text)})")
            if "Internal Error" in text[:1000]:
                errors.append(f"{url}: Markdown疑似错误页面")
        tables_path = root / item.get("tables_path", "")
        if tables_path.exists():
            try:
                json.loads(tables_path.read_text(encoding="utf-8"))
            except Exception as exc:
                errors.append(f"{url}: 表格JSON无效: {exc}")

    counts = {
        "html": len(list((root / "01_HTML").rglob("*.html"))),
        "markdown": len(list((root / "02_MARKDOWN").rglob("*.md"))),
        "tables_json": len(
            list((root / "03_EXTRACTED_REFERENCE" / "tables").rglob("*.json"))
        ),
    }
    checks.append((
        "三套网页产物数量",
        counts == {
            "html": EXPECTED_DOCUMENTS,
            "markdown": EXPECTED_DOCUMENTS,
            "tables_json": EXPECTED_DOCUMENTS,
        },
        json.dumps(counts, ensure_ascii=False),
    ))

    for label, (path_fragment, keyword) in KEYWORD_CHECKS.items():
        matches = [
            root / item["markdown_path"]
            for item in documents
            if path_fragment in item.get("markdown_path", "")
        ]
        found = any(
            keyword.casefold()
            in path.read_text(encoding="utf-8", errors="replace").casefold()
            for path in matches
            if path.exists()
        )
        checks.append((f"关键词：{label}", found, keyword))

    required_files = [
        root / "INDEX_PUBLICATION_GRAPHING.md",
        root / "PUBLICATION_GRAPHING_QUICK_REFERENCE.md",
        root / "OFFICIAL_RECIPE_INDEX.md",
        root / "ORIGIN_DRAWING_PROMPT_TEMPLATE.md",
        root / "03_EXTRACTED_REFERENCE" / "TOPIC_MAP.json",
        root / "03_EXTRACTED_REFERENCE" / "DUPLICATE_AUDIT.json",
        kb_root / "00_START_HERE.md",
        kb_root / "INDEX.md",
    ]
    missing_required = [
        str(path) for path in required_files
        if not path.exists() or path.stat().st_size == 0
    ]
    checks.append((
        "索引和速查文件",
        not missing_required,
        "ok" if not missing_required else "; ".join(missing_required),
    ))

    script_path = kb_root.parent / "download_publication_graphing_supplement.py"
    try:
        py_compile.compile(str(script_path), doraise=True)
        script_ok = True
        script_detail = "py_compile ok"
    except Exception as exc:
        script_ok = False
        script_detail = str(exc)
    checks.append(("下载脚本语法", script_ok, script_detail))

    duplicate_hits = [
        item for item in manifest.get("duplicate_audit", [])
        if item.get("already_in_existing_manifests")
    ]
    checks.append((
        "与已有manifest URL去重",
        not duplicate_hits,
        f"existing_hits={len(duplicate_hits)}",
    ))

    failed_checks = [item for item in checks if not item[1]]
    if errors:
        failed_checks.append(("逐文档检查", False, f"errors={len(errors)}"))

    report_lines = [
        "# 论文绘图与格式化补充校验报告",
        "",
        f"- 校验时间（UTC）：{datetime.now(timezone.utc).isoformat()}",
        f"- 知识库：`{kb_root}`",
        f"- 目标官方页面：{EXPECTED_DOCUMENTS}",
        f"- 逐文档错误：{len(errors)}",
        f"- 总体结果：{'PASS' if not failed_checks else 'FAIL'}",
        "",
        "## 检查项",
        "",
        "| 检查 | 结果 | 详情 |",
        "| --- | --- | --- |",
    ]
    for label, passed, detail in checks:
        safe_detail = str(detail).replace("|", "\\|").replace("\n", " ")
        report_lines.append(
            f"| {label} | {'PASS' if passed else 'FAIL'} | {safe_detail} |"
        )
    report_lines.extend(["", "## 逐文档错误", ""])
    if errors:
        report_lines.extend(f"- {error}" for error in errors)
    else:
        report_lines.append("- 无。")
    report_lines.extend([
        "",
        "## 结论",
        "",
        (
            "80个目标页面均已生成原始HTML、可检索Markdown和表格JSON；"
            "专题索引、中文速查、官方配方索引和提示词模板齐全。"
            if not failed_checks
            else "存在失败检查，归档前必须处理。"
        ),
        "",
    ])
    report_path = root / "VALIDATION_REPORT.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    for label, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'} {label}: {detail}")
    for error in errors:
        print(f"ERROR {error}")
    print(report_path)
    return 0 if not failed_checks else 2


if __name__ == "__main__":
    raise SystemExit(main())
