import os

import requests

def list_voice():
    # 请求头
    headers = {
        'Authorization': f'Bearer {os.getenv('API_KEY')}',
        'Content-Type': 'application/json',
    }
    # 消息体(请求参数具体参考阿里云文档)
    data = {
        "model": "voice-enrollment",
        "input": {
            "action": "list_voice",
            "page_size": 100,
            "page_index": 0
        }
    }
    # 发请求
    response = requests.post(os.getenv('VOICE_URL'), headers=headers, json=data)
    return response.json()