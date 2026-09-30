---
name: python-origin-plotting
description: >
  Automate OriginPro figure generation from Excel or CSV data through Python originpro.
  Use when an agent needs to create, reproduce, or refine Origin/OriginPro .opju
  projects, publication PNG/TIFF exports, worksheet import pipelines, grouped bar
  charts, dual-axis charts, scatter/line plots, or chart styling scripts using
  Python-driven Origin automation.
metadata:
  openclaw:
    requires:
      bins:
        - python
    env: []
    os:
      - windows
    homepage: https://github.com/Gerry2024-hub/Gerry2024-hub-python-origin-plotting-skill
    category: data-visualization
    emoji: "📊"
---

# Python Origin Plotting

Use this skill to turn tabular data and plotting requirements into reproducible OriginPro projects driven by Python `originpro`.

## Mandatory Local Knowledge Base Preflight

Before writing, modifying, or running any OriginPro plotting code, consult the local knowledge base. This is a required preflight, not an optional reference step.

1. Resolve the knowledge-base root:
   - Use a path explicitly supplied by the user when present.
   - Otherwise use `OriginPro_Codex_KB` in the current project, or the `ORIGINPRO_KB_ROOT` environment variable. Never use the publisher's drive paths.
   - Confirm the root and `00_START_HERE.md` exist. If either is missing or unreadable, report the exact missing path and request the correct location before producing formal Origin code.
2. Read `00_START_HERE.md`, then route the lookup by task:
   - Publication styling, templates, legends, annotations, error bars, multi-panel layouts, or export: read `07_PUBLICATION_GRAPHING_SUPPLEMENT/PUBLICATION_GRAPHING_QUICK_REFERENCE.md`.
   - Axis ranges, ticks, endpoints, number formats, or titles: read `06_LABTALK_AXIS_SUPPLEMENT/LABTALK_AXIS_QUICK_REFERENCE.md` and `06_LABTALK_AXIS_SUPPLEMENT/VERIFICATION_REPORT.md`.
   - Python API names, classes, methods, parameters, or return values: search `02_MARKDOWN/docs.originlab.com/originpro/`.
   - External-Python lifecycle and examples: search `02_MARKDOWN/docs.originlab.com/externalpython/`.
   - Reusable implementation patterns: search `04_OFFICIAL_PYTHON_SAMPLES/`, then inspect `05_ORIGINPRO_PYPI_PACKAGE/` only when package behavior must be confirmed.
3. Search narrowly for the exact API, property, template, or graph type required. Read the relevant local official page or sample before using it; do not load the whole knowledge base into context.
4. Prefer evidence in this order: local official API/reference pages, official local samples, local verification reports, then the bundled references in this skill.
5. Do not infer Python APIs from Origin GUI documentation. Keep Page, Layer, Plot, Axis, Label, and other graph-object ownership distinct.
6. Do not invent an API, LabTalk property, enum value, or parameter. If the local sources do not verify it, say that it remains unverified and use a verified alternative or ask the user before proceeding.
7. Before coding, briefly record which local files were consulted and which non-obvious API or LabTalk properties were verified. Add a source-path comment beside version-sensitive or LabTalk-based code.

## Prerequisites

- Windows with OriginPro installed and licensed.
- Python that can import `originpro` and `pandas`.
- Input data supplied by the user as Excel or CSV.
- No API keys or secret environment variables are required.

## Security Notes

- Inspect `scripts/originpro_plot_template.py` before running it in a new environment.
- Do not commit or publish user data files, generated figures, audit CSV files, or `.opju` projects.
- Keep script outputs inside the user-selected project/output folder and an explicit temp folder such as `E:/origin_tmp`.
- Do not download remote code or send user data to network services as part of this skill.

## First Pass

1. Complete the mandatory local knowledge-base preflight above.
2. Locate existing artifacts before writing code:
   - `*origin*.py`, `*.opju`, `*.opj`, `plots_origin/`, exported `Origin_*.png`
   - PowerShell: `Get-ChildItem -Recurse -File -Include *origin*.py,*.opju,*.opj,*.png`
3. Identify the input file, sheet name, required columns, desired chart types, output folder, and whether Origin should be visible.
4. Reuse any existing project script style first, especially workbook setup, LabTalk styling, export naming, and temp-path handling, but re-verify non-obvious APIs against the local knowledge base.
5. For a new project, copy and adapt `scripts/originpro_plot_template.py` only after completing the preflight.

## Standard Workflow

1. Load and clean data with `pandas`.
   - Read Excel or CSV.
   - Drop rows missing required plotting columns.
   - Sort data in the expected visual order.
   - Create short axis labels while preserving long labels in separate worksheet columns.
   - Export an audit CSV such as `origin_input_data_sorted.csv` with `encoding="utf-8-sig"`.

2. Start a clean Origin project.
   - `import originpro as op`
   - `op.set_show(True)` when the user should see Origin.
   - `op.new()` before creating new workbooks and graph pages.
   - Create a workbook with `op.new_book(...)`, write the DataFrame with `wks.from_df(df)`, then set column designations and labels.

3. Create graphs in Origin.
   - Use Origin graph pages and layers rather than matplotlib when the user asks for Origin output.
   - Add plots with `gl.add_plot(wks, coly=..., colx=..., type=...)`.
   - For dual-axis charts, add a second layer and explicitly manage right-Y axis titles and limits.

4. Style through Origin APIs and LabTalk.
   - Set axis titles with `gl.axis("x").title` and `gl.axis("y").title`.
   - Use `gl.lt_exec(...)` or `gp.lt_exec(...)` for labels, legends, grids, tick rotation, and template-specific styling.
   - Call `gl.rescale()` after adding plots.
   - Avoid graph titles when they overlap exports; prefer page long names and filenames.

5. Export figures and save the Origin project.
   - Export PNG/TIFF with `gp.save_fig(...)`.
   - Save `.opju` with `op.save(...)`.
   - If output paths contain Chinese characters or Origin refuses direct export, save first to an ASCII temp directory, then copy to the final path.
   - Use timestamped or versioned `.opju` names if the final project file may be locked.

6. Close Origin cleanly.
   - Put save/export logic in `try`.
   - Put `op.exit()` in `finally`.
   - Do not leave hidden Origin COM sessions running.

## References

The external local knowledge base takes precedence. Read these bundled references only when needed after the mandatory preflight:

- `references/originpro-workflow.md`: detailed implementation patterns, chart recipes, and script structure.
- `references/troubleshooting.md`: common `originpro`, COM, Chinese-path, export, and locked-file failures.

## Validation Checklist

- The local knowledge-base root and `00_START_HERE.md` were found and consulted before coding.
- Every non-obvious `originpro` method, parameter, or LabTalk property used in the final script has a local official source or verification-report basis.
- The script runs without Python exceptions on the target machine.
- Output folder contains an audit CSV, exported figure files, and a saved `.opju`.
- Figure files are non-empty and have recent modification times.
- The `.opju` opens in Origin and contains the worksheet plus graph pages.
- If Origin or `originpro` is not installed, say so clearly and do not fake Origin output with matplotlib unless the user asks for a fallback.

## Distribution attribution

Based on Gerry2024-hub/Gerry2024-hub-python-origin-plotting-skill, MIT. See licenses/python-origin-plotting-MIT.txt in the toolkit. Local knowledge-base routing and portability rules were adapted for this distribution.
