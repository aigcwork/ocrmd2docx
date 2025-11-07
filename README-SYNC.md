# MD2DOCX - 代码仓库同步构建版本

这是一个基于阿里云函数计算的Markdown转Word文档服务，支持代码仓库同步构建。

## 项目结构

```
md2docx/
├── app.py                 # Flask应用主文件
├── requirements.txt       # Python依赖清单
├── Dockerfile.sync       # Docker构建文件（用于代码仓库同步）
├── template-sync.yml     # 函数计算配置文件（用于代码仓库同步）
├── .dockerignore         # Docker忽略文件
├── .gitignore           # Git忽略文件
└── README.md            # 本文件
```

## 功能特性

1. **Markdown转Word**：使用Pandoc将Markdown文本转换为Word文档
2. **图片识别**：使用豆包大模型API识别图片中的文本，支持数学公式和表格
3. **代码仓库同步**：支持从GitHub/Gitee等仓库自动拉取代码并构建
4. **无服务器部署**：基于阿里云函数计算，无需管理服务器

## 部署方式

### 代码仓库同步构建

1. 将代码推送到GitHub/Gitee等代码仓库
2. 在阿里云函数计算控制台创建服务
3. 配置代码仓库同步构建
4. 设置环境变量和HTTP触发器

详细步骤请参考：[代码仓库同步构建指南](../docs/代码仓库同步构建指南.md)

## 环境变量

- `DOUBAO_API_KEY`：豆包大模型API密钥（必需）
- `PYTHONUNBUFFERED`：设置为`1`以立即输出日志
- `TMPDIR`：设置为`/tmp`以使用函数计算的临时目录

## API接口

### 1. Markdown转Word

- **URL**: `/api/convert`
- **方法**: POST
- **请求体**:
  ```json
  {
    "markdown": "# 标题\n\n这是段落内容。"
  }
  ```
- **响应**: Word文档文件

### 2. 图片识别

- **URL**: `/api/recognize`
- **方法**: POST
- **请求体**: multipart/form-data
  - `image`: 图片文件
  - `mode`: 识别模式（text/document）
  - `includeMath`: 是否包含数学公式（true/false）
  - `includeTables`: 是否包含表格（true/false）
- **响应**:
  ```json
  {
    "success": true,
    "markdown": "识别后的Markdown文本",
    "mode": "document",
    "includeMath": true,
    "includeTables": true
  }
  ```

### 3. 健康检查

- **URL**: `/health`
- **方法**: GET
- **响应**:
  ```json
  {
    "status": "healthy",
    "service": "md2docx-api"
  }
  ```

## 本地开发

### 环境准备

1. 安装Python 3.9+
2. 安装Pandoc
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

### 运行应用

1. 设置环境变量：
   ```bash
   export DOUBAO_API_KEY=your_api_key
   ```

2. 运行应用：
   ```bash
   python app.py
   ```

3. 访问 http://localhost:5001

## 注意事项

1. **代码仓库结构**：确保所有必要文件都在仓库中，包括Dockerfile.sync和template-sync.yml
2. **依赖版本**：requirements.txt中的依赖版本需要与阿里云函数计算环境兼容
3. **临时文件**：所有临时文件都保存在/tmp目录中，这是函数计算环境中唯一可写的目录
4. **超时设置**：函数计算的超时时间需要足够长，以处理大文件或复杂图片

## 故障排除

### 构建失败

1. 检查代码仓库结构是否正确
2. 检查Dockerfile.sync中的命令是否正确
3. 检查requirements.txt中的依赖是否兼容

### 运行时错误

1. 检查环境变量是否正确设置
2. 查看函数计算控制台的日志
3. 检查端口配置是否正确（9000）

### API调用失败

1. 检查豆包API密钥是否有效
2. 检查网络连接是否正常
3. 检查请求格式是否正确

## 更新日志

- v1.0.0: 初始版本，支持Markdown转Word和图片识别
- v1.1.0: 添加代码仓库同步构建支持
- v1.2.0: 优化Docker构建过程，减小镜像体积