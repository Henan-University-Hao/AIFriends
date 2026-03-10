import os
from pprint import pprint
from typing import TypedDict, Annotated, Sequence

from django.utils.timezone import localtime, now
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.constants import START, END
from langgraph.graph import add_messages, StateGraph
from langgraph.prebuilt import ToolNode


class ChatGraph:
    @staticmethod
    def create_app():
        @tool
        def get_time() -> str:
            """当需要查询精确时间时, 调用此函数。返回格式为：[年-月-日  时:分:秒]"""
            return localtime(now()).strftime('%Y-%m-%d %H:%M:%S')

        tools = [get_time]

        llm = ChatOpenAI(
            model='deepseek-v3.2',
            openai_api_key=os.getenv('API_KEY'),
            openai_api_base=os.getenv('API_BASE'),
            streaming=True,  # 流式输出
            model_kwargs = {
                "stream_options": {
                    "include_usage": True,  # 输出token消耗数量
                }
            }
        ).bind_tools(tools) # 工具节点绑定到大模型

        # langgraph数据类型:自动把新消息 append 到历史 messages
        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def model_call(state: AgentState) -> AgentState:
            res = llm.invoke(state['messages'])
            return {'messages': [res]}

        def should_continue(state: AgentState) -> str:
            last_message = state['messages'][-1]
            if last_message.tool_calls: ## 非空 → 需要调用工具(tool_calls:内置的标准化属性名)
                return "tools"
            return "end"

        tool_node = ToolNode(tools)

        graph = StateGraph(AgentState) #创建Graph(状态图)
        graph.add_node('agent', model_call) #节点
        graph.add_node('tools', tool_node)

        #两条边
        graph.add_edge(START, 'agent')
        graph.add_conditional_edges(
            'agent',  # 起点节点
            should_continue, # 条件函数
            {  #条件结果与目标节点的映射表(字典的结构是 {返回值: 目标节点})
                'tools': 'tools',
                'end':END,
            }
        )
        graph.add_edge('tools', 'agent')

        return graph.compile()
