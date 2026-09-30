# OriginPro + Codex 科研绘图工具包

面向 Windows 的 OriginPro 自动绘图配置工具：本地官方资料检索、Codex Skill、项目 Agent 规则、资料下载器和环境检查。

## 下载和使用

新手：到本仓库 Releases 下载 `originpro-codex-toolkit-v1.0.0.zip` 并解压。无需 Git。

1. 自行安装并授权 OriginPro，安装 Python 3.10 或更高版本，配置 Codex。
2. 在解压目录打开 PowerShell，执行：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe check_environment.py
.\.venv\Scripts\python.exe download_all.py
```

首次下载需要网络；完成后 Codex 可在本地检索资料。网络中断时可重试；下载器日志和 manifest 用于检查缺失，不以目录存在判断完整。

3. 推荐在 Codex 中直接打开整个解压目录，其根目录 `AGENTS.md` 会提供 OriginPro 规则。
4. 可选：安装本项目 Skill：

```powershell
.\.venv\Scripts\python.exe install_skill.py
```

已有同名 Skill 时安装器会停止，不覆盖；安装后新建 Codex 聊天以加载 Skill。也可将 `templates/AGENTS.originpro.md` 的相关段落手动合并到其他项目的 AGENTS.md，并写明资料实际路径。

## 给 Codex 的首个绘图任务

> 请先检索当前项目 OriginPro_Codex_KB，然后读取我提供的 CSV。用外部 Python originpro 绘制所需曲线，调试时显示 Origin，保存可编辑 OPJU 和 300 DPI PNG；代码在 finally 中关闭 Origin。先核对 API，再执行并视觉检查。不要编造数据。

## 包含哪些内容

- `download_originpro_kb.py`：官方 Python 文档、API、示例和包源码下载与索引。
- `download_labtalk_axis_supplement.py`：LabTalk 坐标轴专题。
- `download_publication_graphing_supplement.py`：模板、图例、多面板和出版格式专题。
- `download_all.py`：依次运行上述三个下载器，失败即停止。
- `check_environment.py`：Python、依赖包和知识库状态检查，不启动 Origin。
- `install_skill.py`：安装本项目适配后的 MIT Skill，不覆盖现有目录。
- `validate_publication_graphing_supplement.py`：论文绘图专题资料的结构检查，不验证 Origin 绘图。会写入历史实测摘要的 finalize 脚本不随包分发。

## 验证边界

本版已检查脚本语法、命令行入口、路径可迁移性和打包内容。环境检查只能证明包可导入，不能证明 Origin 启动、许可证、绘图或导出成功。本次发布未在全新电脑完成安装，也未重新运行整站下载和 Origin 绘图。

离线 ZIP、官方 PDF、研究数据、日志、OPJU 和个人配置未公开。需要离线知识库时运行下载器；第三方来源与分发范围见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。旧版 2024b 轴验证结论不自动适用于其他版本。

## 视频演示顺序

下载发行包 → 安装依赖 → 检查环境 → 下载资料 → 打开 Codex 项目 → 提供自己的数据 → 生成并检查图片和 OPJU。

安装或绘图问题请通过 GitHub Issues 提交，附版本、错误信息与可公开的最小示例；不要上传凭据或未公开科研数据。
