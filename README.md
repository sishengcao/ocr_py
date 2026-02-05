# ocr_py

一个支持多引擎的文本识别服务，提供简单易用的 HTTP API 接口。

## 项目概述

**单一职责**：仅提供 OCR 文字识别功能

**核心功能**：输入图片 → OCR 识别 → 返回结构化数据

**技术栈**：
- Web 框架：FastAPI
- OCR 引擎：PaddleOCR 3.4
- 容器化：Docker
- 架构：多引擎可扩展设计

## 文档导航

| 文档 | 说明 |
|------|------|
| [API 响应结构说明](./API_RESPONSE.md) | 📘 详细的 API 响应字段说明和示例 |
| [测试文档](./TEST_DOCUMENT.md) | 🧪 API 测试指南和调用示例 |

---

## 支持的 OCR 引擎

| 引擎 | 版本 | 说明 | 默认 | 需要配置 |
|------|------|------|------|----------|
| **PaddleOCR** | 3.4.0 | 本地引擎，免费，支持中英日韩等多语言 | ✅ | 否 |

---

## 项目架构

```
ocr_py/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API 路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   └── engine_router.py # 引擎路由器
│   ├── engines/             # OCR 引擎模块
│   │   ├── __init__.py
│   │   ├── base.py          # 引擎基类
│   │   ├── factory.py       # 引擎工厂
│   │   └── paddleocr_engine.py       # PaddleOCR 实现
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic 数据模型
│   └── utils/
│       ├── __init__.py
│       └── image.py         # 图片处理工具
├── tests/                   # 测试文件
├── requirements.txt         # Python 依赖
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker 编排配置
└── .env.example            # 环境变量示例
```

---

## API 接口

### 1. 健康检查

```http
GET /health
```

**响应示例**：
```json
{
  "status": "ok",
  "service": "ocr_py",
  "version": "1.0.0",
  "engines": {
    "paddleocr": {
      "available": true,
      "status": {
        "engine": "PaddleOCR",
        "name": "paddleocr",
        "available": true,
        "version": "3.4.0",
        "supported_languages": ["ch", "ch_traditional", "en", "fr", "german", "korean", "japan"]
      }
    }
  }
}
```

### 2. 引擎列表

```http
GET /engines
```

### 3. OCR 识别

```http
POST /ocr/recognize
```

#### 方式一：Base64 编码（JSON）

**请求头**：
```
Content-Type: application/json
```

**请求体**：
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...",
  "engine": "paddleocr",
  "options": {
    "lang": "ch",
    "return_details": true
  }
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | string | ✅ | Base64 编码的图片数据 URL |
| `engine` | string | ❌ | OCR 引擎：`paddleocr`（默认） |
| `options` | object | ❌ | 识别选项 |
| `options.lang` | string | ❌ | 语言代码：`ch`（简体）、`ch_traditional`（繁体）、`en` 等 |
| `options.return_details` | boolean | ❌ | 返回详细信息（文本框位置、置信度） |

**响应示例**：
```json
{
  "success": true,
  "data": {
    "text": "识别的完整文本\n多行内容",
    "lines": [
      {
        "text": "第一行文本",
        "box": [[367.0, 146.0], [650.0, 146.0], [650.0, 171.0], [367.0, 171.0]],
        "confidence": 0.976
      }
    ],
    "elapsed_time": 1.95,
    "engine": "paddleocr",
    "requested_engine": "paddleocr",
    "fallback_used": false
  },
  "error": null
}
```

> 📖 **查看详细的响应字段说明**：[API 响应结构说明](./API_RESPONSE.md)

---

## 快速开始

### 方式一：Docker 部署（推荐）

#### Windows (WSL) 环境部署

1. **进入 WSL 并构建镜像**
```bash
# 启动 WSL Ubuntu
wsl -d Ubuntu-22.04

# 进入项目目录（假设项目在 D:\project\ocr_py）
cd /mnt/d/project/ocr_py

# 构建镜像
docker build -t ocr_py:latest .
```

2. **运行容器**
```bash
# 运行容器（端口映射 8808）
docker run -d -p 8808:8808 --name ocr_py ocr_py:latest

# 查看容器状态
docker ps

# 查看日志（首次启动会下载 PaddleOCR 模型，约 80MB）
docker logs -f ocr_py
```

3. **验证服务**
```bash
# 健康检查
curl http://localhost:8808/health

# 查看引擎列表
curl http://localhost:8808/engines

# 测试 OCR 识别（使用 base64 编码的图片）
curl -X POST http://localhost:8808/ocr/recognize \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/jpeg;base64,/9j/4AAQ..."}'
```

#### Linux/MacOS 环境部署

1. **构建镜像**
```bash
docker build -t ocr_py:latest .
```

2. **运行容器**
```bash
docker run -d -p 8808:8808 --name ocr_py ocr_py:latest
```

3. **验证服务**
```bash
curl http://localhost:8808/health
```

### 方式二：Docker Compose

```bash
docker-compose up -d
```

### 方式三：本地开发

#### 1. 安装依赖
```bash
pip install -r requirements.txt
```

#### 2. 启动服务
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8808
```

---

## 调用示例

### cURL

**PaddleOCR（默认）**：
```bash
curl -X POST http://localhost:8808/ocr/recognize \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/jpeg;base64,/9j/4AAQ..."}'
```

**文件上传**：
```bash
curl -X POST http://localhost:8808/ocr/recognize \
  -F "image=@/path/to/image.jpg"
```

### Python

```python
import requests
import base64

# PaddleOCR (默认)
with open("image.jpg", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()
    data_url = f"data:image/jpeg;base64,{img_data}"

response = requests.post(
    "http://localhost:8808/ocr/recognize",
    json={"image": data_url}
)
print(response.json())
```

### JavaScript

```javascript
// PaddleOCR (默认)
fetch('http://localhost:8808/ocr/recognize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    image: 'data:image/jpeg;base64,/9j/4AAQ...'
  })
}).then(r => r.json()).then(console.log);
```

---

## 配置说明

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 服务配置
HOST=0.0.0.0
PORT=8808

# OCR 配置
OCR_LANG=ch          # 默认语言：ch=中文简体, en=英文
LOG_LEVEL=INFO       # 日志级别

# 上传限制
MAX_UPLOAD_SIZE=52428800  # 50MB
```

---

## 引擎架构

### 引擎基类 (OcrEngine)

所有 OCR 引擎必须继承 `OcrEngine` 基类并实现以下方法：

```python
from abc import ABC, abstractmethod
from app.engines.base import OcrEngine, OcrOptions, OcrResult

class CustomEngine(OcrEngine):
    def __init__(self, name: str):
        super().__init__(name)

    def recognize(self, image_path: str, options: OcrOptions) -> OcrResult:
        # 实现识别逻辑
        pass

    def get_status(self) -> Dict[str, Any]:
        # 返回引擎状态
        pass
```

### 注册新引擎

在 `app/api/routes.py` 的 `_init_engines()` 函数中注册：

```python
from app.engines.custom_engine import CustomEngine
from app.engines.factory import EngineFactory

custom_engine = CustomEngine()
EngineFactory.register(custom_engine)
```

---

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 测试覆盖率
pytest tests/ --cov=app --cov-report=html
```

---

## 性能参考

| 引擎 | 识别速度 | 内存占用 | 并发支持 |
|------|----------|----------|----------|
| PaddleOCR | 1-3 秒/张 | 500MB-1GB | 单实例 |

---

## 部署到远程服务器

```bash
# 1. 构建镜像
docker build -t ocr_py:latest .

# 2. 保存镜像
docker save ocr_py:latest | gzip > ocr_py.tar.gz

# 3. 传输到服务器
scp ocr_py.tar.gz user@server:/path/

# 4. 在服务器上加载并运行
ssh user@server
docker load < ocr_py.tar.gz
docker run -d -p 8808:8808 --name ocr_py --restart=unless-stopped ocr_py:latest
```

---

## 注意事项

1. **首次启动** PaddleOCR 会自动下载模型（约 80MB），需要网络连接
2. **PaddleOCR** 支持 CPU 模式，适合中小规模识别需求
3. **支持格式**：JPG、PNG、GIF、BMP、WEBP
4. **文件大小限制**：默认 50MB，可通过环境变量调整
5. **架构设计**：使用工厂模式 + 路由模式，方便扩展新的 OCR 引擎

---

## 常见问题

**Q: 服务启动后无法访问？**
A: 检查防火墙设置，确保 8808 端口开放

**Q: PaddleOCR 识别结果不准确？**
A: 确保图片清晰度足够，文字大小适中

**Q: 如何添加其他语言支持？**
A: 修改 `OCR_LANG` 参数或在请求中指定 `lang` 参数

**Q: 如何添加新的 OCR 引擎？**
A: 继承 `OcrEngine` 基类，实现 `recognize` 和 `get_status` 方法，然后在 `routes.py` 中注册

---

## 更新日志

### v1.0.0 (2026-01-30)

- 初始版本
- 支持 PaddleOCR
- 多引擎可扩展架构
- 完整的单元测试覆盖
