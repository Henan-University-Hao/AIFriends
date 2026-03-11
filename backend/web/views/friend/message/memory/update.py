

from django.utils.timezone import now
from langchain_core.messages import SystemMessage, HumanMessage

from web.models.friend import SystemPrompt, Message
from web.views.friend.message.memory.graph import MemoryGraph

def create_system_message(): #系统提示词
    system_prompts = SystemPrompt.objects.filter(title='记忆').order_by('-order_number')
    prompt = ''
    for system_prompt in system_prompts:
        prompt += system_prompt.prompt
    return SystemMessage(prompt)

def create_human_message(friend): #用户的记忆和最近对话
    prompt = f'【原始记忆】\n{friend.memory}\n'
    prompt += f'【最近对话】\n'
    #最近的10条消息
    messages = list(Message.objects.filter(friend=friend).order_by('-id')[:10])
    messages.reverse()
    for message in messages:
        prompt += f'用户: {message.user_message}\n'
        prompt += f'AI: {message.output}'
    return HumanMessage(prompt)

def update_memory(friend):
    app = MemoryGraph.create_app()

    inputs = { # 输入
        'messages': [
            create_system_message(),
            create_human_message(friend),
        ]
    }

    res = app.invoke(inputs)
    friend.memory = res['messages'][-1].content

    friend.update_time = now()
    friend.save()
