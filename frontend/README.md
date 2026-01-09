# Model Price Frontend

AI 模型定价展示前端，基于 React + TypeScript + Vite 构建。

## 技术栈

- **React** 19
- **TypeScript** 5.9
- **Vite** 7 - 构建工具
- **React Router** 7 - 路由
- **Lucide React** - 图标库

## 快速开始

### 安装依赖

```bash
npm install
```

### 配置环境变量（可选）

```bash
cp .env.example .env
# 编辑 .env 进行配置
```

### 启动开发服务器

```bash
npm run dev
```

前端将在 http://localhost:5173 启动

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录

### 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── App.tsx          # 主应用组件
│   ├── App.css          # 全局样式
│   ├── main.tsx         # 应用入口
│   ├── components/      # React 组件
│   │   ├── FilterBar.tsx       # 筛选栏
│   │   ├── ModelCard.tsx       # 模型卡片
│   │   ├── ModelTable.tsx      # 模型表格
│   │   ├── RefreshButton.tsx   # 刷新按钮
│   │   ├── ViewToggle.tsx      # 视图切换
│   │   ├── CapabilityBadge.tsx # 能力标签
│   │   └── ModalityIcons.tsx   # 模态图标
│   ├── config/          # 前端配置
│   │   ├── api.ts            # API 配置
│   │   ├── capabilities.ts   # 能力定义
│   │   ├── providers.ts      # 提供商配置
│   │   ├── version.ts        # 版本信息
│   │   └── visualization.ts  # 可视化配置
│   ├── hooks/
│   │   └── useModels.ts      # 模型数据 Hook
│   └── types/
│       └── pricing.ts        # TypeScript 类型定义
├── package.json
├── vite.config.ts
└── tsconfig.app.json
```

## 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `VITE_API_BASE` | `/api` | API 基础路径 |
| `VITE_BACKEND_URL` | `http://localhost:8000` | 后端服务地址（开发代理用） |

## 功能特性

- 多提供商模型价格对比（AWS Bedrock、Azure OpenAI、OpenAI、Google Gemini、OpenRouter、xAI）
- 按提供商、能力、模型系列筛选
- 模型名称搜索
- 表格/卡片视图切换
- 手动刷新定价数据
- 响应式设计

## 开发

### 代码检查

```bash
npm run lint
```

### 类型检查

```bash
npm run build
```

（`tsc -b` 会在构建时进行类型检查）
