# Django 内置用户模型（auth_user 表）
from django.contrib.auth.models import User

# 获取当前时间（支持时区）
from django.utils.timezone import now

# DRF 的基础视图类
from rest_framework.views import APIView
# DRF 返回 JSON 用的 Response
from rest_framework.response import Response
# DRF 权限类：要求必须登录
from rest_framework.permissions import IsAuthenticated

from web.models.user import UserProfile
from web.views.utils.photo import remove_old_photo


class UpdateProfileVIew(APIView):
    # 只有通过认证的用户才能访问该接口
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 获取当前登录用户（由 DRF 自动注入）
            user = request.user

            # 获取该用户对应的扩展信息（一对一）
            user_profile = UserProfile.objects.get(user=user)

            # 从前端 POST 的数据中取字段
            # strip() 去除前后空格
            username = request.data.get('username').strip()
            profile = request.data.get('profile').strip()[:500]  # 限制最大 500 字
            photo = request.FILES.get('photo', None)  # 获取上传的头像文件（可能没有）

            # 4. 参数校验：用户名不能为空
            if not username:
                return Response({
                    'result': '用户名不能为空'
                })

            # 5. 参数校验：个人简介不能为空
            if not profile:
                return Response({
                    'result': '简介不能为空'
                })

            # 如果用户名被修改了，需要检查是否已存在
            # 注意：允许用户保持原用户名
            if username != user.username and User.objects.filter(username=username).exists():
                return Response({
                    'result': '用户名已存在'
                })

            # 如果上传了新头像
            if photo:
                # 删除旧头像文件（避免磁盘垃圾）
                remove_old_photo(user_profile.photo)
                # 更新头像字段
                user_profile.photo = photo

            # 更新个人简介
            user_profile.profile = profile
            # 更新时间
            user_profile.update_time = now()
            # 保存用户扩展信息
            user_profile.save()
            # 更新 auth_user 表中的用户名
            user.username = username
            user.save()

            # 12. 返回成功结果
            return Response({
                'result': 'success',
                'user_id': user.id,
                'username': user.username,
                'profile': user_profile.profile,
                'photo': user_profile.photo.url if user_profile.photo else '',
            })

        except Exception as e:
            # 捕获所有异常（生产环境不推荐裸 except）
            return Response({
                'result': '系统异常，请稍后重试'
            })
