# 洋洋 · 技术博客

FastAPI + 静态前端，支持 Windows / Linux 部署。

## 一键启动（推荐）

```bash
cd elphant-route
python3 start_site.py
```

或 Linux：

```bash
chmod +x start_site.sh
./start_site.sh
```

Windows：双击 `start_site.bat` 或 `python start_site.py`。

**一条命令会自动完成：**

1. 使用 `.venv`（若存在）或当前 Python  
2. `pip install` 安装 `backend/requirements.txt`（缺依赖时）  
3. 从 `产品示例视频/` 复制演示 MP4，并用 ffmpeg 做 **faststart**（支持拖拽进度）  
4. 启动 uvicorn（Linux 默认 `0.0.0.0:8000`，生产关闭热重载）

浏览器访问：`http://服务器IP:8000`

**演示视频**：`start_site.py` 会从上级目录 `产品示例视频/` 自动复制到 `frontend/assets/videos/`。每次启动后会更新 **`frontend/assets/videos/资源同步记录.md`**。若只同步视频、不启动服务：

```bash
python3 scripts/sync_videos.py
```

**推送到 GitHub**（仓库 [2029203568/-](https://github.com/2029203568/-)）：

```bash
python scripts/push_to_github.py -m "更新项目"
# 需 Token 时:
# PowerShell: $env:GITHUB_TOKEN="ghp_xxxx"
# Linux: export GITHUB_TOKEN=ghp_xxxx
```

**交付脚本**：启动时也会从上级目录同步案例脚本（如 `抖音评论区获客.py`、`抖音私信获客.py`）到 `frontend/assets/code/`。仅同步脚本：

```bash
python3 scripts/sync_code.py
```

> 服务器部署时通常没有 `产品示例视频/` 目录，需把 MP4 直接上传到 `frontend/assets/videos/`，或在本地先跑 `sync_videos.py` 再整体上传项目。

### 可选环境变量

| 变量 | 说明 | 默认 |
|------|------|------|
| `HOST` | 监听地址 | Linux `0.0.0.0`，Windows `127.0.0.1` |
| `PORT` | 端口 | `8000` |
| `RELOAD` | 热重载 `1`/`0` | Linux `0` |
| `SKIP_DEPS` | `1` 跳过 pip 安装 | - |
| `SKIP_VIDEO_SETUP` | `1` 跳过视频复制/转码 | - |
| `TRANSCODE_HLS` | `1` 完整 HLS 转码（首部署较慢） | - |
| `AUTO_HLS` | `1` 且无 HLS 时自动转码（Linux） | - |
| `CREATE_VENV` | `1` 自动创建 `.venv` | - |
| `ADMIN_USERNAME` | 统计后台登录账号 | `admin` |
| `ADMIN_PASSWORD` | 统计后台登录密码 | 见 `backend/auth.py` 默认值 |
| `ADMIN_SECRET` | 会话签名密钥（生产务必修改） | 自动生成到 `backend/logs/.admin_secret` |
| `ADMIN_SESSION_HOURS` | 登录会话有效期（小时） | `168` |

首次需要 HLS 自适应码流时：

```bash
TRANSCODE_HLS=1 python3 start_site.py
```

## Linux + natapp 内网穿透

1. 在 [natapp.cn](https://natapp.cn) 后台将隧道 **本地端口** 设为 `8000`
2. `export NATAPP_AUTHTOKEN=你的token` 后执行 `./start_natapp.sh`

## 宝塔 Nginx 反代

若前面有 Nginx，视频 Range 需正确配置，见 `deploy/nginx-baota.example.conf`。

启动后自检：

```bash
python3 scripts/check_video_streaming.py --url http://127.0.0.1:8000/assets/videos/facebook-yanghao.mp4
```

应看到 `Accept-Ranges: bytes` 与 Range 请求 `206`。

## 浏览进度

前端自动采集滚动深度、区块曝光、视频播放进度等，写入 `backend/logs/progress.json`（与 `visits.json` 一样不提交 git）。

**统计查询需登录**（访客上报 `POST /api/progress` 仍公开，无需登录）。

| 地址 | 说明 |
|------|------|
| `/admin/login` | 管理后台登录页（Elephant Route 风格） |
| `/progress-dashboard` | 统计展示页（登录后访问） |
| `GET /api/progress` | 最近浏览会话 JSON（需登录） |
| `GET /api/progress/stats` | 汇总统计 API（需登录） |
| `POST /api/progress` | 访客进度上报（公开） |

默认账号已写在 `backend/auth.py`；如需覆盖可设置 `ADMIN_USERNAME`、`ADMIN_PASSWORD` 环境变量。
默认账号密码为admin

命令行统计：

```bash
python3 scripts/stats_progress.py
python3 scripts/stats_progress.py --json
```

## 手动安装（可选）

仅需虚拟环境时：`./install.sh`，之后仍用 `python3 start_site.py` 启动即可。
