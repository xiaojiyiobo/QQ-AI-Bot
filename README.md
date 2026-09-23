# QQ AI Bot — AI/Agent 工作说明

## 项目用途

这是一个私人 QQ AI 助手，主要供项目所有者及极少数信任的用户使用。

本项目应保持简单、模块化、易于部署。
除非用户明确要求，否则不要将项目改造成面向公众的 SaaS 服务。

## 当前已验证功能

- 通过 NapCat + OneBot 11 WebSocket 接收 QQ 私聊消息
- 支持文本对话及 AI Provider 抽象
- 支持 Gemini Provider
- 支持 Mistral Provider
- 支持图片理解
- 按平台和用户分别保存对话记忆，目前最多 10 轮
- 支持 `config/content_filter.json` 内容过滤
- 首次使用自动发送 `/help`
- 支持“先发图片，再发问题”的图片理解流程
- 提供本地 `/admin/` 管理页面，可配置 AI Provider 和模型

## 当前架构

`平台适配器 → 核心处理器 → AIManager → AI Provider`

目前只实现 QQ。
未来如果增加其他聊天平台，应通过新的平台适配器实现，不要把平台相关逻辑直接耦合进 `core` 或 `ai`。

AI Provider 位于 `src/ai/providers/`。
增加新的 AI Provider 时，应实现 `AIProvider` 接口，并在 `src/ai/manager.py` 中注册。

## 管理页面

- `src/web/app.py`：启动 FastAPI 和 QQ Bot
- `src/web/admin.py`：管理页面路由
- `src/web/config.py`：负责 `.env` 配置读取和写入
- `src/web/templates/`：管理页面模板
- `src/web/static/`：管理页面样式
- 管理页面默认仅监听本机 `127.0.0.1:8080`，默认不对局域网或公网开放
- 如果未来确有远程管理需求，应单独设计访问控制与身份验证，并在确认安全方案后再开放管理页面
- 未经过身份验证和用户明确同意，不得将管理页面暴露到公网
- API Key 不得显示在管理页面，只显示“已配置 / 未配置”
- 修改 Provider 或模型后，目前需要重启程序才能生效

## 重要配置

- `AI_PROVIDER=gemini|mistral`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `MISTRAL_API_KEY`
- `MISTRAL_MODEL`
- `MISTRAL_VISION_MODEL`
- `ONEBOT_WS_URL`
- `CONTENT_FILTER_CONFIG`

绝对不要打印、提交或公开 API Key。
不得将 Secret 写入日志、README、测试文件、截图或聊天回复。

## 开发规则

1. 修改项目之前必须先阅读本文件。
2. 修改前先检查真实文件和运行环境，不要凭假设判断项目结构。
3. 优先进行小范围、可回滚的修改，并逐步验证。
4. 不要为了展示架构扩展性而提前实现未来平台。
5. Provider 专属代码必须保持在对应 Provider 模块中。
6. Secret 必须保存在 `.env`，`.env` 绝对不能提交到 Git。
7. 没有明确理由和验证方案，不要替换已经正常工作的功能。
8. 临时测试脚本应放在 Sandbox 中，或者验证完成后删除。
9. 部署前增加 Linux / Docker 支持时，不得破坏已经验证过的本地运行行为。
10. 修改启动方式时，必须确认最终只有一个 Bot 实例运行，避免 QQ 重复回复。

## 当前运行方式

### Windows 本地开发 / 测试

当前已验证的开发 / 测试环境为 Windows + QQ + NapCat + OneBot 11 + QQ-AI-Bot。

在项目根目录运行 `run.bat` 即可启动 `src/main.py`。

`AI_PROVIDER` 用于选择 AI Provider。

程序会在同一个进程中同时启动：

- 管理 HTTP 服务
- QQ Bot

本地管理页面默认仅本机可访问：

`http://127.0.0.1:8080/admin/`

### Linux / VPS / Docker 部署

QQ-AI-Bot 本身不应与 Windows 或本地 QQ 客户端运行环境耦合。它通过 OneBot 11 WebSocket 与 QQ / NapCat 通信，因此可以将 QQ-AI-Bot 部署在 Linux 服务器、VPS 或 Docker 环境中。

当前正在单独的 Linux VPS 环境中进行 **24 小时正式环境实测**。该环境与 Windows 本地开发 / 测试环境分离，不影响 Windows 端的开发和验证。

当前正式环境的目标部署结构为：

`Linux VPS → Docker / Docker Compose → NapCat + QQ-AI-Bot`

其中 QQ / NapCat 负责提供 QQ 接入，QQ-AI-Bot 通过 OneBot 11 WebSocket 与 NapCat 通信。NapCat 与 QQ-AI-Bot 也可以部署在不同机器上，只要 OneBot WebSocket 网络可达。OneBot 11 的 WebSocket 通信模式支持 NapCat 作为客户端连接 Bot 侧的 WebSocket 服务端。

Linux / VPS / Docker 部署目前属于**正在实测中的部署方式**，在正式环境验证完成前，不将其描述为与 Windows 一样的完整已验证流程。

增加 Linux / Docker 支持时，必须保持现有 Windows 本地运行方式可用，并确保最终只有一个 QQ Bot 实例运行，避免重复回复。

生产环境的管理页面默认仍不应直接暴露到公网；如确有远程管理需求，应先设计身份验证、访问控制以及必要的反向代理 / HTTPS 方案。

## 部署方向

目标部署环境为 **Linux 服务器**，包括 VPS、独立服务器以及其他能够长期运行 Linux 的服务器环境。

当前优先验证 **VPS 24 小时独立运行**方案，并以 Docker / Docker Compose 作为正式环境的部署方式进行实测。

Windows 主要作为本地开发 / 测试环境；Linux 服务器用于长期运行 QQ Bot。两者应保持环境隔离，避免测试过程影响正式 QQ Bot。

Docker 化部署正在当前正式环境中实测。验证完成后，再将完整的 Linux / Docker 部署步骤整理为其他用户可以直接复现的部署文档。