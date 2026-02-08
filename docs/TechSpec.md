# 基金播客 - 技术实现文档

## 1. 技术架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web App    │  │    H5        │  │   小程序     │      │
│  │  (Next.js)   │  │  (响应式)     │  │  (Taro)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                        API网关层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Nginx      │  │  Rate Limit  │  │    Auth      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       后端服务层                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Server  │  │ Async Worker │  │  Scheduler   │      │
│  │  (FastAPI)   │  │   (Celery)   │  │  (APScheduler)│     │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Redis     │  │ Object Store │      │
│  │  (主数据库)   │  │  (缓存/队列)  │  │  (音频文件)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       外部服务                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   AKShare    │  │  DeepSeek    │  │  TTS服务     │      │
│  │ (基金数据)   │  │  (AI生成)    │  │(Azure/讯飞)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈选择

| 层级 | 技术 | 选择理由 |
|-----|------|---------|
| 前端 | Next.js 14 | SSR优化SEO，API Routes简化架构 |
| 后端 | FastAPI | Python生态，异步高性能 |
| 数据库 | PostgreSQL | 关系型数据，JSONB存储播客内容 |
| 缓存 | Redis | 热点数据、生成队列 |
| 对象存储 | MinIO/阿里云OSS | 音频文件存储 |
| 任务队列 | Celery + Redis | 异步处理播客生成 |
| AI模型 | DeepSeek API | 成本低，中文强 |

---

## 2. 数据库设计

### 2.1 ER图

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│    users     │       │  user_funds  │       │    funds     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │──┐    │ id (PK)      │──┐    │ code (PK)    │
│ phone        │  │    │ user_id (FK) │  └──▶│ name         │
│ created_at   │  └──▶│ fund_code(FK)│       │ manager      │
└──────────────┘       │ created_at   │       │ company      │
                       └──────────────┘       │ type         │
                                              │ logo_url     │
                                              └──────────────┘
                                                     │
                       ┌──────────────┐            │
                       │   podcasts   │◀───────────┘
                       ├──────────────┤
                       │ id (PK)      │
                       │ fund_code(FK)│
                       │ report_period│
                       │ title        │
                       │ audio_url    │
                       │ transcript   │  -- JSONB
                       │ duration     │
                       │ summary      │  -- JSONB
                       │ status       │  -- pending/generated/failed
                       │ created_at   │
                       └──────────────┘
```

### 2.2 表结构详细定义

```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    nickname VARCHAR(50),
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 基金基础信息表
CREATE TABLE funds (
    code VARCHAR(20) PRIMARY KEY,  -- 如: 005827
    name VARCHAR(100) NOT NULL,     -- 如: 易方达蓝筹精选混合
    name_py VARCHAR(100),           -- 拼音，用于搜索
    manager VARCHAR(50),            -- 基金经理
    company VARCHAR(100),           -- 基金公司
    fund_type VARCHAR(50),          -- 基金类型
    logo_url VARCHAR(255),
    last_report_date DATE,          -- 最新季报日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户自选基金关联表
CREATE TABLE user_funds (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    fund_code VARCHAR(20) REFERENCES funds(code) ON DELETE CASCADE,
    notify_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, fund_code)
);

-- 播客内容表
CREATE TABLE podcasts (
    id SERIAL PRIMARY KEY,
    fund_code VARCHAR(20) REFERENCES funds(code),
    report_period VARCHAR(10) NOT NULL,  -- 如: 2024Q4
    title VARCHAR(200) NOT NULL,
    audio_url VARCHAR(500),
    duration INTEGER,  -- 秒
    transcript JSONB,  -- [{time: 0, speaker: '小明', text: '...'}, ...]
    summary JSONB,     -- ['要点1', '要点2', '要点3']
    ai_script TEXT,    -- 原始AI生成的脚本
    status VARCHAR(20) DEFAULT 'pending',  -- pending/generating/completed/failed
    error_msg TEXT,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fund_code, report_period)
);

