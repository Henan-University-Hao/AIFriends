import os

import requests

def delete_voice(voice_id):
    # 请求头
    headers = {
        'Authorization': f'Bearer {os.getenv('API_KEY')}',
        'Content-Type': 'application/json',
    }
    # 消息体(请求参数具体参考阿里云文档)
    data = {
        "model": "voice-enrollment",
        "input": {
            "action": "delete_voice",
            "voice_id": voice_id,
        }
    }
    # 发请求
    response = requests.post(os.getenv('VOICE_URL'), headers=headers, json=data)
    return response.json()