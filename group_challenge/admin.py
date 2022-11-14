from group_challenge.models import UserChallenge
from django.contrib import admin


@admin.register(UserChallenge)
class UserAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = [
        "user","opponent","challenge","is_random_opponent","created_challenge_message_id","created_challenge_chat_id",
    ]
    