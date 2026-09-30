"""下载本地资料；三个阶段依次执行，失败即停止。"""
from pathlib import Path
import argparse
import subprocess
import sys

def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kb-root', type=Path, default=root / 'OriginPro_Codex_KB')
    args = parser.parse_args()
    kb = str(args.kb_root.resolve())
    for script, flag in [('download_originpro_kb.py', '--output'), ('download_labtalk_axis_supplement.py', '--kb-root'), ('download_publication_graphing_supplement.py', '--kb-root')]:
        result = subprocess.run([sys.executable, str(root / script), flag, kb], cwd=root)
        if result.returncode:
            return result.returncode
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
