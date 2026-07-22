下面整理成一个可以直接喂给 AI Agent（Codex / Claude Code / Cursor）的修改任务 MD。

保存为：

```text
docs/FRONTEND_STATIC_MIGRATION.md
```

---

# Prediction Radar Frontend Static Migration

## 目标

将 Prediction Radar 前端从：

```
Astro SSR + Node Adapter
```

迁移为：

```
Astro Static Site
+
Cloudflare Pages / Cloudflare Static Hosting
```

降低部署成本，提高稳定性。

---

# 当前架构

## Before

```
User
 |
 |
Astro SSR Server
(@astrojs/node)
 |
 |
FastAPI Backend
 |
 |
PostgreSQL
```

当前问题：

* 前端需要 Node Server 常驻
* Render 免费实例会休眠
* Cloudflare 无法直接托管
* 对 Prediction Radar 这种数据展示型产品没有必要

---

# Target Architecture

## After

```
                Cloudflare

             mopplo.com
                  |
                  |
          Astro Static Site
                  |
          Build Time Fetch
                  |
                  ↓
        Prediction Radar API
                  |
              FastAPI
                  |
          Supabase PostgreSQL
```

---

# Migration Tasks

## P0. Remove Node Adapter

### Remove dependency

执行：

```bash
cd frontend

npm uninstall @astrojs/node
```

---

## P1. Update astro.config.mjs

### Before

```javascript
import node from '@astrojs/node';
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'server',
  adapter: node({
    mode: 'standalone',
  }),
  server: {
    host: true,
    port: 4321,
  },
});
```

### After

修改为：

```javascript
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
});
```

要求：

* 删除 server 配置
* 删除 adapter 配置
* 保留 Astro 默认构建能力

---

# P2. Verify API Layer

检查：

```
frontend/src/lib/api.ts
```

要求：

API Base URL 必须通过环境变量获取。

推荐：

```ts
const API_BASE_URL = import.meta.env.PUBLIC_API_URL;
```

禁止：

```ts
const API_BASE_URL =
"https://xxx.onrender.com";
```

---

# P3. Add Environment Variable

新增：

```
frontend/.env
```

内容：

```env
PUBLIC_API_URL=https://your-backend-url
```

示例：

```env
PUBLIC_API_URL=https://prediction-radar-api.onrender.com
```

---

# P4. Build Verification

执行：

```bash
cd frontend

npm install

npm run build
```

成功标准：

生成：

```
frontend/dist
├── index.html
├── assets
└── static files
```

不应该出现：

```
dist/
├── client
└── server
```

---

# P5. Check Current Pages

当前首页：

```
src/pages/index.astro
```

已有逻辑：

```astro
await Promise.all([
 getTopMovers(),
 getEmergingSignals(),
 getDailyRadar(),
 getNarrativeTrends(),
])
```

确认：

* build 阶段可以成功请求 API
* API 不可用时页面显示 error state
* 不影响静态生成

---

# P6. Cloudflare Deployment

部署目标：

```
Cloudflare Pages
```

Git Repository:

```
mopplo/prediction-rader
```

Build Command:

```bash
cd frontend && npm install && npm run build
```

Output Directory:

```text
frontend/dist
```

如果 Root Directory 可配置：

```
frontend
```

否则：

Build Command:

```bash
cd frontend && npm install && npm run build
```

---

# P7. Runtime Consideration

Static 架构特点：

## 优点

* 免费
* 全球 CDN
* 无服务器成本
* 加载速度快

## 缺点

数据不是实时刷新

当前 MVP 接受。

---

# Future Optimization

## V2.0 Dynamic Data Layer

未来考虑：

```
Astro Static
+
Client Side Fetch
+
FastAPI JSON API
```

或者：

```
Astro Hybrid
+
ISR
```

实现：

* 实时概率变化
* 自动刷新
* 用户个性化

---

# Acceptance Criteria

完成后：

## Frontend

✅ Astro static build 成功
✅ Cloudflare 部署成功
✅ mopplo.com 可访问

## Backend

保持：

```
Render FastAPI
```

不修改。

## Database

保持：

```
Supabase PostgreSQL
```

不修改。

---

# Final Architecture

```
                 Cloudflare CDN

                 mopplo.com
                      |
                      |
              Astro Static Frontend
                      |
                      |
              Render FastAPI API
                      |
                      |
              Supabase PostgreSQL
```

目标：

Prediction Radar MVP 以 **0 成本公网运行**。

---

这个版本适合直接给 AI 执行。执行完后下一步就是：

1. Cloudflare 部署
2. 绑定 `mopplo.com`
3. 配置 API CORS
4. 发布第一个公网 Beta 版本。