-- 创建索引
CREATE INDEX idx_user_funds_user_id ON user_funds(user_id);
CREATE INDEX idx_podcasts_fund_code ON podcasts(fund_code);
CREATE INDEX idx_podcasts_status ON podcasts(status);
CREATE INDEX idx_funds_name_py ON funds USING gin(name_py gin_trgm_ops);
```

---

## 3. API 设计

### 3.1 RESTful API 列表

#### 用户相关
```
POST   /api/v1/auth/login         # 手机号登录
POST   /api/v1/auth/verify-code   # 发送验证码
GET    /api/v1/user/profile       # 获取用户信息
PUT    /api/v1/user/profile       # 更新用户信息
```

#### 基金相关
```
GET    /api/v1/funds/search?q=...&page=1&size=20    # 搜索基金
GET    /api/v1/funds/:code                          # 基金详情
GET    /api/v1/funds/hot                            # 热门基金
```

#### 自选基金
```
GET    /api/v1/user/funds             # 获取自选列表
POST   /api/v1/user/funds             # 添加自选 {fund_code}
DELETE /api/v1/user/funds/:code       # 移除自选
PUT    /api/v1/user/funds/:code/notify # 开关通知
```

#### 播客相关
```
GET    /api/v1/podcasts?fund_code=...&page=1&size=20   # 播客列表
GET    /api/v1/podcasts/:id                            # 播客详情
GET    /api/v1/podcasts/:id/transcript                 # 获取文字稿
POST   /api/v1/podcasts/:id/generate                   # 手动触发生成
GET    /api/v1/podcasts/:id/stream                     # 音频流播放
```

### 3.2 关键API详细说明

#### GET /api/v1/podcasts - 播客列表

**Request:**
```http
GET /api/v1/podcasts?page=1&size=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 25,
    "page": 1,
    "size": 10,
    "list": [
      {
        "id": 1,
        "fund_code": "005827",
        "fund_name": "易方达蓝筹精选混合",
        "fund_manager": "张坤",
        "report_period": "2024Q4",
        "title": "易方达蓝筹精选2024Q4季报解读",
        "duration": 325,
        "duration_text": "05:25",
        "audio_url": "https://cdn.example.com/audio/podcast_1.mp3",
        "summary": [
          "维持高仓位，重点配置消费医药",
          "看好长期价值，当前估值处于低位",
          "适度调整持仓，保持长期持有"
        ],
        "status": "completed",
        "created_at": "2025-01-15T10:30:00Z",
        "is_new": true
      }
    ]
  }
}
```

#### POST /api/v1/podcasts/:id/generate - 触发生成

**Request:**
```http
POST /api/v1/podcasts/1/generate
Authorization: Bearer <token>
```

**Response:**
```json
{
  "code": 0,
  "message": "任务已加入队列",
  "data": {
    "task_id": "task_abc123",
    "status": "pending",
    "estimated_time": 60
  }
}
```

---

## 4. 核心业务逻辑

### 4.1 播客生成流程

```python
# 伪代码展示核心流程

class PodcastGenerator:
    
    async def generate(self, fund_code: str, report_period: str):
        """播客生成主流程"""
        
        # 1. 检查是否已生成
        if await self.check_exists(fund_code, report_period):
            return {"status": "exists", "podcast_id": ...}
        
        # 2. 创建任务记录
        task = await self.create_task(fund_code, report_period)
        
        # 3. 提交异步任务
        celery_app.send_task(
            'generate_podcast',
            args=[task.id, fund_code, report_period]
        )
        
        return {"status": "queued", "task_id": task.id}


@celery_app.task(bind=True, max_retries=3)
def generate_podcast(self, task_id: int, fund_code: str, report_period: str):
    """Celery异步任务"""
    
    try:
        # 1. 下载并解析PDF
        pdf_text = download_and_parse_pdf(fund_code, report_period)
        viewpoint = extract_manager_viewpoint(pdf_text)
        
        # 2. AI生成对话脚本
        script = generate_ai_script(viewpoint, fund_code, report_period)
        
        # 3. 拆分为对话片段
        dialogues = split_dialogue(script)
        
        # 4. TTS生成音频（按角色）
        audio_segments = []
        for dialogue in dialogues:
            audio = generate_tts(
                text=dialogue['text'],
                voice='male' if dialogue['speaker'] == '小明' else 'female'
            )
            audio_segments.append(audio)
        
        # 5. 合并音频
        final_audio = merge_audio(audio_segments)
        audio_url = upload_to_storage(final_audio)
        
        # 6. 生成摘要
        summary = generate_summary(script)
        
        # 7. 更新数据库
        update_podcast(task_id, {
            'status': 'completed',
            'audio_url': audio_url,
            'transcript': dialogues,
            'summary': summary,
            'duration': calculate_duration(final_audio)
        })
        
        # 8. 推送通知
        notify_users(fund_code, report_period)
        
    except Exception as e:
        logger.error(f"生成失败: {e}")
        update_podcast(task_id, {
            'status': 'failed',
            'error_msg': str(e)
        })
        raise self.retry(exc=e, countdown=60)
