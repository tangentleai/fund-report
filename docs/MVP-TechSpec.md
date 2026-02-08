# 基金播客 - MVP技术方案

## 1. 技术架构（极简版）

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   前端          │      │    后端          │      │   外部服务      │
│  Next.js       │◄────►│  FastAPI        │◄────►│  AKShare       │
│  (单页应用)      │      │  (单进程)        │      │  (基金数据)     │
└─────────────────┘      └──────────────────┘      ├─────────────────┤
                                                    │  DeepSeek      │
                                                    │  (AI生成)       │
                                                    ├─────────────────┤
                                                    │  Edge TTS      │
                                                    │  (免费语音)     │
                                                    └─────────────────┘
```

---

## 2. 技术栈

| 模块 | 技术 | 说明 |
|-----|------|------|
| 前端 | Next.js 14 + Tailwind | 单页应用，简单快速 |
| 后端 | FastAPI | Python异步，开发快 |
| 数据 | SQLite | MVP用本地文件，无需部署数据库 |
| AI | DeepSeek API | 成本低，中文好 |
| TTS | Edge TTS | 免费，MVP验证用 |

---

## 3. 项目结构

```
fund-podcast-mvp/
├── backend/
│   ├── main.py              # FastAPI入口
│   ├── database.py          # SQLite操作
│   ├── services/
│   │   ├── fund_service.py      # 基金数据获取
│   │   ├── report_parser.py     # 季报解析（复用已有代码）
│   │   ├── ai_service.py        # DeepSeek API
│   │   └── tts_service.py       # Edge TTS
│   └── data/
│       └── funds.db         # SQLite数据库
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # 主页面（基金列表+搜索）
│   │   ├── podcast/
│   │   │   └── [code]/
│   │   │       └── page.tsx  # 播客播放页
│   │   └── layout.tsx
│   ├── components/
│   │   ├── SearchBox.tsx
│   │   ├── FundCard.tsx
│   │   ├── PodcastPlayer.tsx
│   │   └── Transcript.tsx
│   └── lib/
│       └── api.ts           # API客户端
└── README.md
```

---

## 4. 数据库设计（SQLite简化版）

```sql
-- 基金基础信息
CREATE TABLE funds (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    manager TEXT,
    fund_type TEXT
);

-- 用户基金（用device_id代替user_id）
CREATE TABLE user_funds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,        -- 前端生成的唯一标识
    fund_code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(device_id, fund_code)
);

-- 播客内容
CREATE TABLE podcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_code TEXT NOT NULL,
    report_period TEXT NOT NULL,    -- 如：2024Q4
    title TEXT,
    audio_url TEXT,                 -- 本地文件路径或临时URL
    duration INTEGER,               -- 秒
    transcript TEXT,                -- JSON字符串
    status TEXT DEFAULT 'pending',  -- pending/generating/completed/failed
    error_msg TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, report_period)
);

-- 索引
CREATE INDEX idx_user_funds_device ON user_funds(device_id);
CREATE INDEX idx_podcasts_status ON podcasts(status);
```

---

## 5. API 设计

### 5.1 接口列表

```
GET    /api/funds/search?q=...          # 搜索基金
POST   /api/funds                       # 添加基金 {device_id, fund_code}
GET    /api/funds?device_id=...         # 获取用户基金列表
DELETE /api/funds/:code?device_id=...   # 删除基金

POST   /api/podcasts/generate           # 生成播客 {fund_code}
GET    /api/podcasts/:id                # 获取播客详情
GET    /api/podcasts/:id/status         # 查询生成状态
```

### 5.2 关键接口

#### 搜索基金
```http
GET /api/funds/search?q=易方达

Response:
{
  "data": [
    {"code": "005827", "name": "易方达蓝筹精选混合", "manager": "张坤"}
  ]
}
```

#### 生成播客
```http
POST /api/podcasts/generate
Content-Type: application/json

{
  "fund_code": "005827",
  "device_id": "abc123"
}

Response:
{
  "data": {
    "id": 1,
    "status": "generating",
    "estimated_time": 120
  }
}
```

#### 查询状态
```http
GET /api/podcasts/1/status

