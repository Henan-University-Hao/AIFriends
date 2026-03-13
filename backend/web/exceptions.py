# 全局异常处理
from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, Throttled):
        detail = '操作过快了，请稍后再试'
        if exc.wait:
            seconds = max(1, int(exc.wait))
            detail = f'{detail}，约 {seconds} 秒后再试'
        response.data = {'detail': detail}

    return response
