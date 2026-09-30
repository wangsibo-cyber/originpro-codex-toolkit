"""选择离线知识库 ZIP，验证后导入固定位置，拒绝覆盖。"""
from pathlib import Path, PurePosixPath
import argparse
import json
import os
import shutil
import sys
import uuid
import zipfile

def long_path(path):
    path = path.resolve()
    if os.name == 'nt' and not str(path).startswith('\\\\?\\'):
        return Path('\\\\?\\' + str(path))
    return path

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--agents-home', type=Path, default=Path.home() / '.agents')
    args = parser.parse_args()
    skill = args.agents_home.resolve() / 'skills' / 'originpro-codex-bundle'
    marker = skill / 'bundle-install.json'
    if not marker.is_file() or not json.loads(marker.read_text(encoding='utf-8')).get('complete'):
        raise RuntimeError('请先双击【一键安装.bat】，完成 Skill 配置。')
    source = args.source
    if source is None:
        import tkinter as tk
        from tkinter import filedialog
        window = tk.Tk()
        window.withdraw()
        chosen = filedialog.askopenfilename(title='选择网盘下载的完整 OriginPro 离线资料 ZIP', filetypes=[('ZIP 资料包','*.zip')])
        window.destroy()
        if not chosen:
            print('已取消，未修改任何资料。')
            return 0
        source = Path(chosen)
    target = skill / 'OriginPro_Codex_KB'
    if target.exists():
        raise RuntimeError('资料目录已存在，未覆盖：' + str(target))
    stage = skill / ('.kb-' + uuid.uuid4().hex[:8])
    stage.mkdir()
    try:
        with zipfile.ZipFile(source) as z:
            entries = z.infolist()
            candidates = [PurePosixPath(x.filename).parent for x in entries if PurePosixPath(x.filename).name == '00_START_HERE.md']
            if len(candidates) != 1:
                raise RuntimeError('没有找到唯一的知识库入口，请选择完整资料包。')
            prefix = candidates[0]
            total = 0
            names = set()
            for entry in entries:
                item = PurePosixPath(entry.filename)
                if item.is_absolute() or '..' in item.parts or '\\' in entry.filename or ':' in entry.filename:
                    raise RuntimeError('ZIP 包含不安全路径，已停止。')
                try:
                    rel = item.relative_to(prefix)
                except ValueError:
                    continue
                if entry.is_dir() or str(rel) == '.':
                    continue
                name = str(rel).casefold()
                if name in names:
                    raise RuntimeError('ZIP 含重复目标文件。')
                names.add(name)
                total += entry.file_size
                if total > 1024**3:
                    raise RuntimeError('资料包展开超过 1 GiB，已停止。')
                dest = long_path(stage.joinpath(*rel.parts))
                dest.parent.mkdir(parents=True, exist_ok=True)
                with z.open(entry) as src, dest.open('wb') as dst:
                    shutil.copyfileobj(src,dst)
        from setup_bundle import validate_kb
        validate_kb(long_path(stage))
        (long_path(stage) / 'USE_THIS_KB.md').write_text('本知识库安装于 SKILL.md 同级的 OriginPro_Codex_KB。不要沿用发布者旧盘符。历史验证仅适用于原验证环境。\n',encoding='utf-8')
        stage.rename(target)
        print('离线资料导入成功：', target)
        print('请重启 Codex，使用 $originpro-codex-bundle 检查知识库，然后绘图。')
        print('导入后，原 ZIP 和配置包不再是运行必需文件。')
        return 0
    finally:
        if stage.exists():
            # 此目录是本次创建的随机临时目录，位于确认的 Skill 安装目录内。
            assert stage.resolve().parent == skill.resolve()
            shutil.rmtree(long_path(stage))

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print('导入失败：', exc)
        raise SystemExit(1)
