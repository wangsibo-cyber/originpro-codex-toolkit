"""只读检查环境，不启动 Origin。"""
from pathlib import Path
import importlib
import sys
import os

def main():
    print('Python:', sys.version.split()[0])
    print('Windows:', os.name == 'nt')
    ok = os.name == 'nt' and sys.version_info >= (3, 10)
    for name in ('originpro', 'pandas', 'openpyxl', 'bs4'):
        try:
            module = importlib.import_module(name)
            print(name + ': 可导入 ' + str(getattr(module, '__version__', '')))
        except Exception as exc:
            print(name + ': 未通过 ' + type(exc).__name__)
            ok = False
    kb = Path(os.environ.get('ORIGINPRO_KB_ROOT', str(Path(__file__).resolve().parent / 'OriginPro_Codex_KB')))
    exists = (kb / '00_START_HERE.md').is_file()
    print('知识库:', str(kb), '入口存在' if exists else '需下载')
    print('此检查不代表 Origin 引擎、许可证或绘图已验证。')
    return 0 if ok else 1

if __name__ == '__main__':
    raise SystemExit(main())
