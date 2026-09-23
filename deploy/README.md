# Linux VPS + Docker Compose 部署

> 当前文档用于正式环境实测。Windows 本地开发环境不受影响。

## 目标结构

```text
浏览器
  │
  ├── SSH 隧道 → 127.0.0.1:8080 → QQ-AI-Bot 管理后台
  │                                  │
  │                                  └── NapCat WebUI
  │
  └── SSH 隧道 → 127.0.0.1:6099 → NapCat

Docker Compose
  ├── qq-ai-bot
  │     └── ws://napcat:3001
  └── napcat
        ├── QQ 持久化数据
        └── NapCat WebUI / OneBot WebSocket
```

NapCat 官方 Docker 项目提供 WebUI（默认 6099）和 QQ 数据持久化目录；官方也提供 NapCat + qq-ai-bot 的 Compose 示例。

## 首次部署

1. 准备 Linux VPS，并安装 Docker Engine 与 Docker Compose。
2. 克隆本仓库。
3. 复制 `.env.example` 为 `.env`。
4. 在 `.env` 中填写 AI API Key 和需要的模型配置。
5. 执行：

```bash
docker compose up -d --build
```

6. 通过 SSH 隧道访问本机管理后台 `127.0.0.1:8080`。
7. 打开管理页面的“QQ 登录”，进入 NapCat WebUI。
8. 使用手机 QQ 扫码完成首次 QQ 登录。
9. 登录成功后，NapCat 的 QQ 数据保存在 `data/napcat/QQ`，后续重启可复用持久化数据。NapCat 官方文档说明 QQ 数据可持久化，WebUI 默认端口为 6099。

## 为什么 Bot 连接 `napcat:3001`

当前 QQ-AI-Bot 使用 OneBot WebSocket 客户端主动连接 NapCat 的 WebSocket 服务端。Docker Compose 中两个服务位于同一网络，因此 Bot 使用服务名 `napcat` 连接容器内部 3001 端口，而不是依赖 `127.0.0.1`。NapCat 官方安装脚本也将 `ws` 模式配置为 3001 WebSocket 服务。

## 安全边界

当前 Compose 将管理后台 8080 和 NapCat WebUI 6099 都只绑定到 VPS 的 `127.0.0.1`，不直接暴露公网。远程访问应通过 SSH 隧道或之后增加经过身份验证的 HTTPS 反向代理。NapCat 官方文档明确提醒公网环境要注意 6099 WebUI。

## 后续

正式环境验证通过后，再补充一键安装、反向代理/HTTPS、管理后台认证以及备份恢复流程。
