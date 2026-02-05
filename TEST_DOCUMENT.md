# OCR 服务测试文档

## 测试环境

- **部署方式**: Docker 容器 / 本地
- **服务地址**: `http://localhost:8808`
- **测试时间**: 2026-01-30
- **容器状态**: ✅ 健康运行

---

## 1. 健康检查接口

### 请求

```http
GET /health
```

### 响应

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
                "supported_languages": [
                    "ch",
                    "ch_traditional",
                    "en",
                    "fr",
                    "german",
                    "korean",
                    "japan"
                ]
            }
        }
    }
}
```

### cURL 测试命令

```bash
curl http://localhost:8808/health
```

---

## 2. 引擎列表接口

### 请求

```http
GET /engines
```

### 响应

```json
{
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
    },
    "default": "paddleocr"
}
```

### cURL 测试命令

```bash
curl http://localhost:8808/engines
```

---

## 3. OCR 识别接口

### 请求方式一：Base64 编码（JSON）

#### 请求头

```http
POST /ocr/recognize
Content-Type: application/json
```

#### 请求体参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | string | ✅ | Base64 编码的图片数据 URL 格式 |
| `engine` | string | ❌ | OCR 引擎：`paddleocr`（默认） |
| `options` | object | ❌ | 识别选项 |
| `options.lang` | string | ❌ | 语言代码：`ch`（简体）、`ch_traditional`（繁体）、`en` 等 |
| `options.enable_table` | boolean | ❌ | 启用表格识别 |
| `options.enable_formula` | boolean | ❌ | 启用公式识别 |
| `options.return_details` | boolean | ❌ | 返回详细信息（文本框位置、置信度） |

#### 请求体示例

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

#### 响应体参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `success` | boolean | 识别是否成功 |
| `data` | object/null | 识别结果数据（成功时存在） |
| `data.text` | string | 识别的完整文本 |
| `data.lines` | array | 单行文本详情数组 |
| `data.lines[].text` | string | 单行文本内容 |
| `data.lines[].box` | array | 文本框坐标 `[[x1,y1], [x2,y2], [x3,y3], [x4,y4]]` |
| `data.lines[].confidence` | float | 置信度 (0.0-1.0) |
| `data.elapsed_time` | float | 处理耗时（秒） |
| `data.engine` | string | 实际执行识别的引擎名称 |
| `data.requested_engine` | string/null | 用户请求的引擎名称（与 engine 不同表示发生了故障转移） |
| `data.fallback_used` | boolean | 是否使用了故障转移引擎 |
| `error` | string/null | 错误信息（失败时存在） |

#### 响应示例

**成功响应**:
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
            },
            {
                "text": "第二行文本",
                "box": [[367.0, 180.0], [650.0, 180.0], [650.0, 205.0], [367.0, 205.0]],
                "confidence": 0.968
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

**失败响应**:
```json
{
    "success": false,
    "data": null,
    "error": "Missing required field: 'image'"
}
```

#### cURL 测试命令

```bash
curl -X POST http://localhost:8808/ocr/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...",
    "engine": "paddleocr"
  }'
```

---

### 请求方式二：文件上传（multipart/form-data）

#### 请求头

```http
POST /ocr/recognize
Content-Type: multipart/form-data
```

#### 请求体参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | file | ✅ | 图片文件 |
| `engine` | string | ❌ | OCR 引擎：`paddleocr`（默认） |
| `lang` | string | ❌ | 语言代码：`ch`（简体）、`en` 等 |
| `return_details` | string | ❌ | 是否返回详细信息：`true`（默认）或 `false` |

#### cURL 测试命令

```bash
curl -X POST http://localhost:8808/ocr/recognize \
  -F "image=@/path/to/image.jpg" \
  -F "engine=paddleocr" \
  -F "lang=ch"
