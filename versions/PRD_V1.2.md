下面是**只包含 V1.2 范围**的优化文档，控制范围在「不改核心架构、不引入 AI、不扩大功能」的产品打磨阶段。

目标：

> 把 Prediction Radar 从 MVP Dashboard 优化成一个可以公开 Beta 的产品。

可以直接保存为：

`Prediction Radar V1.2 Product Optimization.md`

---

```md
# Prediction Radar V1.2 Product Optimization Plan

## 版本目标

版本：

v1.2 Product Refinement

目标：

在现有 MVP 基础上，提高：

- 产品专业感
- 用户理解效率
- 信息价值密度
- 首页转化体验


不新增复杂能力：

- 不引入 AI Summary
- 不新增用户系统
- 不新增告警系统
- 不改变核心 Signal Engine


重点：

优化已有数据的表达方式。


---

# 当前产品结构


## 首页


```

Prediction Radar

├── Top Movers  
│  
├── Emerging Signals  
│  
├── Narrative Trends  
│  
└── Daily Radar

```


## 详情页


```

Market Detail

├── Market Header  
│  
├── Probability Information  
│  
├── Why It Moved  
│  
├── Probability History  
│  
└── Signal Breakdown

```


---

# V1.2 核心优化方向


## 1. 首页产品感增强

### 1.1 增加 Stats Bar


## 当前问题

用户打开首页不知道：

- 覆盖规模
- 更新频率
- 当前活跃信号数量


## 新增模块

位置：

Hero 区域下面


展示：


```

Markets Tracked

5,000+

Signals Today

XX

Update Frequency

15 min

```


数据来源：

Markets:

- total markets count


Signals:

- daily signal count


Update:

- latest sync timestamp


目标：

增强产品可信度。


---

# 2. 首页模块说明优化


## Top Movers


### 定位

回答：

> 哪些重要事件的市场观点变化最大？


展示说明：


```

Largest validated probability shifts.

Discover where prediction markets changed their beliefs.

```


卡片增强：

当前：


```

+38pp

Probability

Signal Score

```


优化：

突出：


```

+38pp

24h Probability Shift

```


增加 tooltip：

说明：


```

pp means percentage point.

Example:  
40% → 78% = +38pp

```


---

## Emerging Signals


### 定位

回答：

> 哪些市场正在获得关注？


当前问题：

Volume Spike 价值没有突出。


优化卡片：


增加：


```

Attention Spike

Volume

3.8x baseline

Probability

+5.2%

```


视觉强调：

- volume spike
- liquidity increase
- early attention


---

## Narrative Trends


### 定位

回答：

> 哪些故事正在形成？


保持现有设计。


优化：

增加说明：


```

Stories forming across related prediction markets.

```


重点突出：

不要展示单一市场。

强调：

多个市场形成的趋势。


---

## Daily Radar


### 定位

回答：

> 今天最值得看的市场有哪些？


当前问题：

和 Top Movers / Emerging 边界不明显。


优化：

描述改为：


```

Today's highest quality signals.

Curated by signal score and data confidence.

```


卡片增加：


```

Why selected:

High confidence

Strong liquidity

Meaningful movement

```


---

# 3. 首页 Card 统一优化


所有 Market Card 增加：


## 必备信息



```

Market Title

Current Probability

XX%

24h Change

+XXpp

Signal Score

XX/100

Data Confidence

High

```


保持信息一致。


---

# 4. 详情页 Hero 重构


## 当前问题

详情页数据完整，但是重点不突出。


## 优化后


顶部展示：



```

Market Title

Current Probability

76%

24h Change

+38pp

Signal Score

67/100

Data Confidence

82

```


用户第一眼理解：

- 当前状态
- 市场变化
- 信号质量


---

# 5. Why It Moved 优化


## 当前

已经具备：

- probability change
- volume
- liquidity
- confidence


保留。


## 调整标题


修改：


```

Why It Moved

```


改为：


```

Why This Signal Matters

```


展示：



```

✓ Probability shifted +38pp

✓ Volume increased 1.2x

✓ Liquidity remains strong

✓ High confidence data

```


目标：

从：

数据解释

变成：

价值解释。


---

# 6. Signal Breakdown 优化


## 当前问题

普通用户不知道 Signal Breakdown 含义。


## 修改


标题：


```

Signal Breakdown

```


改为：


```

Signal Quality

```


展示：



```

Probability Momentum

82

Volume Activity

70

Liquidity Quality

75

Data Confidence

82

```


增加 tooltip：

解释每个指标。


---

# 7. Polymarket 跳转优化


## 当前

已有：


```

View on Polymarket

```


保持。


优化：

位置：

详情页 Hero 区域明显位置。


按钮：


```

View on Polymarket ↗

```


原因：

Prediction Radar 定位：

Discovery Layer


不是交易平台。


---

# 8. Footer 品牌增强


当前：


```

Data source:  
Polymarket public API

Updated every 15 minutes

```


增加：



```

Built by Mopplo

Prediction Radar is an independent  
prediction market intelligence tool.

Data:  
Polymarket API

Links:

GitHub

X

```


目的：

强化 Mopplo 品牌。


---

# 9. SEO 优化


增加：

## Title


```

Prediction Radar - Track Prediction Market Signals

```


## Description


```

Discover where prediction markets are changing their minds.

Track probability shifts, emerging signals and global narratives.

```


## Open Graph

增加：

- favicon
- social preview image
- Twitter card


---

# 10. V1.2 不做内容


以下功能延后：

## AI Summary

V1.3


## Related Markets

V1.3


## Alerts

V1.4


## Daily Newsletter

V1.4


## Multi Prediction Market

V2


---

# V1.2 完成标准


## 首页

完成：

[x] Stats Bar

[x] 模块说明优化

[x] Card 信息层级优化

[x] Top Movers 强调变化

[x] Emerging 强调 Attention


---

## 详情页

完成：

[x] Hero 数据重构

[x] Why This Signal Matters

[x] Signal Quality

[x] Polymarket CTA


---

## 品牌

完成：

[x] Footer Mopplo Branding

[x] SEO Metadata

[x] OpenGraph


---

# V1.2 产品目标


完成后：

用户打开 Prediction Radar：

5 秒内知道：

1. 这是预测市场情报工具

2. 哪些事件正在变化

3. 为什么值得关注

4. 可以进一步去 Polymarket 查看


最终定位：


```

Prediction Radar

Discover where the world is changing its mind.

```

by Mopplo

```

---

这个版本控制得比较合理，**AI Agent 一次实现不会失控**。

我建议执行顺序：

1. 首页 Hero + Stats Bar
2. Card 信息优化
3. Detail Hero
4. Signal Quality
5. Footer/SEO

做完这五步，基本就是一个可以正式发 X 的 Beta 产品。