# MD2DOCX 后端服务

## 概述

MD2DOCX 后端服务是一个基于 Flask 的 Web 应用程序，提供 Markdown 转 Word 文档和图片 OCR 识别两大核心功能。该服务使用豆包大模型 API 实现图片内容的智能识别，支持将图片中的文字、表格、公式等内容转换为 Markdown 格式。

## 功能特点

### 1. Markdown 转 Word 文档
- 支持标准 Markdown 语法转换
- 保留文本格式、表格、列表等结构
- 支持数学公式转换
- 自动生成可下载的 Word 文档

### 2. 图片 OCR 识别
- 支持多种图片格式（JPEG、PNG、GIF、WebP）
- 智能识别图片中的文字、表格、公式等内容
- 支持普通文本和数学公式两种识别模式
- 自动将识别结果转换为 Markdown 格式
- 支持大图片压缩以提高识别速度

### 3. 系统特性
- RESTful API 设计
- 完善的错误处理机制
- 请求日志记录
- 跨域支持（CORS）
- Docker 容器化部署支持
- 阿里云函数计算部署支持

## 技术栈

- **后端框架**: Flask 2.3.3
- **HTTP 客户端**: requests 2.31.0
- **跨域支持**: flask-cors 4.0.0
- **容器化**: Docker
- **AI 模型**: 豆包大模型 API
- **云平台**: 阿里云函数计算 + 容器镜像服务 (ACR)

## 部署方式

### 1. 阿里云函数计算 + ACR 镜像部署（推荐）

本项目推荐使用阿里云函数计算结合容器镜像服务（ACR）进行部署，这种方式具有以下优势：
- 环境稳定性高
- 依赖管理简单
- 冷启动速度快
- 配置灵活
- 适合复杂应用

#### 快速部署步骤

1. **准备环境变量**
   ```bash
   # 设置阿里云账号信息
   set ACCOUNT_ID=your_account_id
   set REGION=cn-hangzhou
   set NAMESPACE=your_namespace
   set REPO_NAME=md2docx
   set DOUBAO_API_KEY=your_doubao_api_key
   ```

2. **构建并推送镜像**
   ```bash
   # 运行部署脚本
   h:\apps\md2d\build-and-deploy-acr.bat
   ```

3. **配置函数计算**
   - 登录阿里云函数计算控制台
   - 创建新函数，选择"容器镜像"方式
   - 配置实例规格（推荐：1.5 vCPU, 3072MB内存）
   - 设置环境变量 `DOUBAO_API_KEY`
   - 创建HTTP触发器

4. **测试函数**
   - 使用提供的测试API验证功能
   - 检查日志确保正常运行

详细部署指南请参考：
- [ACR镜像快速部署指南](../docs/ACR镜像快速部署指南.md)
- [基于ACR镜像的阿里云函数部署指南](../docs/基于ACR镜像的阿里云函数部署指南.md)
- [函数实例配置建议](../docs/函数实例配置建议.md)

### 2. 本地开发部署

#### 环境要求
- Python 3.8+
- 豆包大模型 API 密钥

#### 安装依赖

```bash
# 克隆项目
git clone https://github.com/aigcwork/ocrmd2docx.git
cd md2docx

# 安装依赖
pip install -r requirements.txt
```

#### 配置环境变量

创建 `.env` 文件并配置以下变量：

```bash
# 豆包大模型 API 配置
DOUBAO_API_KEY=your_doubao_api_key_here
DOUBAO_API_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
DOUBAO_MODEL=doubao-seed-1-6-251015

# 可选配置
MAX_CONTENT_LENGTH=16777216  # 最大请求内容长度（16MB）
```

#### 运行应用

```bash
# 开发模式运行
python app.py

# 生产模式运行（使用 Gunicorn）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

#### Docker 部署

```bash
# 构建镜像
docker build -t md2docx-backend .

# 运行容器
docker run -d -p 5000:5000 --name md2docx-backend \
  -e DOUBAO_API_KEY=your_doubao_api_key_here \
  md2docx-backend
```

## API 接口

### 1. Markdown 转 Word

**接口地址**: `POST /api/convert`

**请求参数**:
```json
{
  "content": "# 标题\n\n这是要转换的 Markdown 内容"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "转换成功",
  "filename": "document.docx"
}
```

**使用示例**:
```bash
curl -X POST http://localhost:5000/api/convert \
  -H "Content-Type: application/json" \
  -d '{"content": "# 标题\n\n这是要转换的 Markdown 内容"}'
```

### 2. 图片 OCR 识别

**接口地址**: `POST /api/recognize`

**请求参数**:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
  "is_math_mode": false
}
```

**响应示例**:
```json
{
  "success": true,
  "result": "# 识别的标题\n\n这是识别出的内容",
  "model": "doubao-seed-1-6-251015",
  "usage": {
    "prompt_tokens": 1250,
    "completion_tokens": 350,
    "total_tokens": 1600
  }
}
```

**使用示例**:
```bash
curl -X POST http://localhost:5000/api/recognize \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "is_math_mode": false
  }'
```

## 错误处理

### 错误响应格式
```json
{
  "success": false,
  "error": "错误描述信息"
}
```

### 常见错误码

| 错误信息 | 描述 | 解决方案 |
|---------|------|---------|
| 缺少必要参数 | 请求中缺少必需的参数 | 检查请求参数是否完整 |
| 无效的图片格式 | 上传的图片格式不支持 | 使用支持的图片格式（JPEG、PNG、GIF、WebP） |
| 图片文件过大 | 上传的图片文件超过大小限制 | 压缩图片或减小图片尺寸 |
| OCR 服务不可用 | 豆包 API 服务不可用 | 检查 API 密钥和网络连接 |
| API 调用次数超限 | API 调用次数超过限制 | 等待限制重置或升级 API 计划 |

## 日志记录

应用会记录以下类型的日志：
- 请求日志：记录所有 API 请求信息
- 错误日志：记录所有错误信息
- OCR 调用日志：记录 OCR API 调用详情

日志级别可通过环境变量 `LOG_LEVEL` 配置，默认为 `INFO`。

## 性能优化

### 1. 图片处理优化
- 自动压缩大图片以提高识别速度
- 支持多种图片格式
- 智能调整图片对比度和亮度

### 2. API 调用优化
- 设置合理的超时时间
- 实现请求重试机制
- 使用连接池提高并发性能

### 3. 缓存策略
- 对相同图片的识别结果进行缓存
- 设置合理的缓存过期时间

### 4. 函数计算优化
- 配置合适的实例规格和预留实例
- 优化冷启动时间
- 合理设置超时时间
- 使用并发处理提高吞吐量

详细优化方案请参考：
- [图片识别功能优化方案](../docs/图片识别功能优化方案.md)
- [函数实例配置建议](../docs/函数实例配置建议.md)



## 故障排除

### 常见问题

1. **函数冷启动慢**
   - 增加预留实例数量
   - 优化镜像大小
   - 使用预热策略

2. **内存不足错误**
   - 增加内存配置
   - 优化代码内存使用
   - 检查是否有内存泄漏

3. **API调用超时**
   - 增加超时时间配置
   - 优化API调用逻辑
   - 检查网络连接

4. **图片识别失败**
   - 检查API密钥是否正确
   - 验证图片格式是否支持
   - 检查图片大小是否超限

更多故障排除方法请参考：
- [ACR镜像快速部署指南](../docs/ACR镜像快速部署指南.md)
- [基于ACR镜像的阿里云函数部署指南](../docs/基于ACR镜像的阿里云函数部署指南.md)



## 版本更新

### 更新函数代码

1. 修改代码后重新构建镜像
2. 推送新镜像到ACR
3. 在函数计算中更新镜像版本
4. 测试新版本功能

### 版本回滚

1. 在函数计算中选择历史镜像版本
2. 更新函数配置
3. 验证回滚后功能正常

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 安全考虑

### 1. API 密钥安全
- 使用环境变量存储 API 密钥
- 不在代码中硬编码敏感信息
- 定期轮换 API 密钥

### 2. 输入验证
- 验证上传文件类型和大小
- 对输入内容进行安全检查
- 防止恶意输入和注入攻击

### 3. 访问控制
- 实现适当的访问控制机制
- 限制 API 调用频率
- 记录和监控异常访问

## 开发指南

### 1. 项目结构
```
md2docx/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖列表
├── .env.example       # 环境变量示例
├── .dockerignore      # Docker 忽略文件
├── Dockerfile         # Docker 配置文件
├── Dockerfile.acr     # ACR 优化 Docker 配置文件
└── README.md          # 项目说明文档
```

### 2. 添加新功能

1. 在 `app.py` 中添加新的路由处理函数
2. 实现相应的业务逻辑
3. 添加错误处理和日志记录
4. 更新 API 文档

### 3. 测试

使用以下命令运行测试：
```bash
# 安装测试依赖
pip install pytest

# 运行测试
pytest
```

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue: [项目 Issues 页面](https://github.com/aigcwork/ocrmd2docx/issues)
- 邮箱: [ixujue@163.com](mailto:ixujue@163.com)