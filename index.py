import json
from app import app

def handler(environ, start_response):
    """
    阿里云函数计算入口函数 - WSGI模式
    """
    return app(environ, start_response)

def handler_http(event, context):
    """
    阿里云函数计算入口函数 - HTTP触发器模式
    """
    # 解析事件
    try:
        # 如果是HTTP触发器，event会是字典格式
        if isinstance(event, dict):
            # 获取请求信息
            path = event.get('path', '/')
            method = event.get('httpMethod', 'GET')
            headers = event.get('headers', {})
            queryParameters = event.get('queryParameters', {})
            body = event.get('body', '')
            
            # 构建Werkzeug环境
            environ = {
                'REQUEST_METHOD': method,
                'PATH_INFO': path,
                'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in queryParameters.items() if v is not None]),
                'CONTENT_TYPE': headers.get('Content-Type', ''),
                'CONTENT_LENGTH': str(len(body)) if body else '0',
                'wsgi.input': type('MockInput', (), {'read': lambda self, size: body.encode()})(),
                'wsgi.version': (1, 0),
                'wsgi.errors': type('MockErrors', (), {'write': lambda self, x: None})(),
                'wsgi.multithread': False,
                'wsgi.multiprocess': False,
                'wsgi.run_once': False,
                'wsgi.url_scheme': 'https',
            }
            
            # 添加HTTP头
            for key, value in headers.items():
                key = key.upper().replace('-', '_')
                if key not in ['CONTENT_TYPE', 'CONTENT_LENGTH']:
                    environ[f'HTTP_{key}'] = value
            
            # 创建响应收集器
            response_data = {}
            
            def start_response(status, response_headers):
                response_data['status'] = status
                response_data['headers'] = response_headers
            
            # 调用Flask应用
            app_iter = app(environ, start_response)
            response_body = b''.join(app_iter)
            
            # 解析状态码
            status_code = int(response_data['status'].split(' ')[0])
            
            # 构建响应头
            response_headers = {}
            for key, value in response_data['headers']:
                response_headers[key] = value
            
            # 返回函数计算格式的响应
            return {
                'statusCode': status_code,
                'headers': response_headers,
                'body': response_body.decode('utf-8'),
                'isBase64Encoded': False
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }