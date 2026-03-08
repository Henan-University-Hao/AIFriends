from django.contrib import admin

from web.models.friend import Friend, Message
from web.models.user import UserProfile
from web.models.character import Character

@admin.register(UserProfile)
class UserAdmin(admin.ModelAdmin):
    # 在 Django Admin 中注册模型后，所有增删改查都会走 ORM，
    # ORM 再通过 settings.py 的 DATABASES 配置连接到 sqlite3。
    # 最终 SQL 由 Django 生成并执行，数据写入 db.sqlite3 文件。
    raw_id_fields = ('user',)  # 外键/一对一字段用输入框，避免下拉加载过多数据。

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    raw_id_fields = ('author',)


@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    raw_id_fields = ('me', 'character',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    raw_id_fields = ('friend',)

