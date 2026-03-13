import asyncio
import base64
import json
import os
import threading
import uuid
from queue import Queue

import websockets
from django.http import StreamingHttpResponse
from langchain_core.messages import HumanMessage, BaseMessageChunk, SystemMessage, AIMessage
from rest_framework.renderers import BaseRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle

from web.models.friend import Friend, Message, SystemPrompt
from web.views.friend.message.chat.graph import ChatGraph
from web.views.friend.message.memory.update import update_memory


class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'txt'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

def add_system_prompt(state, friend): #添加提示词
    messages = state['messages']
    system_prompts = SystemPrompt.objects.filter(title='回复').order_by('order_number')
    prompt = ''
    for system_prompt in system_prompts:
        prompt += system_prompt.prompt
    prompt += f'\n【角色性格】\n{friend.character.profile}\n' # 角色的简介描述
    prompt += f'【长期记忆】{friend.memory}\n' # 对用户的长期记忆
    return {'messages': [SystemMessage(prompt)] + messages}

def add_recent_messages(state, friend): #添加最近的对话
    messages = state['messages']
    message_raw = list(Message.objects.filter(friend=friend).order_by('-id'))
    message_raw.reverse()
    recent_messages = []
    for message in message_raw:
        recent_messages.append(HumanMessage(message.user_message))
        recent_messages.append(AIMessage(message.output))
    return {'messages': messages[:1] + recent_messages + messages[-1:],} #对话添加到系统提示词和最后一条用户提问中间


