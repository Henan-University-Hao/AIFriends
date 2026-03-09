import json

from django.http import StreamingHttpResponse
from langchain_core.messages import HumanMessage, BaseMessageChunk
from rest_framework.renderers import BaseRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.friend import Friend, Message
from web.views.friend.message.chat.graph import ChatGraph

class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'txt'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data

class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]
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

        #模型回复改为流式的回复
        def event_stream():
            full_usage = {}
            full_output = ''
            for msg, metadata in app.stream(inputs, stream_mode='messages'): # 判断当前消息是否为消息块（流式返回的消息通常以块的形式逐步返回）
                if isinstance(msg, BaseMessageChunk):
                    if msg.content:
                        full_output += msg.content
                        # 以 SSE (Server-Sent Events) 格式生成数据
                        # json.dumps 确保中文等非 ASCII 字符正常显示（ensure_ascii=False）
                        # 格式要求：data: {内容}\n\n
                        yield f'data: {json.dumps({'content': msg.content}, ensure_ascii=False)}\n\n'
                    if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                        full_usage = msg.usage_metadata
            yield "data: [DONE]\n\n" # 流式响应结束，返回 [DONE] 标识，告知前端流已结束

            input_tokens = full_usage.get('input_tokens', 0)
            output_tokens = full_usage.get('output_tokens', 0)
            total_tokens = full_usage.get('total_tokens', 0)
            Message.objects.create(
                friend=friend,
                user_message=message[:500],
                input=json.dumps(           # 把 inputs['messages'] 中的消息对象列表 → 转换为 JSON 字符串 → 保留中文 → 截断到 10000 字符。
                    [m.model_dump() for m in inputs['messages']],
                    ensure_ascii=False,
                )[:10000],
                output=full_output[:500],
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
            )

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream') # 创建流式 HTTP 响应，指定 SSE 标准 MIME 类型
        response['Cache-Control'] = 'no-cache' #禁止浏览器/代理缓存该响应
        return response