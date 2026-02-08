# 基金播客 MVP 部署与配置指南

本指南聚焦 MVP 版本的部署与配置，覆盖本地运行、配置项说明、部署到 Render/Vercel 的建议方案。

## 1. 项目结构速览

```
fund-report/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── requirements.txt
│   ├── data/
│   │   └── funds.db
│   └── services/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
└── README-MVP.md
```

## 2. 本地运行（推荐先验证）

### 2.1 后端

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 main.py
```

默认地址：`http://localhost:8000`

### 2.2 前端

```bash
cd frontend
npm install
npm run dev
```

默认地址：`http://localhost:3000`

## 3. 配置说明

后端支持从 `backend/.env` 自动读取配置（如果存在）。

### 3.1 必需或推荐配置

| 配置项 | 说明 | 示例 |
| --- | --- | --- |
| ARK_API_KEY | ARK OpenAI 兼容接口 Key | `ARK_API_KEY=xxx` |
| ARK_MODEL | 模型 ID（可选） | `ARK_MODEL=ep-20260208171328-jgc8q` |

### 3.2 可选依赖

| 依赖 | 用途 | 说明 |
| --- | --- | --- |
| akshare | 获取基金公告列表 | 用于真实季报下载 |
| pdfplumber | 解析 PDF 文本 | 提取季报内容 |
| pydub | 拼接音频 | 生成完整播客 |
| ffmpeg | 音频拼接备用方案 | 系统级工具 |

## 4. 运行机制与落盘路径

- SQLite 数据库：`backend/data/funds.db`
- 真实季报缓存：`backend/data/reports/<fund_code>/`
- 音频输出：`backend/audio/`，通过 `/audio` 静态路径访问

## 5. 部署建议（MVP）

### 5.1 后端部署（Render）

建议作为单体服务部署（FastAPI 单进程，SQLite 文件落盘）。

- **Build Command**
  ```bash
  pip install -r backend/requirements.txt
  ```
- **Start Command**
  ```bash
  python backend/main.py
  ```
- **环境变量**
  - `ARK_API_KEY`
  - `ARK_MODEL`（可选）

**注意事项**
- Render 免费版可能休眠，首次访问需唤醒
- SQLite 文件随实例存储，重启或迁移可能导致数据丢失（MVP 可接受）

### 5.2 前端部署（Vercel）

在 Vercel 导入仓库，设置如下：

- **Framework Preset**：Next.js
- **Root Directory**：`frontend`
- **Build Command**
  ```bash
  npm run build
  ```
- **Output Directory**：`.next`

## 6. 常见问题

### 6.1 无法生成音频？
- 确认 Edge TTS 依赖可用
- 若未安装 `pydub` 或 `ffmpeg`，会退化为首段音频复制

### 6.2 真实季报下载失败？
- AKShare 数据源不稳定时会回退到内置样例文本
- 部分公告链接不是直接 PDF，可能导致下载失败

### 6.3 API 返回 401？
- 检查 `ARK_API_KEY` 是否正确
- 确保 `base_url` 为 `https://ark.cn-beijing.volces.com/api/v3`

## 7. 建议的上线前检查

- 后端 `/api/funds/search`、`/api/podcasts/generate` 可用
- 前端列表页可正常添加基金并触发生成
- 播客详情页可播放音频并展示文字稿
