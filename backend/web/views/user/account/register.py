from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from web.models.user import UserProfile


class RegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'
    def post(self, request):
        try:
            username = request.data['username'].split()
            password = request.data['password'].split()
            if not username or not password:
                return Response({
                    'result': '用户名和密码不能为空',
                })
            if User.objects.filter(username=username[0]).exists():
                return Response({
                    'result': '用户名已存在'
                })
            user = User.objects.create_user(username=username[0], password=password[0])
            user_profile = UserProfile.objects.create(user=user)
            refresh = RefreshToken.for_user(user)
            response = Response({
                'result': 'success',
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
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
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
