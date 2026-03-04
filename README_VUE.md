# DataVerse Pro - Vue 3 版本

多模态数据湖系统，前后端分离架构。

## 技术栈

**后端**
- FastAPI - 高性能 Web 框架
- LanceDB - 向量数据库
- Sentence Transformers - 文本/图像嵌入
- Whisper - 语音转文本

**前端**
- Vue 3 - 渐进式框架
- Element Plus - UI 组件库
- ECharts - 数据可视化
- Vite - 构建工具

## 快速开始

### 1. 安装依赖

**后端依赖**
```bash
pip install fastapi uvicorn python-multipart
```

**前端依赖**
```bash
cd frontend
npm install
```

### 2. 启动服务

**开发模式（前后端分离）**

终端 1 - 启动后端：
```bash
cd backend
python main.py
```
后端运行在 http://localhost:8080

终端 2 - 启动前端：
```bash
cd frontend
npm run dev
```
前端运行在 http://localhost:3000

**生产模式（前端构建后集成）**

1. 构建前端：
```bash
cd frontend
npm run build
```

2. 启动后端（会自动服务前端静态文件）：
```bash
cd backend
python main.py
```

访问 http://localhost:8080

## 项目结构

```
├── backend/              # FastAPI 后端
│   ├── api/             # API 路由
│   │   ├── upload.py    # 文件上传
│   │   ├── search.py    # 向量搜索
│   │   ├── files.py     # 文件管理
│   │   ├── dashboard.py # 仪表盘
│   │   └── system.py    # 系统监控
│   └── main.py          # 入口文件
├── frontend/            # Vue 3 前端
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── api/         # API 调用
│   │   ├── assets/      # 静态资源
│   │   ├── router/      # 路由配置
│   │   ├── App.vue      # 根组件
│   │   └── main.js      # 入口文件
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── etl.py               # ETL 处理逻辑
├── models_loader.py     # AI 模型加载
├── database.py          # SQLite 数据库
├── config.py            # 配置文件
└── README_VUE.md        # 本文件
```

## API 文档

启动后端后访问：http://localhost:8080/docs

## 功能特性

- ✅ 文件批量上传（文本、图片、音频、视频）
- ✅ 向量语义搜索（文本、图像）
- ✅ 文件管理（列表、预览、删除）
- ✅ 实时仪表盘（统计、趋势、分布）
- ✅ 应用日志查看
- ✅ 系统资源监控
- ✅ 蓝白透明卡片风格 UI

## 注意事项

1. 首次运行需要下载 AI 模型（约 1-2 GB），请确保网络畅通
2. 建议使用 GPU 加速（CUDA），CPU 模式会较慢
3. SeaweedFS/S3 需要提前配置好，修改 `config.py` 中的连接信息
4. 生产环境建议使用 Nginx 反向代理

## 开发说明

- 前端修改后会自动热重载
- 后端修改后需要重启服务（或使用 `--reload` 参数）
- API 接口遵循 RESTful 规范
- 所有接口返回 JSON 格式

## 故障排查

**前端无法连接后端**
- 检查后端是否启动：http://localhost:8080/api/health
- 检查 Vite 代理配置：`frontend/vite.config.js`

**图表不显示**
- 打开浏览器控制台查看错误
- 检查 ECharts 是否正确加载
- 确认 API 返回数据格式正确

**文件上传失败**
- 检查 `temp_uploads` 目录权限
- 查看后端日志：`app.log`
- 确认 S3/SeaweedFS 连接正常
