# 基金播客项目 - 快速启动指南

## 项目概览

一个将基金季报转化为AI播客的Web应用，让投资者通过收听轻松了解基金经理观点。

**核心功能：**
- 搜索并添加自选基金
- 自动获取季报并AI解读
- 双人对话式播客 + 文字稿
- 移动端友好的音频播放

---

## 开发环境搭建

### 1. 克隆项目并安装依赖

```bash
# 克隆项目
git clone <repo-url>
cd fund-podcast

# 安装Python依赖
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# 安装Node依赖
cd frontend
npm install
```

### 2. 配置环境变量

```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/fundpodcast
REDIS_URL=redis://localhost:6379/0
DEEPSEEK_API_KEY=your_deepseek_api_key
TTS_API_KEY=your_tts_api_key
SECRET_KEY=your_jwt_secret
```

### 3. 启动数据库

```bash
# 使用Docker启动PostgreSQL和Redis
docker-compose up -d

# 初始化数据库
cd backend
alembic upgrade head
python scripts/seed_funds.py  # 导入基金基础数据
```

### 4. 启动开发服务器

```bash
# 终端1: 启动后端API
cd backend
uvicorn app.main:app --reload --port 8000

# 终端2: 启动Celery Worker
celery -A app.tasks worker --loglevel=info

# 终端3: 启动Celery Beat（定时任务）
celery -A app.tasks beat --loglevel=info

# 终端4: 启动前端
cd frontend
npm run dev
```

访问 http://localhost:3000 查看应用

---

## MVP开发路线图

### Week 1: 基础架构（2-3天）

**Day 1-2: 后端基础**
- [ ] 搭建FastAPI项目结构
- [ ] 配置PostgreSQL + SQLModel
- [ ] 基金数据模型 + 基础CRUD
- [ ] 集成AKShare获取基金列表

**Day 3: 前端基础**
- [ ] Next.js项目初始化
- [ ] 配置Tailwind CSS
- [ ] 基础布局（导航栏、底部播放器占位）
- [ ] API客户端封装

### Week 2: 核心功能（4-5天）

**Day 4-5: 基金搜索与自选**
- [ ] 基金搜索API + 前端搜索页
- [ ] 基金卡片组件
- [ ] 自选基金API（增删改查）
- [ ] 用户自选列表页

**Day 6-7: 播客列表**
- [ ] 播客数据模型
- [ ] 播客列表API + 页面
- [ ] 播客卡片组件（含状态标签）
- [ ] 空状态/加载状态

**Day 8-9: AI播客生成**
- [ ] 季报PDF下载解析
- [ ] DeepSeek API集成
- [ ] Celery异步任务
- [ ] 生成进度状态更新

### Week 3: 音频与播放（3-4天）

**Day 10-11: TTS音频生成**
- [ ] TTS服务集成（Azure/讯飞）
- [ ] 音频合并与上传OSS
- [ ] 音频时长计算

**Day 12-13: 播放器开发**
- [ ] Web Audio API封装
- [ ] 底部播放器组件
- [ ] 播放/暂停/进度条/倍速
- [ ] 播放列表管理

**Day 14: 文字稿**
- [ ] 文字稿展示组件
- [ ] 播放时高亮当前句
- [ ] 点击跳转播放位置

### Week 4: 优化与上线（2-3天）

**Day 15-16: 完善功能**
- [ ] AI摘要生成
- [ ] 基金详情页
- [ ] 用户登录（简单手机号）
- [ ] 响应式适配优化

**Day 17-18: 部署上线**
- [ ] 生产环境配置
- [ ] Docker镜像构建
- [ ] 云服务器部署
- [ ] 域名配置 + HTTPS

---

## 目录结构

```
fund-podcast/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI入口
│   │   ├── config.py          # 配置管理
│   │   ├── models/            # SQLModel模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── fund.py
│   │   │   └── podcast.py
│   │   ├── routers/           # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── funds.py
│   │   │   ├── podcasts.py
│   │   │   └── user.py
│   │   ├── services/          # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── fund_service.py
│   │   │   ├── podcast_service.py
│   │   │   ├── ai_service.py       # DeepSeek
│   │   │   └── tts_service.py      # 语音合成
│   │   ├── tasks.py           # Celery任务
│   │   └── dependencies.py    # FastAPI依赖
│   ├── alembic/               # 数据库迁移
│   ├── scripts/               # 脚本工具
│   ├── tests/                 # 测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js前端
│   ├── app/
│   │   ├── (main)/           # 主布局组
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── search/
│   │   │   └── fund/
│   │   └── layout.tsx
│   ├── components/
│   │   ├── player/
│   │   ├── podcast/
│   │   ├── fund/
│   │   └── ui/
│   ├── hooks/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docs/                      # 文档
│   ├── PRD.md
│   └── TechSpec.md
├── docker-compose.yml
└── README.md
```

---

## API密钥获取

### 1. DeepSeek API
```bash
# 访问 https://platform.deepseek.com/
# 注册账号 → 创建API Key
# 价格：输入¥0.001/1K tokens，输出¥0.002/1K tokens
```

### 2. TTS服务选择

**方案A: Azure TTS（推荐）**
```bash
# 访问 https://azure.microsoft.com/
# 创建Speech服务 → 获取Key和Region
# 价格：约¥0.7/千字符
# 优点：中文语音自然，有多种音色
```

**方案B: 科大讯飞**
```bash
# 访问 https://www.xfyun.cn/
# 注册开发者账号 → 创建应用
# 价格：有免费额度（约500次/天）
# 优点：国内服务稳定
```

**方案C: Edge TTS（免费）**
```bash
# 无需API Key
# 使用edge-tts库
# 优点：完全免费
# 缺点：不适合生产环境
```

---

## 测试数据

### 热门基金列表（测试用）
```json
[
  {"code": "005827", "name": "易方达蓝筹精选混合", "manager": "张坤"},
  {"code": "003095", "name": "中欧医疗健康混合A", "manager": "葛兰"},
  {"code": "161725", "name": "招商中证白酒指数", "manager": "侯昊"},
  {"code": "110022", "name": "易方达消费行业股票", "manager": "萧楠"},
  {"code": "000083", "name": "汇添富消费行业混合", "manager": "胡昕炜"}
]
```

---

## 常见问题

### Q: 季报PDF从哪里获取？
A: 使用AKShare获取公告列表，解析PDF链接下载。部分基金可能需要从天天基金、巨潮资讯网获取。

### Q: 生成一个播客需要多长时间？
A: 大概1-3分钟：
- PDF下载解析：10-20秒
- AI脚本生成：30-60秒
- TTS音频生成：30-90秒（取决于字数）

### Q: 如何降低AI成本？
A: 
1. 精简Prompt，只传核心观点
2. 缓存已生成的内容
3. 限制单用户同时生成数量
4. 使用DeepSeek而非Claude

### Q: 音频文件存储在哪里？
A: 推荐使用对象存储（阿里云OSS、腾讯云COS），便宜且带CDN加速。

---

## 下一步

1. **完成Week 1任务** → 搭建基础框架
2. **实现基金搜索** → 让用户能找到基金
3. **跑通AI生成** → 验证核心逻辑
4. **上线MVP** → 收集用户反馈

有问题随时交流！
