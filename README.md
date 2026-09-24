# QQ AI Bot

一个私人 QQ AI 助手。通过 NapCat + OneBot 11 WebSocket 接收 QQ 消息，并提供 FastAPI 管理后台配置 AI Provider、模型、API Key 和 QQ 登录入口。

## 当前功能

- QQ 私聊文本对话
- Gemini / Mistral Provider
- 图片理解
- 按用户保存最多 10 轮上下文
- 内容过滤
- NapCat WebUI 扫码登录 QQ
- 管理后台配置 Provider、模型和 API Key
- API Key 只显示“已配置 / 未配置”，真实 Key 不回显
- OneBot 断线自动重连：2s → 5s → 10s → 30s
- `/health` 健康检查

## 架构

```text
QQ
 ↓
NapCat + Linux QQ
 ↓ OneBot 11 WebSocket :3001（Docker 内网）
QQ-AI-Bot
 ├─ FastAPI 管理后台 :8080
 └─ AI Provider
```

Windows 本地开发和 Linux/VPS 正式环境共用同一套 Bot 代码；QQ/NapCat 运行环境通过 Docker 与 Bot 解耦。

## Windows 本地开发 / 测试

在项目根目录运行：

```text
run.bat
```

默认管理页面：

```text
http://127.0.0.1:8080/admin/
```

Windows 本地默认只监听 `127.0.0.1`，不会因此影响 Linux/VPS Docker 环境。

## Linux / VPS / Docker 正式部署

正式环境结构：

```text
Linux VPS
 └─ Docker Compose
     ├─ NapCat + QQ
     └─ QQ-AI-Bot
```

NapCat 官方 Docker 镜像支持将 QQ 数据 `/app/.config/QQ` 和 NapCat 配置 `/app/napcat/config` 持久化到宿主机；本项目在此基础上使用自己的 OneBot 配置模板，避免套用官方 `qq-ai-bot` 模板时误变成反向 WebSocket 客户端。参考 [NapCat-Docker](https://github.com/NapNeko/NapCat-Docker) 的官方 Docker 配置。

本项目的 Compose 配置因此使用：

- NapCat 使用仓库自己的 `deploy/napcat/onebot11.json` 配置模板
- OneBot WebSocket：`0.0.0.0:3001`
- Token：空字符串
- 心跳：30000ms
- 3001 **不映射到 VPS 公网**
- QQ 数据：`./data/napcat/QQ`
- NapCat 配置：`./data/napcat/config`
- 管理后台：`0.0.0.0:8080`
- NapCat WebUI：`0.0.0.0:6099`

NapCat 官方当前的 Docker 说明明确将 `/app/.config/QQ` 用于 QQ 持久化数据、`/app/napcat/config` 用于 NapCat 配置；`ACCOUNT` 也是镜像支持的可选 QQ 账号配置项。参考 [NapCat-Docker](https://github.com/NapNeko/NapCat-Docker) 的官方持久化与环境变量说明。

### 首次部署

```bash
git clone https://github.com/xiaojiyiobo/QQ-AI-Bot.git
cd QQ-AI-Bot
cp .env.example .env
mkdir -p data/app data/napcat/config data/napcat/QQ
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

部署脚本会串行执行 Compose 校验、镜像拉取、Bot 构建、启动和基础健康检查，并使用 `/tmp/qq-ai-bot-deploy.lock` 防止重复部署。

启动后：

```text
http://VPS公网IP:6099/webui/
http://VPS公网IP:8080/admin/
```

部署脚本执行完成后，会直接在终端显示 NapCat WebUI Token（从 NapCat 容器日志自动提取；NapCat 启动较慢时最多等待 60 秒）。只有当自动检测失败并显示 `[WARN]` 时，才需要手动执行：

```bash
docker logs qq-ai-bot-napcat | grep "WebUi Token"
```

第一次登录 QQ 仍然需要本人扫码。之后 QQ 数据和 NapCat 配置会保存在 `data/napcat/`，因此 Docker 重启、Compose 重启或 VPS 重启时会尽可能复用已有登录状态。**QQ 登录态最终是否会被 QQ 服务端要求重新验证，必须通过实际长时间运行测试确认，不能仅靠 Docker 持久化保证。**

### 管理后台

打开：

```text
http://VPS公网IP:8080/admin/
```

可以：

- 打开 NapCat QQ 登录 WebUI
- 切换 Gemini / Mistral
- 修改模型
- 填写或替换 API Key
- 留空 API Key 时保持原 Key 不变
- 保存配置
- 保存并重启 Bot
- 查看 Bot / OneBot / QQ 状态
- 查看最近消息时间和最近错误

生产环境当前**没有管理员登录认证**。如果直接开放 8080/6099 到公网，应使用 VPS 安全组、防火墙或后续反向代理认证控制访问范围。

## OneBot 连接

QQ-AI-Bot 使用：

```text
ws://napcat:3001
```

3001 只存在于 Docker Compose 网络中。不要把它映射到 VPS 公网。

NapCat 与 Bot 的 Token 当前统一为空字符串，避免出现一边启用 Token、另一边没有 Token 的半配置状态。以后如果增加 Token 支持，再统一引入 `ONEBOT_ACCESS_TOKEN`。

## AI 配置持久化

Docker 正式环境将管理后台配置保存到：

```text
data/app/app-config.env
```

该文件由管理后台维护并通过 Docker volume 持久化，不需要把生产 API Key 提交到 Git。Compose 的初始环境变量只作为首次启动默认值。Docker Compose 的 `env_file` 用于向容器注入环境变量，具体优先级以 Compose 规则为准。参考 [Docker Compose 环境变量文档](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)。

## 健康检查

```text
GET /health
```

会返回：

- Bot 状态
- OneBot 连接状态
- QQ 在线状态（NapCat/OneBot 可提供时）
- 最近 QQ 消息时间
- 最近错误摘要

Docker Compose 还会对 NapCat 和 QQ-AI-Bot 分别执行 healthcheck。

## 重要规则

1. 不提交 `.env`、API Key、QQ 登录数据。
2. Windows 本地测试和 VPS 正式环境必须保持隔离。
3. 最终只运行一个 QQ-AI-Bot 实例，避免重复回复。
4. AI 单次请求失败不能导致 Bot 或管理后台退出。
5. OneBot 断线不能导致管理后台退出。
6. 新增 Docker/Linux 能力不得破坏 Windows 本地运行。

## 当前验证状态

Windows 本地开发/测试已经验证。Linux/VPS 24 小时无人值守能力正在针对以下问题做专项实测：

- OneBot 3001 自动配置
- QQ 登录态持久化
- NapCat 重启后的自动恢复
- OneBot 断线自动重连
- AI API 异常隔离
- 管理后台配置持久化

在完成真实 VPS 长时间测试前，不把“QQ 永不掉线”描述成已经保证的功能。
