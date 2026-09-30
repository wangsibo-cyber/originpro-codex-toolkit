"""双击安装入口：将 Skill、运行环境和资料安装在同一用户目录。"""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid

VERSION = '1.1.0'
NAME = 'originpro-codex-bundle'
ROOT = Path(__file__).resolve().parent

def run(command):
    subprocess.run([str(x) for x in command], check=True)

def validate_kb(kb):
    required = ['00_START_HERE.md', '02_MARKDOWN/docs.originlab.com/originpro',
                '06_LABTALK_AXIS_SUPPLEMENT/LABTALK_AXIS_QUICK_REFERENCE.md',
                '07_PUBLICATION_GRAPHING_SUPPLEMENT/PUBLICATION_GRAPHING_QUICK_REFERENCE.md']
    for relative in required:
        if not (kb / relative).exists():
            raise RuntimeError('知识库缺少：' + relative)
    for folder in ('02_MARKDOWN/docs.originlab.com/originpro',):
        if not any((kb / folder).rglob('*.md')):
            raise RuntimeError('API 文档目录为空。')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agents-home', type=Path, default=Path.home() / '.agents')
    parser.add_argument('--skip-deps', action='store_true', help='仅供安装逻辑 QA，不安装 Python 依赖')
    args = parser.parse_args()
    if os.name != 'nt' or sys.version_info[:2] != (3, 11):
        raise RuntimeError('请先安装 Windows 64 位 Python 3.11，再双击安装。')
    if sys.maxsize <= 2**32:
        raise RuntimeError('需要 64 位 Python。')
    target = args.agents_home.resolve() / 'skills' / NAME
    marker = target / 'bundle-install.json'
    if target.exists():
        if marker.is_file() and json.loads(marker.read_text(encoding='utf-8')).get('version') == VERSION and json.loads(marker.read_text(encoding='utf-8')).get('complete'):
            print('此版本已经安装，未覆盖：', target)
            if not (target / 'OriginPro_Codex_KB' / '00_START_HERE.md').exists():
                print('尚未导入知识库，请双击【导入离线资料.bat】。')
            return 0
        raise RuntimeError('安装目标已存在且不匹配；为保护原文件停止：' + str(target))
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = target.parent / ('.install-' + uuid.uuid4().hex[:8])
    stage.mkdir()
    print('[1/4] 准备绘图 Skill')
    source = ROOT / 'skills' / 'python-origin-plotting'
    shutil.copytree(source, stage, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copytree(ROOT / 'licenses', stage / 'licenses')
    shutil.copy2(ROOT / 'THIRD_PARTY_NOTICES.md', stage / 'THIRD_PARTY_NOTICES.md')
    kb = stage / 'OriginPro_Codex_KB'
    try:
        print('[2/4] 建立 Python 绘图环境')
        if not args.skip_deps:
            run([sys.executable, '-m', 'venv', stage / '.venv'])
            run([stage / '.venv' / 'Scripts' / 'python.exe', '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt'])
        print('[3/4] 配置本地知识库')
        if (ROOT / 'OriginPro_Codex_KB' / '00_START_HERE.md').is_file():
            print('检测到随包资料，复制到安装目录，不重新下载文档。')
            shutil.copytree(ROOT / 'OriginPro_Codex_KB', kb, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            print('本包不带官方文档，也不会自动下载。配置完成后双击【导入离线资料.bat】，选择网盘资料 ZIP。')
        if kb.exists():
            validate_kb(kb)
            kb_entry = kb / 'USE_THIS_KB.md'
            kb_entry.write_text('本知识库随 Skill 安装。实际位置为 SKILL.md 同级的 OriginPro_Codex_KB；不要使用发布者旧盘符。历史实测结果仅代表发布者原环境。\n', encoding='utf-8')
        (stage / 'SKILL.md').write_text('''---
name: originpro-codex-bundle
description: 使用随 Skill 安装的官方离线知识库和 Windows Python originpro 绘制科研图，交付可编辑 OPJU 及实际导出的图片。
---

# OriginPro 科研绘图完整配置

- 知识库始终在本 SKILL.md 所在目录下的 `OriginPro_Codex_KB/`，不依赖最初解压目录。用户明确指定其他知识库时优先遵循用户。
- Python 运行环境在本 SKILL.md 所在目录下的 `.venv/Scripts/python.exe`。正式执行先检查它可用，不使用不明来源的解释器。
- 先读知识库的 `00_START_HERE.md`；样式、图例、多面板查论文绘图专题；轴设置查 LabTalk 轴专题；API 查本地官方 API 文档和示例，禁止猜测。
- 历史 2024b 验证报告是发布者旧环境证据，不代表使用者的安装或版本已验证。需要时复验。
- 先确认真实数据、目标图型、模板与输出路径。使用高级 originpro API；只有高级 API 不足时才用经核实的 LabTalk，记录依据。
- 调试阶段显示 Origin；外部 Python 保证 finally 中执行 op.exit()。
- 保留用户原始数据与模板，明确导出尺寸/DPI和 OPJU 路径。必要时通过明确的 ASCII 临时目录导出，再复制。
- 交付原生可编辑 OPJU 和实际导出的 PNG/TIFF，完成视觉检查；需要 SVG 时核实本机支持后提供。没有真实运行不能声称绘图通过。
- 故障排查可查 `references/`，脚本模板见 `scripts/`。上游 MIT 许可在 `licenses/`。安装或可导入不等于 Origin 引擎、许可证或绘图通过。
''', encoding='utf-8')
        # venv 的激活脚本包含绝对路径，因此先将目录固定，再重建环境入口。
        stage.rename(target)
        if not args.skip_deps:
            run([sys.executable, '-m', 'venv', target / '.venv'])
            run([target / '.venv' / 'Scripts' / 'python.exe', '-c', 'import originpro, pandas, openpyxl, bs4; print("绘图依赖可导入")'])
        (target / 'bundle-install.json').write_text(json.dumps({'version': VERSION, 'name': NAME, 'qa_only': args.skip_deps, 'complete': True}, ensure_ascii=False), encoding='utf-8')
        print('[4/4] 安装完成：', target)
        print('请重启 Codex，在任意本地绘图项目中新建聊天，输入：使用 $originpro-codex-bundle，先检查知识库和 Origin 环境。')
        print('安装完成后可以移动或删除原解压文件夹。OriginPro 和 Codex 须自行安装并授权。')
        if not (target / 'OriginPro_Codex_KB' / '00_START_HERE.md').is_file():
            print('注意：Skill 配置已安装，知识库尚未导入；先导入资料，再正式绘图。')
        return 0
    except Exception:
        print('安装未完成。已准备文件保留在：', stage if stage.exists() else target)
        raise

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('配置失败：', exc)
        raise SystemExit(1)
