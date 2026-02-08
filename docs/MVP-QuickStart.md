# 基金播客 MVP - 快速启动

## 项目目标
2周内完成MVP，验证AI播客解读季报的产品价值。

---

## 1. 环境准备

```bash
# 克隆项目
git clone <repo-url>
cd fund-podcast-mvp

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装Python依赖
pip install fastapi uvicorn sqlite3 requests edge-tts

# 安装Node依赖
cd frontend
npm install next@14 react react-dom tailwindcss
```

---

## 2. 配置API密钥

```bash
# backend/.env
DEEPSEEK_API_KEY=your_deepseek_api_key
# Edge TTS 无需API Key
```

获取 DeepSeek API Key：
1. 访问 https://platform.deepseek.com/
2. 注册账号 → 创建API Key
3. 价格：¥0.001/千token（约¥0.1/次生成）

---

## 3. 开发步骤

### Day 1-2：后端基础

**任务清单：**
- [ ] 创建 `backend/main.py`，FastAPI基础结构
- [ ] 创建 `backend/database.py`，SQLite操作
- [ ] 复制 `fund_report_parser.py` 到 `backend/services/`
- [ ] 复制 `tts_service.py` 到 `backend/services/`
- [ ] 实现基金搜索API（用预置数据）

**Day 2结束检查点：**
```bash
# 能访问
GET http://localhost:8000/api/funds/search?q=易方达
# 返回基金列表
```

### Day 3-4：播客生成API

**任务清单：**
- [ ] 集成DeepSeek API生成对话脚本
- [ ] 集成Edge TTS生成音频
- [ ] 实现生成状态查询API
- [ ] 测试完整生成流程

**Day 4结束检查点：**
```bash
# 能生成播客
POST http://localhost:8000/api/podcasts/generate
{"fund_code": "005827"}

# 能查询状态
GET http://localhost:8000/api/podcasts/1/status
# 返回 completed 和音频URL
```

### Day 5-7：前端基础

**任务清单：**
- [ ] Next.js项目初始化
- [ ] 基金列表页面
- [ ] 搜索框组件
- [ ] 基金卡片组件（显示生成状态）

**Day 7结束检查点：**
- 能看到基金列表
- 能搜索基金
- 能添加基金到列表

### Day 8-10：播客播放

**任务清单：**
- [ ] 播客播放页
- [ ] 音频播放器组件
- [ ] 文字稿组件
- [ ] 播放时高亮当前文字

**Day 10结束检查点：**
- 能播放音频
- 能看到文字稿
- 能切换倍速

### Day 11-12：集成与测试

**任务清单：**
- [ ] 前后端联调
- [ ] 测试完整流程
- [ ] 预生成3个基金播客
- [ ] 简单样式美化

### Day 13-14：部署与试用

**任务清单：**
- [ ] 部署到 Render + Vercel
- [ ] 邀请10个朋友试用
- [ ] 收集反馈
- [ ] 修复明显问题

---

## 4. 目录结构

```
fund-podcast-mvp/
├── backend/
│   ├── main.py                 # FastAPI入口
│   ├── database.py             # SQLite操作
│   ├── .env                    # API密钥
│   ├── requirements.txt
│   └── services/
│       ├── fund_service.py     # 基金数据
│       ├── report_parser.py    # 解析季报（已有）
│       ├── ai_service.py       # DeepSeek
│       └── tts_service.py      # Edge TTS（已有）
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # 主页面
│   │   ├── podcast/
│   │   │   └── [code]/
│   │   │       └── page.tsx    # 播客播放页
│   │   └── layout.tsx
│   ├── components/
│   │   ├── SearchBox.tsx
│   │   ├── FundCard.tsx
│   │   └── PodcastPlayer.tsx
│   ├── lib/
│   │   └── api.ts
│   └── package.json
└── README.md
```

---

## 5. 关键代码片段

### 5.1 后端：SQLite操作

```python
# database.py 简化版
import sqlite3
import json

DB_PATH = "data/funds.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS funds (
            code TEXT PRIMARY KEY,
            name TEXT,
            manager TEXT
        );
        CREATE TABLE IF NOT EXISTS podcasts (
            id INTEGER PRIMARY KEY,
            fund_code TEXT,
            status TEXT,
            audio_url TEXT,
            transcript TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.close()

def get_podcast(fund_code: str):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT * FROM podcasts WHERE fund_code=? ORDER BY id DESC LIMIT 1",
        (fund_code,)
    ).fetchone()
    conn.close()
    return row
```

### 5.2 前端：API客户端

```typescript
// lib/api.ts
const API_BASE = 'http://localhost:8000/api';

export const api = {
  searchFunds: (q: string) => 
    fetch(`${API_BASE}/funds/search?q=${q}`).then(r => r.json()),
    
  generatePodcast: (fund_code: string, device_id: string) =>
    fetch(`${API_BASE}/podcasts/generate`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({fund_code, device_id})
    }).then(r => r.json()),
    
  getPodcastStatus: (id: string) =>
    fetch(`${API_BASE}/podcasts/${id}/status`).then(r => r.json())
};
```

### 5.3 前端：设备ID生成

```typescript
// hooks/useDeviceId.ts
export const useDeviceId = () => {
  if (typeof window === 'undefined') return null;
  
  let id = localStorage.getItem('device_id');
  if (!id) {
    id = 'user_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('device_id', id);
  }
  return id;
};
```

---

## 6. 测试数据

预置3个热门基金：

```sql
INSERT INTO funds (code, name, manager) VALUES
('005827', '易方达蓝筹精选混合', '张坤'),
('003095', '中欧医疗健康混合A', '葛兰'),
('161725', '招商中证白酒指数', '侯昊');
```

---

## 7. 部署命令

### 后端部署（Render）

1. 推送代码到GitHub
2. 在Render创建Web Service
3. 配置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python backend/main.py`
   - 环境变量：DEEPSEEK_API_KEY

### 前端部署（Vercel）

1. 在Vercel导入GitHub仓库
2. 配置：
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `frontend/.next`

---

## 8. 验证检查清单

**MVP完成标准：**
- [ ] 能搜索基金并添加到列表
- [ ] 点击生成后显示进度
- [ ] 生成完成后能播放音频
- [ ] 能看到文字稿
- [ ] 能正常播放/暂停/调速
- [ ] 部署后10个人能正常使用

**收集反馈：**
- 内容质量如何？（1-5分）
- 播客形式比阅读更好吗？
- 愿意推荐给朋友吗？
- 最想要增加什么功能？

---

## 9. 常见问题

**Q: SQLite能支撑多少用户？**
A: MVP阶段100用户足够，单机SQLite能处理几百并发。

**Q: 音频文件存在哪里？**
A: MVP阶段存在服务器本地（backend/audio/），后期再迁移到OSS。

**Q: Edge TTS被封怎么办？**
A: 降级方案：仅显示文字稿，提示"音频服务暂时不可用"。

**Q: 生成太慢怎么办？**
A: 设置超时5分钟，超过则标记失败，用户可重试。

---

## 10. 下一步

如果MVP验证成功：
1. 添加用户系统（手机号登录）
2. 更好的TTS服务（Azure/讯飞）
3. 自动检测季报更新
4. 播客分享功能

如果验证失败：
1. 分析用户反馈
2. 调整产品方向或放弃

**开始开发吧！**
