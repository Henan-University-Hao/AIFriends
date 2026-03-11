# 前端上传音频 → Django 后端做中转 → 第三方 ASR 服务识别 → Django 把文本返回前端

import asyncio
import json
import os
import uuid

import websockets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ASRView(APIView):
    """
    语音识别接口视图

    功能：
    1. 接收前端上传的音频文件
    2. 读取音频二进制内容
    3. 通过 WebSocket 把音频流发送给 ASR 服务
    4. 接收 ASR 服务返回的识别结果
    5. 将最终文本返回给前端
    """

    # 只有登录用户才能访问这个接口
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        处理前端 POST 请求

        前端应通过 form-data 上传一个名为 audio 的音频文件。

        执行流程：
        1. 从 request.FILES 中取出音频文件
        2. 如果没有上传音频，直接返回错误信息
        3. 读取音频的原始二进制数据
        4. 调用异步方法 run_asr_tasks 进行语音识别
        5. 返回识别结果
        """
        audio = request.FILES.get('audio')

        # 如果没有上传音频文件，直接返回
        if not audio:
            return Response({
                'result': '音频不存在'
            })

        # 读取整个音频文件的二进制内容
        # 这里读出来的是 bytes，例如 PCM 原始字节流
        pcm_data = audio.read()

        # 因为 Django 的 post 是同步函数，而 run_asr_tasks 是异步函数，
        # 所以用 asyncio.run() 启动一个事件循环来执行异步任务
        text = asyncio.run(self.run_asr_tasks(pcm_data))

        # 把识别出来的文字返回给前端
        return Response({
            'result': 'success',
            'text': text,
        })

    async def asr_sender(self, pcm_data, ws, task_id):
        """
        音频发送协程：负责把音频数据分块发送给 ASR 服务

        参数：
        - pcm_data: 音频的原始二进制数据
        - ws: 已建立连接的 WebSocket 对象
        - task_id: 当前识别任务的唯一 ID

        逻辑：
        1. 将整段音频按固定大小切块
        2. 逐块通过 WebSocket 发送给服务端
        3. 每次发送后 sleep 0.01 秒，模拟流式发送，避免一次性塞太快
        4. 所有音频发送完后，再发送 finish-task 消息，告诉服务端音频结束
        """
        # 每次发送 3200 字节
        # 这个值通常与采样率、位深、声道数、服务端要求有关
        chunk = 3200

        # 按 chunk 大小遍历音频数据并逐块发送
        for i in range(0, len(pcm_data), chunk):
            await ws.send(pcm_data[i: i + chunk])

            # 稍微暂停一下，模拟实时流式输入
            # 如果不暂停，可能会一次性发太快
            await asyncio.sleep(0.01)

        # 音频发完后，通知服务端“本次任务输入已经结束”
        await ws.send(json.dumps({
            "header": {
                "action": "finish-task",   # 表示结束当前任务
                "task_id": task_id,        # 对应本次识别任务 ID
                "streaming": "duplex"      # 双工流式模式
            },
            "payload": {
                "input": {}
            }
        }))

    async def asr_receiver(self, ws):
        """
        结果接收协程：负责不断接收 ASR 服务返回的消息，并拼接最终识别文本

        参数：
        - ws: WebSocket 连接对象

        返回：
        - text: 最终拼接好的识别文本

        逻辑：
        1. 持续监听 WebSocket 消息
        2. 解析返回事件类型 event
        3. 如果是 result-generated，说明服务端生成了一段识别结果
        4. 如果这一段识别结果 sentence_end=True，表示一句话结束，可以追加到最终文本
        5. 如果收到 task-finished 或 task-failed，说明任务结束，跳出循环
        """
        text = ''

        # async for 会持续从 WebSocket 中读取消息，直到连接关闭或 break
        async for msg in ws:
            # 服务端发来的消息一般是 JSON 字符串，这里转成 Python 字典
            data = json.loads(msg)

            # 获取当前消息的事件类型
            event = data['header']['event']

            # 识别结果生成事件
            if event == 'result-generated':
                output = data['payload']['output']

                # 有些返回可能不包含 transcription，因此先用 get 做安全判断
                # 并且只有 sentence_end 为 True 时，才把这段文本拼到最终结果中
                # 说明这是一句完整的话，而不是中间态
                if output.get('transcription', None) and output['transcription']['sentence_end']:
                    text += output['transcription']['text']

            # 如果任务已经完成或失败，就停止接收
            elif event in ['task-finished', 'task-failed']:
                break

        return text

    async def run_asr_tasks(self, pcm_data):
        """
        语音识别主流程协程

        参数：
        - pcm_data: 音频原始字节数据

        返回：
        - text: ASR 服务识别出的最终文本

        逻辑：
        1. 生成唯一 task_id
        2. 从环境变量中读取 API_KEY 和 WebSocket 地址
        3. 建立 WebSocket 连接
        4. 发送 run-task 消息，告诉服务端要启动一个 ASR 任务
        5. 等待服务端返回 task-started，确认任务已开始
        6. 并发执行：
           - asr_sender：持续发送音频流
           - asr_receiver：持续接收识别结果
        7. 等两个协程都结束后，返回最终文本
        """
        # 生成一个唯一任务 ID，用于标识本次 ASR 任务
        task_id = uuid.uuid4().hex

        # 从环境变量中读取 API Key 和 WebSocket 地址
        api_key = os.getenv('API_KEY')
        wss_url = os.getenv('WSS_URL')

        # WebSocket 握手时带上认证头
        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        # 建立 WebSocket 连接
        # additional_headers 用来在握手时附加 HTTP 请求头
        async with websockets.connect(wss_url, additional_headers=headers) as ws:

            # 发送“启动任务”消息
            # 告诉服务端：
            # - 这是一个音频识别任务
            # - 使用什么模型
            # - 输入音频格式是什么
            # - 需要开启转写功能
            await ws.send(json.dumps({
                "header": {
                    "streaming": "duplex",   # 双工流式：可以一边发一边收
                    "task_id": task_id,      # 当前任务唯一标识
                    "action": "run-task"     # 启动任务
                },
                "payload": {
                    "model": "gummy-realtime-v1",   # 指定模型
                    "parameters": {
                        "sample_rate": 16000,       # 音频采样率 16k
                        "format": "pcm",            # 音频格式为 PCM
                        "transcription_enabled": True,  # 开启转写
                    },
                    "input": {},
                    "task": "asr",                  # 任务类型：自动语音识别
                    "task_group": "audio",         # 任务分组：音频
                    "function": "recognition"      # 功能：识别
                }
            }))

            # 等待服务端确认任务已启动
            # 只有收到 task-started 后，才说明可以开始正式发送音频流
            async for msg in ws:
                if json.loads(msg)['header']['event'] == 'task-started':
                    break

            # 并发执行两个协程：
            # 1. asr_sender：往服务端发送音频流
            # 2. asr_receiver：从服务端接收识别文本
            #
            # gather 返回一个元组：
            # 第一个位置是 asr_sender 的返回值（这里没有 return，所以是 None）
            # 第二个位置是 asr_receiver 的返回值（最终 text）
            _, text = await asyncio.gather(
                self.asr_sender(pcm_data, ws, task_id),
                self.asr_receiver(ws),
            )

            return text