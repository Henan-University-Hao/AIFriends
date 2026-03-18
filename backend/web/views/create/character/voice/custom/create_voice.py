import os

import requests

def create_voice(voice_url, prefix):
    # 请求头
    headers = {
        'Authorization': f'Bearer {os.getenv('API_KEY')}',
        'Content-Type': 'application/json',
    }
    # 消息体(请求参数具体参考阿里云文档)
    data = {
        "model": "voice-enrollment",
        "input": {
            "action": "create_voice",
            "target_model": "cosyvoice-v3-plus",
            "prefix": prefix,
            "url": voice_url,
            "language_hints": ["zh"]
        }
    }
    # 发请求
    response = requests.post(os.getenv('VOICE_URL'), headers=headers, json=data)
    return response.json()