```

---

## 4. 引擎架构

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

## 5. 支持的语言代码

| 代码 | 语言 |
|------|------|
| `ch` | 中文简体 |
| `ch_traditional` | 中文繁体 |
| `en` | 英文 |
| `fr` | 法语 |
| `german` | 德语 |
| `korean` | 韩语 |
| `japan` | 日语 |

**语言别名映射**:
- `zh`, `zh-cn`, `simplified` → `ch`
- `zh-tw`, `zh-hk`, `traditional` → `ch_traditional`

---

## 6. 错误码说明

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 200 | 业务错误 | 请求成功，但识别失败（返回 `success: false`） |
| 200 | 参数错误 | 请求成功，但缺少必要参数（返回 `success: false`） |
| 422 | 验证错误 | JSON 格式或数据类型错误 |

### 常见错误信息

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Missing required field: 'image'` | 缺少图片数据 | 添加 `image` 字段 |
| `Invalid base64 image format` | Base64 格式错误 | 检查数据 URL 格式 |
| `Unsupported content type` | 不支持的内容类型 | 使用 `application/json` 或 `multipart/form-data` |
| `File too large` | 文件超过大小限制 | 默认限制 50MB |
| `No OCR engine available` | 无可用引擎 | 检查引擎安装状态 |

---

## 7. 测试清单

### 基础功能测试

- [x] 健康检查接口正常返回
- [x] 引擎列表接口正常返回
- [x] PaddleOCR 识别成功（Base64）
- [x] PaddleOCR 识别成功（文件上传）

### 错误处理测试

- [x] 空请求体返回错误信息
- [x] 无效 Base64 格式返回错误
- [x] 缺少 image 字段返回错误
- [x] 不支持的内容类型返回错误

### 边界测试

- [x] 超大文件上传（>50MB）
- [x] 空图片处理
- [x] 损坏的图片文件

---

## 8. Python 调用示例

```python
import requests
import base64

# 准备图片
with open("image.jpg", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()
    data_url = f"data:image/jpeg;base64,{img_data}"

# PaddleOCR 识别
response = requests.post(
    "http://localhost:8808/ocr/recognize",
    json={
        "image": data_url,
        "engine": "paddleocr",
        "options": {
            "lang": "ch",
            "return_details": True
        }
    }
)

result = response.json()
if result["success"]:
    print(f"识别文本: {result['data']['text']}")
    print(f"耗时: {result['data']['elapsed_time']:.2f}秒")
else:
    print(f"识别失败: {result['error']}")
```

---

## 9. JavaScript 调用示例

```javascript
// PaddleOCR 识别
fetch('http://localhost:8808/ocr/recognize', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    image: 'data:image/jpeg;base64,/9j/4AAQ...',
    engine: 'paddleocr',
    options: {
      lang: 'ch',
      return_details: true
    }
  })
}).then(r => r.json()).then(result => {
  if (result.success) {
    console.log('识别文本:', result.data.text);
    console.log('耗时:', result.data.elapsed_time);
  } else {
    console.error('识别失败:', result.error);
  }
});

// 文件上传
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('engine', 'paddleocr');
formData.append('lang', 'ch');

fetch('http://localhost:8808/ocr/recognize', {
  method: 'POST',
  body: formData
}).then(r => r.json()).then(console.log);
```

---

## 10. 部署信息

### Docker 部署

```bash
# 构建镜像
docker build -t ocr_py:latest .

# 运行容器
docker run -d -p 8808:8808 --name ocr_py ocr_py:latest

# 查看日志
docker logs -f ocr_py

# 停止容器
docker stop ocr_py
```

### 使用 docker-compose

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 11. 注意事项

1. **首次启动** PaddleOCR 会自动下载模型（约 80MB），需要网络连接
2. **支持格式**：JPG、PNG、GIF、BMP、WEBP
3. **文件大小限制**：默认 50MB，可通过环境变量调整
4. **架构设计**：使用工厂模式 + 路由模式，方便扩展新的 OCR 引擎

---

## 12. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0.0 | 2026-01-30 | 初始版本，支持 PaddleOCR |
