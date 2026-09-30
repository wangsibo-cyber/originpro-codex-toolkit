"""安装适配后的 MIT Skill；拒绝覆盖已有目录。"""
from pathlib import Path
import argparse
import os
import shutil

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', type=Path, default=Path.home() / '.agents')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / 'skills' / 'python-origin-plotting'
    target = args.codex_home / 'skills' / source.name
    if target.exists():
        print('已有目录，不覆盖:', target)
        return 1
    shutil.copytree(source, target)
    print('已安装:', target)
    print('在绘图项目 AGENTS.md 中注明知识库实际路径，并新建 Codex 聊天。')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
