# API 响应结构说明

本文档详细说明 OCR 服务 API 的所有响应字段及其含义。

---

## 目录

- [1. 通用响应格式](#1-通用响应格式)
- [2. 健康检查响应](#2-健康检查响应)
- [3. 引擎列表响应](#3-引擎列表响应)
- [4. OCR 识别响应](#4-ocr-识别响应)
- [5. 错误响应](#5-错误响应)
- [6. 字段数据类型](#6-字段数据类型)

---

## 1. 通用响应格式

所有 API 响应都使用 JSON 格式，遵循统一的结构规范。

### HTTP 状态码

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | OK | 请求成功，响应体包含业务数据或错误信息 |
| 422 | Unprocessable Entity | 请求格式错误或数据验证失败 |

### 字符编码

- **Content-Type**: `application/json; charset=utf-8`
- **编码**: UTF-8

---

## 2. 健康检查响应

### 接口

```http
GET /health
```

### 响应结构

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
                "supported_languages": ["ch", "en", "ch_traditional", "fr", "german", "korean", "japan"]
            }
        }
    }
}
```

### 字段说明

#### 根级字段

| 字段路径 | 类型 | 必填 | 说明 |
|----------|------|------|------|
| `status` | string | ✅ | 服务状态：`ok`（至少一个引擎可用）或 `error`（所有引擎不可用） |
| `service` | string | ✅ | 服务名称，固定值 `ocr_py` |
| `version` | string | ✅ | 服务版本号，遵循语义化版本规范 |
| `engines` | object | ✅ | 所有引擎的状态信息对象 |

#### engines 对象

`engines` 是一个嵌套对象，键名为引擎标识符，值为引擎状态对象：

| 字段路径 | 类型 | 说明 |
|----------|------|------|
| `engines.{engine_name}` | object | 单个引擎的状态信息 |
| `engines.{engine_name}.available` | boolean | 该引擎是否可用 |
| `engines.{engine_name}.status` | object | 引擎详细状态 |

#### 引擎状态对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `engine` | string | 引擎显示名称（如 `PaddleOCR`） |
| `name` | string | 引擎标识符（如 `paddleocr`） |
| `available` | boolean | 引擎是否可用（已配置且正常运行） |
| `version` | string | 引擎版本号 |
| `supported_languages` | array | 支持的语言代码数组 |

---

## 3. 引擎列表响应

### 接口

```http
GET /engines
```

### 响应结构

```json
{
    "engines": {
        "paddleocr": {
            "available": true,
            "status": { ... }
        }
    },
    "default": "paddleocr"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `engines` | object | ✅ | 引擎状态对象，结构与健康检查响应中的 `engines` 相同 |
| `default` | string | ✅ | 默认引擎标识符 |

---

## 4. OCR 识别响应

### 接口

```http
POST /ocr/recognize
```

### 成功响应结构

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

### 字段说明

#### 根级字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `success` | boolean | ✅ | 识别是否成功：`true` 表示成功，`false` 表示失败 |
| `data` | object/null | ❌ | 识别结果数据（成功时存在） |
| `error` | string/null | ❌ | 错误信息（失败时存在） |

**注意**：`success` 为 `true` 时，`data` 存在且 `error` 为 `null`；`success` 为 `false` 时，`data` 为 `null` 且 `error` 包含错误描述。

#### data 对象

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | 识别的完整文本，包含所有识别结果，多行文本用换行符 `\n` 分隔 |
| `lines` | array | ✅ | 单行文本详情数组，每个元素包含该行的文本、位置和置信度 |
| `elapsed_time` | float | ✅ | 处理耗时，单位为秒，精确到小数点后两位 |
| `engine` | string | ✅ | **实际执行识别**的引擎标识符（如 `paddleocr`） |
| `requested_engine` | string/null | ❌ | **用户请求的**引擎标识符，为 `null` 表示使用默认引擎 |
| `fallback_used` | boolean | ✅ | 是否使用了故障转移：`true` 表示请求引擎失败后切换到其他引擎 |

#### lines 数组元素

每个元素代表识别到的一行文本：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | 该行的识别文本内容 |
| `box` | array | ✅ | 文本框坐标，四个角点的坐标数组 |
| `confidence` | float | ✅ | 识别置信度，范围 0.0 到 1.0，值越大表示越可信 |

#### box 坐标数组

格式：`[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]`

- 类型：二维数组，包含 4 个坐标点
- 坐标系：原点在图片左上角，x 轴向右，y 轴向下
- 顺序：左上、右上、右下、左下（顺时针）
- 单位：像素（float 类型，可包含小数）

示例：
```json
[[367.0, 146.0], [650.0, 146.0], [650.0, 171.0], [367.0, 171.0]]
```

表示文本框四个角点的坐标：
- 左上角：(367, 146)
- 右上角：(650, 146)
- 右下角：(650, 171)
- 左下角：(367, 171)

#### confidence 置信度

- 范围：0.0 ~ 1.0
- 阈值建议：
  - ≥ 0.9：高可信度
  - 0.7 ~ 0.9：中等可信度
  - < 0.7：低可信度，建议人工校验

---

## 5. 错误响应

### 参数缺失错误

```json
{
    "success": false,
    "data": null,
    "error": "Missing required field: 'image'"
}
```

### 引擎不可用错误

```json
{
    "success": false,
    "data": null,
    "error": "No available OCR engine"
}
```

### 图片格式错误

```json
{
    "success": false,
    "data": null,
    "error": "Invalid base64 image format"
}
```

### 文件过大错误

```json
{
    "success": false,
    "data": null,
    "error": "File too large. Maximum size: 52428800 bytes"
}
```

### error 字段说明

| 错误信息 | 触发条件 | 解决方案 |
|----------|----------|----------|
| `Missing required field: 'image'` | 请求体缺少 `image` 字段 | 添加图片数据（Base64 或文件上传） |
| `Invalid base64 image format` | Base64 格式不正确 | 确保格式为 `data:image/<type>;base64,<data>` |
| `Unsupported content type` | 使用了不支持的 Content-Type | 使用 `application/json` 或 `multipart/form-data` |
| `File too large` | 文件超过大小限制 | 压缩图片或分割请求 |
| `No available OCR engine` | 所有引擎都不可用 | 检查引擎配置 |
| `Image file not found` | 临时图片文件丢失 | 重试请求 |

---

## 6. 字段数据类型

### string

JSON 字符串类型，使用 UTF-8 编码。

示例：
```json
"text": "识别的文本内容",
"engine": "paddleocr"
```

### boolean

JSON 布尔类型，值为 `true` 或 `false`（小写）。

示例：
```json
"success": true,
"fallback_used": false
```

### number (float)

JSON 数字类型，支持整数和小数。

示例：
```json
"elapsed_time": 1.95,
"confidence": 0.976
```

### array

JSON 数组类型，有序列表。

示例：
```json
"supported_languages": ["ch", "en", "fr"],
"lines": [...]
```

### object

JSON 对象类型，键值对集合。

示例：
```json
"engines": {
    "paddleocr": {
        "available": true
    }
}
```

### null

JSON null 值，表示字段不存在或无值。

示例：
```json
"error": null,
"requested_engine": null
```

---

## 7. 响应示例场景

### 场景 1：正常识别（PaddleOCR）

**请求**：
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "engine": "paddleocr"
}
```

**响应**：
```json
{
    "success": true,
    "data": {
        "text": "Hello World\nOCR Test",
        "lines": [
            {
                "text": "Hello World",
                "box": [[10, 20], [100, 20], [100, 40], [10, 40]],
                "confidence": 0.98
            },
            {
                "text": "OCR Test",
                "box": [[10, 50], [100, 50], [100, 70], [10, 70]],
                "confidence": 0.95
            }
        ],
        "elapsed_time": 1.2,
        "engine": "paddleocr",
        "requested_engine": "paddleocr",
        "fallback_used": false
    },
    "error": null
}
```

### 场景 2：使用默认引擎

**请求**：
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**响应**：
```json
{
    "success": true,
    "data": {
        "text": "识别结果",
        "lines": [...],
        "elapsed_time": 1.5,
        "engine": "paddleocr",
        "requested_engine": null,
        "fallback_used": false
    },
    "error": null
}
```

---

## 8. 版本兼容性

### 当前版本：1.0.0

| 字段 | 引入版本 | 废弃状态 |
|------|----------|----------|
| `success` | 1.0.0 | 稳定 |
| `data.text` | 1.0.0 | 稳定 |
| `data.lines` | 1.0.0 | 稳定 |
| `data.elapsed_time` | 1.0.0 | 稳定 |
| `data.engine` | 1.0.0 | 稳定 |
| `data.requested_engine` | 1.0.0 | 稳定 |
| `data.fallback_used` | 1.0.0 | 稳定 |

### 废弃字段

| 字段 | 原使用 | 替代方案 | 废弃版本 |
|------|--------|----------|----------|
| 无 | - | - | - |

---

## 9. 常见问题

### Q1: `engine` 和 `requested_engine` 有什么区别？

**A**:
- `requested_engine`：用户在请求中指定的引擎
- `engine`：实际执行识别的引擎

当两者相同时，表示使用请求的引擎成功；当不同时，表示发生了故障转移。

### Q2: 如何判断是否发生了故障转移？

**A**: 检查 `fallback_used` 字段：
- `true`：发生了故障转移
- `false`：使用请求的引擎成功

### Q3: `confidence` 值为 1.0 表示什么？

**A**: 表示引擎对识别结果有 100% 的信心，但实际准确度仍可能因图片质量、字体等因素有偏差。

### Q4: `lines` 数组为空表示什么？

**A**: 表示引擎成功处理图片，但未识别到任何文本。可能原因：
- 图片中没有文字
- 文字过小或模糊
- 图片质量问题

---

## 10. 相关文档

- [README.md](./README.md) - 项目概述和快速开始
- [TEST_DOCUMENT.md](./TEST_DOCUMENT.md) - 测试文档

---

最后更新：2026-01-30
