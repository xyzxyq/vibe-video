# vibe-video · 动画视频制作 Skill

基于 Remotion 的中文知识动画视频制作 skill，覆盖选题、分镜脚本、画面制作、渲染混音、逐帧审片和发布文案。

## 文件结构

- [`vibe-video/SKILL.md`](vibe-video/SKILL.md)：skill 入口与制作流程。
- [`vibe-video/references/`](vibe-video/references/)：Remotion 制作说明、审片清单与脚本标准。
- [`vibe-video/assets/starter/`](vibe-video/assets/starter/)：Remotion 起手工程。
- [`vibe-video/scripts/`](vibe-video/scripts/)：混音、音效生成、局部拼接与抠图工具。
- [`skill.zip`](skill.zip)：完整 skill 压缩包，内容与 `vibe-video/` 一致。

## 安装与使用

下载并解压 `skill.zip`，将解压后的 `vibe-video` 文件夹放入所用 AI 工具的 skills 目录。

Codex 的默认用户 skills 目录为 `~/.codex/skills/`，安装后入口文件应位于 `~/.codex/skills/vibe-video/SKILL.md`。

使用时读取 `SKILL.md`；需要制作与渲染视频时，按其中说明使用参考文档和起手工程。

## 原始内容与运行条件

本仓库从原始“动画视频制作”目录独立提取，保留全部 25 个源文件及其原始内容，仅增加此说明和 `.gitignore`。

原始 skill 包含特定项目的风格、175 秒时长、Linux 容器路径及对既有聊天上下文的引用。实际使用时需按自己的环境调整，并自行提供参考视频、背景音乐等外部素材；这些素材不包含在本仓库中。

本次独立发布已核对源文件完整性及压缩包一致性，未执行视频渲染验证。原始目录未附许可证，本次提取未新增许可证。