```

### 4.2 AI Prompt设计

```python
PODCAST_PROMPT = """
你是专业的基金播客主持人。请将以下基金经理的季报观点转换为双人播客对话。

【角色设定】
- 小明：男主持人，金融专业背景，说话幽默风趣，擅长用比喻解释专业概念
- 小红：女嘉宾，普通投资者视角，会提出小白用户关心的问题

【输入内容】
基金：{fund_name}（{fund_code}）
基金经理：{manager_name}
报告期：{report_period}

基金经理观点：
{viewpoint}

【输出要求】
1. 对话自然流畅，有轻松的开场和结尾
2. 小红要提3-5个关键问题，小明用通俗易懂的方式解答
3. 适当使用比喻和生活化的例子
4. 控制在800-1200字
5. 格式：【小明】对话内容\n【小红】对话内容

【注意事项】
- 不要照读原文，要解读和扩展
- 风险提示：AI解读仅供参考，不构成投资建议
- 语气友好，像朋友聊天
"""
```

---

## 5. 前端实现

### 5.1 项目结构

```
frontend/
├── app/                       # Next.js App Router
│   ├── (main)/               # 主布局组
│   │   ├── layout.tsx        # 主布局（含底部播放器）
│   │   ├── page.tsx          # 首页-播客列表
│   │   ├── search/
│   │   │   └── page.tsx      # 搜索页
│   │   └── fund/
│   │       └── [code]/
│   │           └── page.tsx  # 基金详情
│   ├── api/                  # API Routes（可选）
│   └── layout.tsx            # 根布局
├── components/               # 组件
│   ├── player/              # 播放器组件
│   │   ├── AudioPlayer.tsx
│   │   ├── ProgressBar.tsx
│   │   └── Playlist.tsx
│   ├── podcast/
│   │   ├── PodcastCard.tsx
│   │   ├── PodcastList.tsx
│   │   └── Transcript.tsx
│   ├── fund/
│   │   ├── FundCard.tsx
│   │   └── SearchBox.tsx
│   └── ui/                  # 基础UI组件
├── hooks/                   # 自定义Hooks
│   ├── useAudio.ts         # 音频播放逻辑
│   ├── usePodcast.ts       # 播客数据获取
│   └── useSearch.ts        # 搜索逻辑
├── lib/                     # 工具函数
│   ├── api.ts              # API客户端
│   └── utils.ts
├── types/                   # TypeScript类型
│   └── index.ts
└── public/                  # 静态资源
```

### 5.2 关键组件示例

#### 底部播放器组件
```tsx
// components/player/AudioPlayer.tsx
'use client';

import { useAudio } from '@/hooks/useAudio';
import { ProgressBar } from './ProgressBar';

export function AudioPlayer() {
  const { 
    currentPodcast, 
    isPlaying, 
    currentTime, 
    duration,
    play, 
    pause, 
    seek,
    playbackRate,
    setPlaybackRate 
  } = useAudio();

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg">
      <ProgressBar 
        current={currentTime} 
        total={duration} 
        onSeek={seek} 
      />
      <div className="flex items-center px-4 py-3">
        {/* 当前播客信息 */}
        <div className="flex-1">
          <h4 className="font-medium truncate">{currentPodcast?.title}</h4>
          <p className="text-sm text-gray-500">
            {currentPodcast?.fund_manager}
          </p>
        </div>
        
        {/* 控制按钮 */}
        <div className="flex items-center gap-4">
          <button onClick={() => setPlaybackRate(rate => rate === 1 ? 1.5 : 1)}>
            {playbackRate}x
          </button>
          <button onClick={() => isPlaying ? pause() : play()}>
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 6. 部署方案

### 6.1 开发环境
```bash
# 本地开发
docker-compose up -d  # 启动PostgreSQL、Redis

# 后端
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 6.2 生产环境

**推荐配置：**
- **服务器**: 2核4G云服务器（约￥200/月）
- **数据库**: 阿里云RDS PostgreSQL（约￥100/月）
- **对象存储**: 阿里云OSS（按量计费，约￥50/月）
- **CDN**: 音频文件加速（约￥30/月）

**Docker部署：**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  web:
    build: ./frontend
    ports:
      - "3000:3000"
  
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
  
  worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info --concurrency=2
  
  scheduler:
    build: ./backend
    command: celery -A tasks beat --loglevel=info
```

---

## 7. 成本估算

### 7.1 月度运营成本（1000活跃用户）

| 项目 | 费用 | 说明 |
|-----|------|------|
| 服务器 | ¥200 | 2核4G + 100G存储 |
| 数据库 | ¥100 | RDS PostgreSQL |
| 对象存储 | ¥50 | 音频文件（约50G）|
| CDN | ¥30 | 音频加速 |
| DeepSeek API | ¥50 | 约2万条请求 |
| TTS服务 | ¥100 | 约1000分钟音频 |
| **总计** | **¥530/月** | |

### 7.2 规模化成本

| 用户规模 | 月成本 | 单用户成本 |
|---------|--------|-----------|
| 1,000 | ¥530 | ¥0.53 |
| 10,000 | ¥2,000 | ¥0.20 |
| 50,000 | ¥8,000 | ¥0.16 |

---

## 8. 监控与运维

### 8.1 日志收集
```python
# 结构化日志
import structlog

logger = structlog.get_logger()

logger.info(
    "播客生成完成",
    fund_code="005827",
    report_period="2024Q4",
    duration=325,
    cost_ms=45000
)
```

### 8.2 关键指标监控
- API响应时间（P95 < 500ms）
- 播客生成成功率（> 95%）
- AI API调用成本（每日/每月）
- 用户留存率（7日/30日）

### 8.3 告警规则
- 播客生成失败率 > 10%
- API响应时间 P95 > 2s
- 数据库连接数 > 80%
- 磁盘使用率 > 85%

---

## 9. 安全考虑

### 9.1 防护措施
- **API限流**: 每IP 100次/分钟
- **认证**: JWT Token，有效期7天
- **SQL注入**: 使用ORM参数化查询
- **XSS**: 前端输入过滤，后端输出转义

### 9.2 数据保护
- 用户手机号脱敏存储
- API传输使用HTTPS
- 数据库定期备份（每日）
- 敏感配置使用环境变量