Response:
{
  "data": {
    "id": 1,
    "status": "completed",  // pending/generating/completed/failed
    "progress": 100
  }
}
```

---

## 6. 核心逻辑

### 6.1 播客生成流程

```python
# main.py 中的生成接口
@app.post("/api/podcasts/generate")
async def generate_podcast(fund_code: str, device_id: str):
    # 1. 检查是否已存在
    podcast = db.get_podcast(fund_code, "2024Q4")
    if podcast and podcast.status == "completed":
        return {"status": "completed", "podcast": podcast}
    
    # 2. 创建任务记录
    task_id = db.create_podcast_task(fund_code, "2024Q4")
    
    # 3. 后台异步生成（不阻塞请求）
    asyncio.create_task(do_generate(task_id, fund_code))
    
    return {"status": "generating", "task_id": task_id}


async def do_generate(task_id: int, fund_code: str):
    """后台生成任务"""
    try:
        # 1. 获取季报PDF
        pdf_text = await fetch_report_pdf(fund_code)
        
        # 2. 解析观点
        viewpoint = extract_viewpoint(pdf_text)
        
        # 3. AI生成脚本
        script = await generate_script(viewpoint, fund_code)
        
        # 4. TTS生成音频
        audio_path = await generate_audio(script)
        
        # 5. 更新数据库
        db.update_podcast(task_id, {
            "status": "completed",
            "audio_url": audio_path,
            "transcript": parse_script_to_transcript(script)
        })
        
    except Exception as e:
        db.update_podcast(task_id, {
            "status": "failed",
            "error_msg": str(e)
        })
```

---

## 7. 前端实现要点

### 7.1 状态管理（React Hooks）

```typescript
// 使用本地状态管理，无需Redux
const [funds, setFunds] = useState([]);
const [currentPodcast, setCurrentPodcast] = useState(null);
const [isPlaying, setIsPlaying] = useState(false);
```

### 7.2 设备标识

```typescript
// 生成唯一设备ID存储在localStorage
const getDeviceId = () => {
  let id = localStorage.getItem('device_id');
  if (!id) {
    id = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('device_id', id);
  }
  return id;
};
```

### 7.3 轮询生成状态

```typescript
// 生成播客时轮询状态
const checkStatus = async (taskId: string) => {
  const interval = setInterval(async () => {
    const res = await fetch(`/api/podcasts/${taskId}/status`);
    const data = await res.json();
    
    if (data.status === 'completed') {
      clearInterval(interval);
      loadPodcast(data.id);
    } else if (data.status === 'failed') {
      clearInterval(interval);
      alert('生成失败，请重试');
    }
  }, 3000);
};
```

---

## 8. 部署方案

### 8.1 本地开发

```bash
# 1. 启动后端
cd backend
pip install -r requirements.txt
python main.py
# 服务运行在 http://localhost:8000

# 2. 启动前端
cd frontend
npm install
npm run dev
# 服务运行在 http://localhost:3000
```

### 8.2 简单部署（Vercel + Render）

**前端：** Vercel（免费）
- 自动部署，无需配置

**后端：** Render（免费）
- Web Service 免费额度足够MVP
- 配合SQLite（文件存储）

**注意：** Render免费版有休眠，首次访问需等待唤醒

---

## 9. 成本控制

### 月度成本（100用户）

| 项目 | 成本 | 说明 |
|-----|------|------|
| 前端托管 | ¥0 | Vercel免费版 |
| 后端服务器 | ¥0 | Render免费版 |
| DeepSeek API | ¥10-20 | 约500次生成 |
| Edge TTS | ¥0 | 免费 |
| **总计** | **¥10-20** | |

---

## 10. 风险与应对

| 风险 | 概率 | 应对方案 |
|-----|------|---------|
| Edge TTS失效 | 中 | 降级为仅文字稿，提示"音频暂不可用" |
| AKShare失效 | 中 | 准备3个热门基金预生成数据 |
| DeepSeek API超时 | 低 | 设置5分钟超时，失败后可重试 |
| SQLite并发问题 | 低 | MVP用户少，单进程足够 |

---

## 11. 预生成数据

准备3个热门基金的播客，确保AKShare失效时仍有Demo可用：

1. **易方达蓝筹精选**（张坤）- 2024Q4
2. **中欧医疗健康**（葛兰）- 2024Q4  
3. **招商中证白酒**（侯昊）- 2024Q4
