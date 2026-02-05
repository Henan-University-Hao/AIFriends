from django.conf import settings                      # Django 项目配置，用来读取 SIMPLE_JWT 配置
from rest_framework.response import Response          # DRF 的响应类，用来返回 JSON 数据
from rest_framework.views import APIView              # DRF 提供的基础视图类（支持 POST 等）
from rest_framework_simplejwt.tokens import RefreshToken
                                                     # SimpleJWT 提供的 RefreshToken 类，用于解析和生成 token


class RefreshTokenView(APIView):
    def post(self, request):
        try:
            # 从请求的 Cookie 中读取 refresh_token
            # refresh token 通常存放在 HttpOnly Cookie 中，前端 JS 无法直接访问
            refresh_token = request.COOKIES.get('refresh_token')

            # 如果 Cookie 中不存在 refresh_token，说明用户未登录或已退出
            if not refresh_token:
                return Response({
                    'result': 'refresh token 不存在'
                }, status=401)

            # 使用 SimpleJWT 的 RefreshToken 类解析 refresh token
            # 如果 refresh token 已过期或非法，这里会直接抛异常，进入 except
            refresh = RefreshToken(refresh_token)

            # 判断是否开启了 refresh token 轮换机制（ROTATE_REFRESH_TOKENS）
            # 如果开启：每次刷新 access token，都会生成一个新的 refresh token
            if settings.SIMPLE_JWT['ROTATE_REFRESH_TOKENS']:
                # 生成新的 jti（JWT ID），使旧的 refresh token 失效
                refresh.set_jti()

                # 构造响应，返回新的 access token
                response = Response({
                    'result': 'success',
                    'access': str(refresh.access_token),  # 返回新的 access token 给前端
                })

                # 将新的 refresh token 写入 Cookie
                response.set_cookie(
                    key='refresh_token',      # Cookie 名称，用于存储 refresh token
                    value=str(refresh),       # 新生成的 refresh token
                    httponly=True,            # 仅后端可访问，防止 XSS 攻击
                    samesite='Lax',            # 限制跨站请求携带 Cookie，安全与兼容性折中
                    secure=True,               # 仅在 HTTPS 下发送 Cookie
                    max_age=86400 * 7,         # Cookie 有效期：7 天（单位：秒）
                )

                # 返回包含新 access token 的响应
                return response

            # 如果没有开启 refresh token 轮换机制
            # 则只返回新的 access token，refresh token 仍然使用旧的
            return Response({
                'result': 'success',
                'access': str(refresh.access_token),
            })

        except:
            # 捕获 refresh token 解析异常（通常是过期、伪造或格式错误）
            return Response({
                'result': 'refresh token 过期了'
            }, status=401)
