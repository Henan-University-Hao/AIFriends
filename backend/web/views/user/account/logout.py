from rest_framework.response import Response          # DRF 的响应类，用来返回 JSON 数据
from rest_framework.views import APIView               # DRF 提供的基础视图类（支持 GET / POST 等）
from rest_framework.permissions import IsAuthenticated # 权限类：必须是已登录用户才能访问


class LogoutView(APIView):
    # 只有通过认证（携带有效 access token）的用户，才能调用登出接口
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 构造一个响应对象，返回给前端一个登出成功的提示
        response = Response({
            'result': 'success',  # 告诉前端：登出操作已成功
        })

        # 删除浏览器中保存的 refresh_token Cookie
        # 本质：让 refresh token 失效，用户无法再刷新 access token
        response.delete_cookie('refresh_token')

        # 返回响应
        return response
