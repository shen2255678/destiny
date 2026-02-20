# DESTINY — Deployment Guide

**Last Updated:** 2026-02-18

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      USERS (Browser)                     │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────┐
│                  VERCEL (Free Hobby)                      │
│  Next.js 16 App Router                                    │
│  ├── /app (frontend pages)                                │
│  ├── /api/onboarding/*    (birth-data, rpv, photos)      │
│  ├── /api/rectification/* (next-question, answer)         │
│  ├── /api/matches/*       (daily feed, actions)           │
│  ├── /api/connections/*   (chat, icebreaker)              │
│  └── /api/profile/*       (me, energy, photos)           │
└───────┬──────────────────────────┬───────────────────────┘
        │ SQL / Auth / Storage     │ HTTP (internal calls)
        │                          │
┌───────▼──────────┐    ┌──────────▼────────────────────── ┐
│  SUPABASE        │    │  RAILWAY ($5/month Hobby)         │
│  (already live)  │    │  Python FastAPI (astro-service)   │
│  ├── PostgreSQL  │    │  ├── POST /calculate-chart        │
│  ├── Auth        │    │  ├── POST /analyze-relation       │
│  └── Storage     │    │  ├── POST /run-daily-matching     │
│                  │    │  └── GET  /health                 │
└──────────────────┘    └───────────────────────────────────┘
                                    ↑
                          AI API calls (Gemini / OpenAI / Claude)
                          can be called from EITHER service
                          depending on response length (see §4)
```

---

## 1. Platform Summary

| Service | Platform | Plan | Est. Cost |
|---------|----------|------|-----------|
| Next.js App | Vercel | Hobby (free) | $0/月 |
| Python astro-service | Railway | Hobby | $5/月 |
| Database + Auth + Storage | Supabase | Free tier | $0/月 |
| AI APIs (Claude / Gemini / OpenAI) | Anthropic / Google / OpenAI | Pay-as-you-go | 依用量 |
| **Total** | | | **~$5/月** |

---

## 2. Vercel — Next.js 部署

### 2.1 Setup

```bash
# 安裝 Vercel CLI
npm i -g vercel

# 首次部署（在 destiny-app/ 目錄下）
cd destiny-app
vercel

# 之後 git push 自動部署（需連接 GitHub repo）
vercel --prod
```

### 2.2 Environment Variables（在 Vercel Dashboard 設定）

```bash
NEXT_PUBLIC_SUPABASE_URL=https://masninqgihbazjirweiy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Railway 部署後填入
ASTRO_SERVICE_URL=https://your-astro-service.up.railway.app

# AI APIs（依使用哪個填入）
ANTHROPIC_API_KEY=<your-key>
GOOGLE_AI_API_KEY=<your-key>       # Gemini
OPENAI_API_KEY=<your-key>
```

### 2.3 Vercel Hobby 限制

| 限制項目 | Hobby 方案 | 影響 |
|---------|-----------|------|
| Serverless Function timeout | **10 秒** | 長 AI 生成需用 streaming（見 §4） |
| 流量 | 100 GB/月 | MVP 期夠用 |
| 部署次數 | 無限 | OK |
| Custom domain | ✅ 支援 | OK |
| Preview deployments | ✅ 每 PR 一個 URL | 測試方便 |

> **重要：** 若 AI 生成超過 10 秒，需改用 streaming（`TransformStream`）或升級到 Pro（$20/月，60 秒 timeout）。

---

## 3. Railway — Python astro-service 部署

### 3.1 Setup

```bash
# 安裝 Railway CLI
npm i -g @railway/cli

# 登入
railway login

# 在 astro-service/ 目錄下初始化
cd astro-service
railway init

# 部署
railway up
```

### 3.2 Procfile（放在 `astro-service/` 根目錄）

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Railway 會自動注入 `$PORT` 環境變數。

### 3.3 Railway Environment Variables

```bash
# Railway Dashboard 設定（astro-service 不需要 Supabase，由 Next.js API 負責寫回 DB）
# 若日後 astro-service 也需呼叫 AI API：
ANTHROPIC_API_KEY=<your-key>
GOOGLE_AI_API_KEY=<your-key>
```

### 3.4 `requirements.txt` 確認

```txt
fastapi
uvicorn
pyswisseph       # C native lib — Railway 支援，Vercel/Cloudflare 不支援
httpx
python-dotenv
```

Railway 會自動安裝，包含 native C extensions。

---

## 4. AI API 整合策略

### 4.1 從哪裡呼叫 AI？

| 功能 | 預估回應時間 | 建議呼叫位置 | 方式 |
|------|------------|-------------|------|
| 變色龍標籤生成（3-5 個詞） | < 3s | Vercel (Next.js API route) | 一般呼叫 |
| 校正問題選題解釋（短文） | < 5s | Vercel | 一般呼叫 |
| 破冰題生成（1-2 句） | < 5s | Vercel | 一般呼叫 |
| 靈魂原型報告（長文） | 10-30s | Vercel with **Streaming** | `TransformStream` |
| 深度相合分析（長文）| 15-40s | Vercel with **Streaming** | `TransformStream` |
| 占星相關 AI 分析 | 任意 | Railway (Python) | 可避免 10s 限制 |

### 4.2 Vercel Streaming API Route 範例（Next.js）

```typescript
// src/app/api/onboarding/soul-report/route.ts
import Anthropic from '@anthropic-ai/sdk'

export const runtime = 'nodejs'  // 或 'edge'（edge 更快但限制更多）
export const maxDuration = 60    // Pro 方案才有效；Hobby 固定 10s

export async function GET(request: Request) {
  const client = new Anthropic()

  const stream = await client.messages.stream({
    model: 'claude-opus-4-6',
    max_tokens: 1024,
    messages: [{ role: 'user', content: '生成靈魂原型報告...' }]
  })

  // 使用 ReadableStream 串流給前端
  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        if (chunk.type === 'content_block_delta') {
          controller.enqueue(new TextEncoder().encode(chunk.delta.text))
        }
      }
      controller.close()
    }
  })

  return new Response(readable, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' }
  })
}
```

### 4.3 AI API 費用估算

| API | 模型 | 輸入價格 | 輸出價格 | 適合用途 |
|-----|------|---------|---------|---------|
| **Anthropic Claude** | claude-haiku-4-5 | $0.80/M tokens | $4/M tokens | 短標籤、破冰題（便宜） |
| **Anthropic Claude** | claude-sonnet-4-6 | $3/M tokens | $15/M tokens | 靈魂報告、深度分析（推薦） |
| **Google Gemini** | gemini-2.0-flash | $0.10/M tokens | $0.40/M tokens | 最便宜，短文本 |
| **OpenAI** | gpt-4o-mini | $0.15/M tokens | $0.60/M tokens | 備選 |

> **建議：** 標籤/問題生成用 **claude-haiku-4-5** 或 **gemini-2.0-flash**；靈魂報告用 **claude-sonnet-4-6**。

---

## 5. 部署順序（逐步上線）

```
Step 1: Railway — 部署 astro-service
  └── 取得 Railway URL
  └── 驗證 GET /health 回應

Step 2: Vercel — 部署 Next.js
  └── 設定所有環境變數（含 ASTRO_SERVICE_URL）
  └── 驗證 /api/onboarding/birth-data 能呼叫到 Railway

Step 3: Supabase — 執行 Migration 005
  └── supabase db push（或 Supabase Dashboard SQL editor）

Step 4: 端對端測試
  └── 註冊流程 → 星盤計算 → Rectification 初始化

Step 5: 設定 AI API Keys
  └── 加入 Vercel 環境變數
  └── 升級 soul-report API 為 Claude API + streaming
```

---

## 6. 未來擴展考量

| 需求 | 建議 |
|------|------|
| 流量成長，Vercel Hobby 不夠 | 升 Vercel Pro（$20/月，60s timeout，更多流量）|
| astro-service 需要更多資源 | Railway 升規格（CPU/RAM 按用量計費）|
| 需要背景 Cron Job（每日配對） | Railway 內建 Cron Job 支援 |
| WebSocket / Supabase Realtime | Supabase 直接提供，不需額外基礎設施 |
| 多 region 低延遲 | Vercel Edge + Railway 選近的 region |

### 6.1 Railway Cron Job（每日配對）

```bash
# Railway Dashboard → Service → Cron Jobs
# 每日 21:00 UTC+8（13:00 UTC）執行
0 13 * * *  curl -X POST https://your-astro-service.up.railway.app/run-daily-matching
```

---

## 7. 本地開發 vs 雲端環境對照

| | 本地 | 雲端 |
|--|------|------|
| Next.js | `npm run dev` (port 3000) | Vercel |
| astro-service | `uvicorn main:app --port 8001` | Railway |
| ASTRO_SERVICE_URL | `http://localhost:8001` | `https://xxx.railway.app` |
| Supabase | 同一個 cloud project | 同一個 cloud project |
