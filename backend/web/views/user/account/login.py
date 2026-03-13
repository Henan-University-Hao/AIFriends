from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from web.models.user import UserProfile


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    # 登录接口：接收用户名/密码，认证通过后签发 JWT 并返回用户信息。
    def post(self, request, *args, **kwargs):
        # 使用 try/except 防止认证流程中的异常导致接口崩溃。
        try:
            # 从请求体中读取账号信息（DRF 会把 JSON 解析到 request.data）。
            username = request.data.get('username').strip()
            password = request.data.get('password').strip()
            # 账号或密码为空时，直接返回错误信息。
            if not username or not password:
                return Response({
                    'result': '用户名和密码不能为空',
                })
            # 调用 Django 认证系统校验用户名与密码。
            user = authenticate(username=username, password=password)
            if user:
                # 获取扩展的用户资料（头像、简介等）。
                user_profile = UserProfile.objects.get(user=user)
                # 生成刷新令牌，并从中得到访问令牌。
                refresh = RefreshToken.for_user(user)
                response = Response({
                    'result': 'success',
                    'access': str(refresh.access_token),
                    'user_id':user.id,
                    'username':user.username,
                    'photo': user_profile.photo.url,
                    'profile': user_profile.profile,
                })
                response.set_cookie(
                    key='refresh_token',  # Cookie 的名字，这里用来存刷新用的 token
                    value=str(refresh),  # Cookie 的值，通常是 refresh token（转成字符串）
                    httponly=True,  # 只允许后端访问，前端 JS 不能通过 document.cookie 读取（防 XSS）
                    samesite='Lax',  # 限制跨站请求携带 Cookie，Lax 模式在普通跳转时允许，安全性和兼容性折中
                    secure=True,  # 只在 HTTPS 请求中发送 Cookie（HTTP 下不会发送）
                    max_age=86400 * 7,  # Cookie 的存活时间（单位：秒），这里是 7 天
                )
                return response
            else: #user为空时的错误信息
                return Response({
                    'result': '用户名或密码错误'
                })
        except:
            # 捕获未知异常，避免抛栈信息暴露给客户端。
            return Response({
                'result': '系统异常，请稍后重试',
            })

# 本文件中用到的函数说明：
# - authenticate(username, password)：调用 Django 认证后端校验账号密码，成功返回 User，否则 None。
# - RefreshToken.for_user(user)：为指定用户生成刷新令牌，可派生访问令牌。
# - UserProfile.objects.get(user=...)：通过 ORM 查询用户扩展资料，不存在会抛异常。
# - Response(data)：构建 DRF 响应对象，自动序列化为 JSON。
# - request.data.get(key)：从请求体中读取字段，通常来自 JSON 或表单数据。

