import os
import uuid
import subprocess
import base64
import json
import requests
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

# -----------------------------------------------------------------------------
# 1. 初始化 Flask 应用
# -----------------------------------------------------------------------------
# 创建 Flask app 实例
app = Flask(__name__)

# 使用 Flask-Cors 扩展来处理跨域请求，允许任何来源访问我们的 API
CORS(app)

# -----------------------------------------------------------------------------
# 2. 豆包大模型API配置
# -----------------------------------------------------------------------------
# 豆包大模型API配置
DOUBAO_API_CONFIG = {
    "url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "model": "doubao-seed-1-6-251015",  # 豆包模型ID
    "api_key": os.environ.get("DOUBAO_API_KEY"),  # 从环境变量读取API密钥，必须设置
    "max_tokens": 4000,  # 最大令牌数
    "temperature": 0.1  # 温度参数，控制随机性
}

# -----------------------------------------------------------------------------
# 3. 定义临时文件存储目录
# -----------------------------------------------------------------------------
# 函数计算环境的可写目录是 /tmp
# 我们将在这里存放转换过程中的临时 .md 和 .docx 文件
TEMP_DIR = '/tmp'

# -----------------------------------------------------------------------------
# 3. 创建核心的 API 转换接口
# -----------------------------------------------------------------------------
# 定义一个 API 路由，地址为 /api/convert，只接受 POST 方法的请求
@app.route('/api/convert', methods=['POST'])
def convert_markdown_to_docx():
    """
    接收 Markdown 文本，使用 Pandoc 将其转换为 DOCX 文件，并返回该文件。
    """
    # --- 安全检查：确保收到的数据是 JSON 格式 ---
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    # --- 获取请求中的 Markdown 内容 ---
    data = request.get_json()
    markdown_content = data.get('markdown')

    if not markdown_content:
        return jsonify({"error": "Missing 'markdown' key in request body"}), 400

    # --- 创建唯一的临时文件名，避免并发请求时文件冲突 ---
    # 使用 uuid 生成一个随机的、几乎不可能重复的字符串
    unique_id = str(uuid.uuid4())
    input_md_path = os.path.join(TEMP_DIR, f'{unique_id}.md')
    output_docx_path = os.path.join(TEMP_DIR, f'{unique_id}.docx')

    # --- 使用 try...finally 结构确保临时文件总能被清理 ---
    try:
        # --- 将收到的 Markdown 内容写入临时文件 ---
        # 使用 utf-8 编码以支持中文和各种特殊符号
        with open(input_md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # --- 构建并执行 Pandoc 命令行指令 ---
        command = [
            'pandoc',
            '--from', # 输入格式
            'markdown+tex_math_dollars+tex_math_single_backslash', # 支持 LaTeX 数学公式
            input_md_path,
            '-o',
            output_docx_path,
            '--reference-doc=/app/reference.docx' #新添加的引用文档参数，参考格式，输出中文
        ]
        
        # 使用 subprocess.run 执行命令，这是更现代、更安全的方式
        # timeout=30: 设置30秒超时，防止 pandoc 因异常输入而卡死
        result = subprocess.run(
            command, 
            capture_output=True,  # 捕获标准输出和标准错误
            text=True,            # 以文本形式解码输出
            timeout=30
        )

        # --- 检查 Pandoc 是否成功执行 ---
        # 如果 result.returncode 不为 0，说明 pandoc 执行失败
        if result.returncode != 0:
            # 将 pandoc 的错误信息返回给前端，方便排查问题
            print("Pandoc Error:", result.stderr) # 在函数计算日志中打印错误
            return jsonify({
                "error": "Pandoc conversion failed",
                "details": result.stderr
            }), 500

        # --- 检查输出文件是否存在 ---
        if not os.path.exists(output_docx_path):
             return jsonify({"error": "Converted file not found on server"}), 500

        # --- 成功，将生成的 DOCX 文件作为附件发回给客户端 ---
        return send_file(
            output_docx_path,
            as_attachment=True,
            # 这是用户下载时看到的文件名
            download_name='converted_document.docx',
            # 这是标准的 docx 文件 MIME 类型
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    finally:
        # --- 清理战场：删除临时文件 ---
        # 无论转换成功还是失败，这个代码块都会执行
        if os.path.exists(input_md_path):
            os.remove(input_md_path)
        if os.path.exists(output_docx_path):
            os.remove(output_docx_path)

# -----------------------------------------------------------------------------
# 5. 健康检查端点
# -----------------------------------------------------------------------------
@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查端点，用于函数计算服务健康检查
    """
    return jsonify({"status": "healthy", "service": "md2docx-api"}), 200

# -----------------------------------------------------------------------------
# 6. 图片识别API接口
# -----------------------------------------------------------------------------
@app.route('/api/recognize', methods=['POST'])
def recognize_image():
    """
    接收图片文件，使用豆包大模型API识别图片中的文本，并返回Markdown格式的文本。
    """
    # 检查是否有文件上传
    if 'image' not in request.files:
        return jsonify({"success": False, "message": "没有上传图片"}), 400
    
    file = request.files['image']
    
    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({"success": False, "message": "没有选择文件"}), 400
    
    # 检查文件大小（限制为10MB）
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # 重置文件指针
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        return jsonify({"success": False, "message": "图片文件过大，请上传小于10MB的图片"}), 400
    
    # 获取识别选项
    mode = request.form.get('mode', 'text')  # 默认为文本模式
    include_math = request.form.get('includeMath', 'false').lower() == 'true'
    include_tables = request.form.get('includeTables', 'false').lower() == 'true'
    
    try:
        # 读取图片文件并转换为base64（不进行压缩，保持原始质量）
        image_bytes = file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 构建请求提示词
        prompt = build_recognition_prompt(mode, include_math, include_tables)
        
        # 调用豆包大模型API
        response = call_doubao_api(image_base64, prompt)
        
        # 处理API响应
        markdown_text = process_api_response(response, mode, include_math, include_tables)
        
        # 返回识别结果
        return jsonify({
            "success": True,
            "markdown": markdown_text,
            "mode": mode,
            "includeMath": include_math,
            "includeTables": include_tables
        })
        
    except Exception as e:
        print(f"图片识别错误: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"图片识别失败: {str(e)}"
        }), 500

def build_recognition_prompt(mode, include_math, include_tables):
    """
    构建图片识别的提示词
    """
    if mode == "text":
        return "请识别图片中的文本内容，只返回纯文本，保留基本段落结构。"
    elif mode == "document":
        prompt = "请识别图片中的文本内容，保持原文档的格式。"
        
        if include_math:
            prompt += "数学公式用LaTeX格式表示。"
            
        if include_tables:
            prompt += "表格用Markdown表格格式表示。"
            
        return prompt
    
    return "请识别图片中的文本内容。"

def check_api_key():
    """
    检查API密钥是否已设置
    """
    api_key = DOUBAO_API_CONFIG["api_key"]
    if not api_key:
        raise ValueError("API密钥未设置。请设置环境变量 DOUBAO_API_KEY")
    return api_key

def call_doubao_api(image_base64, prompt):
    """
    调用豆包大模型API进行图片识别
    """
    # 检查API密钥是否已设置
    api_key = check_api_key()
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": DOUBAO_API_CONFIG["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": DOUBAO_API_CONFIG["max_tokens"],
        "temperature": DOUBAO_API_CONFIG["temperature"]
    }
    
    print(f"API URL: {DOUBAO_API_CONFIG['url']}")
    print(f"API Model: {DOUBAO_API_CONFIG['model']}")
    print(f"API Key: {api_key[:10]}...")  # 只打印前10个字符
    print(f"Image base64 length: {len(image_base64)}")
    print(f"Prompt: {prompt}")
    
    try:
        # 增加超时时间到120秒，适应更大的图片
        response = requests.post(
            DOUBAO_API_CONFIG["url"],
            headers=headers,
            json=payload,
            timeout=120  # 增加超时时间到120秒
        )
        
        print(f"Response Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response Body: {response.text}")
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as e:
        print(f"API请求超时: {str(e)}")
        raise Exception(f"API请求超时，请重试或尝试更小的图片")
    except Exception as e:
        print(f"API请求失败: {str(e)}")
        raise

def process_api_response(response, mode, include_math, include_tables):
    """
    处理豆包API的响应，提取Markdown文本
    """
    try:
        # 提取API响应中的文本内容
        content = response["choices"][0]["message"]["content"]
        
        # 确保返回的是有效的Markdown格式
        if not content.strip():
            return ""
            
        # 根据模式进行后处理
        if mode == "text":
            # 纯文本模式，移除可能的Markdown标记
            import re
            # 移除标题标记
            content = re.sub(r'^#+\s', '', content, flags=re.MULTILINE)
            # 移除列表标记
            content = re.sub(r'^\s*[-*+]\s', '', content, flags=re.MULTILINE)
            # 移除数字列表标记
            content = re.sub(r'^\s*\d+\.\s', '', content, flags=re.MULTILINE)
            
        return content.strip()
        
    except (KeyError, IndexError) as e:
        print(f"处理API响应错误: {str(e)}")
        return ""



# 注意：在函数计算环境中，我们不需要 app.run()
# Gunicorn 会直接从 Dockerfile 的 CMD 指令启动 app。
# 下面的代码块仅用于本地测试，在生产环境中不会被执行。
if __name__ == '__main__':
    # 在本地 5001 端口上以调试模式运行
    app.run(host='0.0.0.0', port=5001, debug=True)