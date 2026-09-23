# Linux VPS + Docker Compose 部署

> 当前文档用于正式环境实测。Windows 本地开发环境不受影响。

## 目标结构

浏览器 / 手机
  |
  +-- http://VPS公网IP:8080/admin/
  |       +-- QQ-AI-Bot 管理后台
  |
  +-- http://VPS公网IP:6099/webui/
          +-- NapCat WebUI

Docker Compose
  +-- qq-ai-bot
  |    +-- ws://napcat:3001
  +-- napcat
       +-- QQ 持久化数据
       +-- NapCat WebUI / OneBot WebSocket

Docker Compose 中两个服务位于同一网络。QQ-AI-Bot 通过 Docker 内部 DNS 使用 napcat:3001 连接 NapCat 的 OneBot WebSocket，不使用宿主机 127.0.0.1。

## 首次部署

1. 准备 Linux VPS，并安装 Docker Engine 与 Docker Compose。
2. 克隆本仓库。
3. 复制 .env.example 为 .env。
4. 在 .env 中填写 AI API Key 和需要的模型配置。
5. 执行：

docker compose up -d --build

6. 确认 VPS 云厂商安全组 / 防火墙允许 TCP 8080 和 6099。
7. 从外部电脑或手机打开：
   - http://VPS公网IP:8080/admin/
   - http://VPS公网IP:6099/webui/
8. 打开管理页面的“QQ 登录”，进入 NapCat WebUI。
9. 使用手机 QQ 扫码完成首次 QQ 登录。
10. 登录成功后，NapCat 的 QQ 数据保存于 data/napcat/QQ，后续重启可复用持久化数据。

## 为什么 Bot 连接 napcat:3001

当前 QQ-AI-Bot 使用 OneBot WebSocket 客户端主动连接 NapCat WebSocket 服务端。Docker Compose 中两个服务位于同一网络，因此 Bot 使用服务名 napcat 连接容器内部 3001 端口，而不是依赖 127.0.0.1。

6099 和 8080 是宿主机发布端口，仅用于外部浏览器访问；它们不参与 QQ-AI-Bot 与 NapCat 的内部 OneBot 通信。

## 公网访问说明

当前正式 Docker Compose 配置将：

- NapCat WebUI 6099 发布到宿主机所有网络接口；
- QQ-AI-Bot 管理后台 8080 发布到宿主机所有网络接口；
- QQ-AI-Bot 容器内部管理服务继续监听 0.0.0.0:8080；
- QQ-AI-Bot 与 NapCat 继续通过 ws://napcat:3001 通信。

因此，VPS 公网 IP 可直接访问：

http://VPS公网IP:6099/webui/
http://VPS公网IP:8080/admin/

发布端口到宿主机所有接口意味着这些端口可能直接暴露到互联网；Docker 官方文档也明确说明，未指定 host IP 的 published port 默认绑定到所有网络接口。因此正式环境应至少在 VPS 云安全组 / 主机防火墙层面确认只开放需要的端口，并注意 6099 是 NapCat WebUI 管理入口。

本次部署不增加后台账号、密码或额外认证系统；如以后需要更严格的公网访问控制，再单独增加认证或 HTTPS 反向代理。

## Windows 本地开发 / 测试

Windows 本地运行方式保持不变，不因 VPS 的公网端口发布设置而改变。

Windows 本地管理页面仍默认使用：

http://127.0.0.1:8080/admin/

.env.example 中的 127.0.0.1 默认值用于本地运行；Docker Compose 中的生产环境配置会单独覆盖管理服务监听地址及宿主机端口发布方式。

## 持久化

NapCat 配置与 QQ 数据继续使用：

./data/napcat/config
./data/napcat/QQ

本次修改不改变持久化目录、Docker 网络或容器 restart: unless-stopped 策略。

## 后续

后续如需要，再单独补充 HTTPS、管理后台认证、备份恢复等能力。
