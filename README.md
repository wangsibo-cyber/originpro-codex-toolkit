# OriginPro + Codex 科研绘图工具包

Windows 双击配置版：安装绘图 Skill 和独立 Python 运行环境，单独导入离线资料包。不会自动下载文档；无需手动输入 PowerShell 命令。

## 从零开始

1. 自行安装并登录 Codex，安装已授权的 OriginPro，以及 Windows 64 位 Python 3.11（启用 Python Launcher 或加入 PATH）。OriginPro 先手动打开一次。
2. 从 [Releases](https://github.com/wangsibo-cyber/originpro-codex-toolkit/releases/tag/v1.1.0) 下载 `originpro-codex-toolkit-v1.1.0.zip`，右键“全部解压”。不要在压缩包内部直接运行。
3. 双击 `一键安装.bat`。它会联网安装 Python 依赖、配置 Skill，但不下载官方文档。窗口最后显示安装完成再继续。
4. 如果已有完整离线资料 ZIP，双击 `导入离线资料.bat`，在文件选择窗口中选中 ZIP。无需提前解压，也不用决定资料放在哪里。
5. 重启 Codex，在自己的本地绘图文件夹中新建聊天，输入：

> 使用 $originpro-codex-bundle。先读取随 Skill 安装的 OriginPro_Codex_KB，并使用随 Skill 的 Python 环境检查 OriginPro。然后根据我提供的真实数据和图型要求，生成可编辑 OPJU 和 PNG，并实际检查结果。

## 资料到底放在哪里

安装器自动固定到：`%USERPROFILE%\.agents\skills\originpro-codex-bundle\OriginPro_Codex_KB`。

Python 环境和 Skill 也安装在该 Skill 目录中。解压目录可任意选择；安装和导入成功后，移动或删除原解压文件夹不会影响已安装内容。

无需连接 GitHub 账号。Codex 中使用 Windows 本地运行环境；OriginPro、Python 和 Codex 软件本身不随包提供。

## 没有离线资料包怎么办

配置包保留 `download_all.py` 和三个专题下载器。可让 Codex 在本机运行下载器获取官方资料，再按实际路径使用。本版双击安装器不会自动整站下载。

## 已有旧 Skill

新入口名为 `originpro-codex-bundle`，不覆盖旧 `python-origin-plotting`。重复安装同版不覆盖；资料已存在时导入器会停止保护原文件。单独的 `install_skill.py` 保留给需要旧 Skill 的使用者，不是新手必需步骤。

## 包含与不包含

包含 MIT 上游绘图 Skill、参考说明、脚本模板、Agent 规则、下载器、双击安装器与 ZIP 导入器。上游许可见 `licenses/`。

不包含官方文档快照、PDF、研究数据、日志、OriginPro/Codex/Python 安装程序。官方文档公开再分发要求见 [OriginLab 条款](https://www.originlab.com/index.aspx?go=Company/TermsOfUse)，本发行版没有公开上传旧离线 ZIP。

## 检查范围

实际完成临时环境依赖安装、中文/空格路径安装、现有完整离线 ZIP 导入、拒绝覆盖及路径安全检查。详细结果见 [QA_REPORT.md](QA_REPORT.md)。未在全新电脑验收，未做 GUI 文件选择或真实双击视觉检查，未启动 Origin 或验证绘图与许可证。

## 视频讲解

“先装好 Codex、OriginPro 和 Python 3.11；下载配置包并全部解压，双击一键安装。已有离线资料包时，再双击导入离线资料，选中 ZIP。最后重启 Codex，用 originpro-codex-bundle 绘图。”
