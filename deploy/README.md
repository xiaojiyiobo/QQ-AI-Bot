# Linux VPS + Docker Compose 部署

## 一键部署

```bash
cp .env.example .env
mkdir -p data/app data/napcat/config data/napcat/QQ
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

部署脚本会串行执行：

1. 防重复部署锁 `/tmp/qq-ai-bot-deploy.lock`
2. Compose 配置校验
3. 镜像拉取
4. QQ-AI-Bot 构建
5. Compose 启动
6. 8080 / 6099 / OneBot 3001 基础检查

## 服务关系

```text
浏览器 / 手机
  ├─ http://VPS公网IP:8080/admin/
  └─ http://VPS公网IP:6099/webui/

Docker Compose
  ├─ napcat
  │   ├─ QQ
  │   └─ OneBot WebSocket :3001
  └─ qq-ai-bot
      └─ ws://napcat:3001
```

3001 **不会映射到 VPS 公网**。8080 和 6099 才是给外部浏览器访问的端口。

## OneBot 自动配置

首次部署脚本会把仓库中的：

```text
deploy/napcat/onebot11.json
```

复制到：

```text
data/napcat/config/onebot11.json
```

其中已经固定：

- Name：`QQ-AI-BOT`
- Enable：`true`
- Host：`0.0.0.0`
- Port：`3001`
- Message format：`array`
- Report self message：`false`
- Force push event：`true`
- Token：空字符串
- Heartbeat：30000ms

只有第一次部署时复制；如果配置已经存在，不会覆盖用户现有配置。

## QQ 登录与持久化

NapCat 数据目录：

```text
data/napcat/QQ
data/napcat/config
```

首次启动打开 NapCat WebUI 完成 QQ 扫码登录。之后 Docker / Compose / VPS 重启会复用这些数据。`NAPCAT_ACCOUNT` 可以在 `.env` 中填写 QQ 号，用于 NapCat 的账号启动参数；留空时仍可通过 WebUI 扫码登录。

注意：Docker 持久化只能保证本地登录数据被保存，不能保证 QQ 服务端永远不会要求重新验证。ErrCode 3 的长期恢复能力必须通过真实 VPS 长时间运行测试确认。

## AI 配置

管理后台：

```text
http://VPS公网IP:8080/admin/
```

可以配置：

- Gemini / Mistral
- API Key
- 模型
- 保存
- 保存并重启 Bot

生产配置持久化在：

```text
data/app/app-config.env
```

真实 API Key 不会显示在页面，也不要提交到 Git。

## Windows 本地开发

Windows 仍然使用原来的 `run.bat`，默认管理页面：

```text
http://127.0.0.1:8080/admin/
```

Linux/VPS Compose 的 8080 / 6099 公网发布不会修改 Windows 本地行为。