class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'chat'
    renderer_classes = [SSERenderer]
    def post(self, request):
        friend_id = request.data['friend_id']
        message = request.data['message'].strip()
        if not message:
            return Response({
                'result': '消息不能为空'
            })
        friends = Friend.objects.filter(pk=friend_id, me__user=request.user)
        if not friends.exists():
            return Response({
                'result': '好友不存在'
            })
        friend = friends.first()
        app = ChatGraph.create_app()

        inputs = {
            'messages': [HumanMessage(message)]
        }
        inputs = add_system_prompt(inputs, friend)
        inputs = add_recent_messages(inputs, friend)

        response = StreamingHttpResponse(self.event_stream(app, inputs, friend, message), content_type='text/event-stream') # 创建流式 HTTP 响应，指定 SSE 标准 MIME 类型
        response['Cache-Control'] = 'no-cache' #禁止浏览器/代理缓存该响应
        response['X-Accel-Buffering'] = 'no' # 禁止nginx缓存
        return response

    async def tts_sender(self, app, inputs, message_queue, ws, task_id):
        """
        TTS 发送协程：
        1. 从大模型流式拿到文本 chunk
        2. 每拿到一段文本，就通过 WebSocket 发给 TTS 服务继续合成
        3. 同时把文本片段塞进消息队列，供 SSE 主线程返回给前端
        4. 如果拿到 token 使用量，也一并塞进队列
        5. 全部文本发送完后，通知 TTS 服务 finish-task
        """
        async for msg, metadata in app.astream(inputs, stream_mode="messages"):
            # astream(..., stream_mode="messages") 会流式返回消息块
            if isinstance(msg, BaseMessageChunk):
                if msg.content:
                    # 告诉 TTS 服务：继续处理新的文本片段
                    await ws.send(json.dumps({
                        "header": {
                            "action": "continue-task",
                            "task_id": task_id,   # 当前 TTS 任务唯一标识
                            "streaming": "duplex" # duplex 表示双工流式通信
                        },
                        "payload": {
                            "input": {
                                "text": msg.content,  # 本次新生成的文本片段
                            }
                        }
                    }))

                    # 把文本片段放入队列，供 event_stream() 通过 SSE 发给前端
                    message_queue.put_nowait({'content': msg.content})

                # 某些模型在流式 chunk 中会携带 usage 元数据
                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    message_queue.put_nowait({'usage': msg.usage_metadata})

        # 模型文本全部生成结束后，通知 TTS 服务：输入结束
        await ws.send(json.dumps({
            "header": {
                "action": "finish-task",
                "task_id": task_id,
                "streaming": "duplex"
            },
            "payload": {
                "input": {}  # 某些 TTS 服务要求 input 不能省略
            }
        }))

    async def tts_receiver(self, message_queue, ws):
        """
        TTS 接收协程：
        持续接收 TTS 服务返回的数据。

        返回的数据分两类：
        1. bytes：音频二进制分片
        2. str/json：任务状态事件，如 task-finished / task-failed
        """
        async for msg in ws:
            if isinstance(msg, bytes):
                # SSE 是文本协议，不能直接传二进制音频
                # 所以先把音频 bytes 转成 base64 字符串再发给前端
                audio = base64.b64encode(msg).decode('utf-8')
                message_queue.put_nowait({'audio': audio})
            else:
                # 文本消息一般是事件控制信息
                data = json.loads(msg)
                event = data['header']['event']

                # 任务完成或失败时结束接收循环
                if event in ['task-finished', 'task-failed']:
                    break

    async def run_tts_tasks(self, app, inputs, message_queue):
        """
        整个 TTS 异步总控函数：
        1. 建立到 TTS 平台的 WebSocket 连接
        2. 发送 run-task 启动 TTS 任务
        3. 等待 task-started
        4. 并发执行 sender / receiver 两个协程
        """
        task_id = uuid.uuid4().hex  # 为本次 TTS 会话生成唯一任务 ID

        api_key = os.getenv('API_KEY')
        wss_url = os.getenv('wss_url')

        headers = {'Authorization': f'Bearer {api_key}'}

        # 连接远程 TTS WebSocket 服务
        async with websockets.connect(wss_url, additional_headers=headers) as ws:
            # 启动一个 TTS 任务
            await ws.send(json.dumps({
                "header": {
                    "action": "run-task",
                    "task_id": task_id,   # 本次 TTS 任务的唯一 ID
                    "streaming": "duplex" # 双工：可一边发文本，一边收音频
                },
                "payload": {
                    "task_group": "audio",
                    "task": "tts",
                    "function": "SpeechSynthesizer",
                    "model": "cosyvoice-v3-flash",
                    "parameters": {
                        "text_type": "PlainText",
                        "voice": "longanyang",  # 音色
                        "format": "mp3",        # 输出音频格式
                        "sample_rate": 22050,   # 采样率
                        "volume": 50,           # 音量
                        "rate": 1.5,           # 语速
                        "pitch": 1              # 音调
                    },
                    "input": {
                        # 某些服务端要求 input 字段必须存在，即使一开始为空
                    }
                }
            }))

            # 等待服务端返回 task-started，表示 TTS 任务已成功启动
            # 你原来的判断写反了：
            # if json.loads(msg)['header']['event'] != 'task-started': break
            # 这样会在“不是 task-started”时 break，逻辑不对
            async for msg in ws:
                if json.loads(msg)['header']['event'] == 'task-started':
                    break

            # 并发执行两个协程：
            # 1. sender：从大模型拿文本 -> 发给 TTS -> 塞文本到队列
            # 2. receiver：从 TTS 收音频/事件 -> 塞音频到队列
            await asyncio.gather(
                self.tts_sender(app, inputs, message_queue, ws, task_id),
                self.tts_receiver(message_queue, ws),
            )


    def work(self, app, inputs, messaage_queue):
        """
               线程入口函数：
               在子线程中创建并运行 asyncio 事件循环，
               避免在同步 Django 视图里直接处理复杂异步逻辑。

               无论执行成功还是失败，最后都向队列塞一个 None，
               作为“整个流式任务结束”的信号。
        """
        try:
            asyncio.run(self.run_tts_tasks(app, inputs, messaage_queue))
        finally:
            messaage_queue.put_nowait(None)

    # 模型回复改为流式的回复
    def event_stream(self, app, inputs, friend, message):
        """
                SSE 数据生成器：
                1. 创建消息队列
                2. 启动后台线程执行异步 TTS 任务
                3. 主线程不断从队列中取出文本/音频/usage
                4. 用 yield 按 SSE 格式推送给前端
                5. 最后落库并更新长期记忆
        """
        message_queue = Queue() # 消息队列

        # 后台线程启动异步TTS总任务
        thread = threading.Thread(target=self.work, args=(app, inputs,message_queue))
        thread.start()

        full_usage = {}
        full_output = ''
        while True:
            msg = message_queue.get()
            if not msg:
                break
            if msg.get('content', None):
                full_output += msg['content']
                yield f'data: {json.dumps({'content': msg['content']}, ensure_ascii=False)}\n\n'
            if msg.get('audio', None):
                yield f'data: {json.dumps({'audio': msg['audio']}, ensure_ascii=False)}\n\n'
            if msg.get('usage', None):
                full_usage = msg['usage']
        yield "data: [DONE]\n\n"  # 流式响应结束，返回 [DONE] 标识，告知前端流已结束

        input_tokens = full_usage.get('input_tokens', 0)
        output_tokens = full_usage.get('output_tokens', 0)
        total_tokens = full_usage.get('total_tokens', 0)
        Message.objects.create(
            friend=friend,
            user_message=message[:500],
            input=json.dumps(  # 把 inputs['messages'] 中的消息对象列表 → 转换为 JSON 字符串 → 保留中文 → 截断到 10000 字符。
                [m.model_dump() for m in inputs['messages']],
                ensure_ascii=False,
            )[:10000],
            output=full_output[:500],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

        if Message.objects.filter(friend=friend).count() % 1 == 0:
            update_memory(friend)
