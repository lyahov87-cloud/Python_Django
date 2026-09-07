from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    # Достаем поля из связанной модели User
    fullName = serializers.CharField(source='user.first_name', default="")
    email = serializers.EmailField(source='user.email', default="")
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['fullName', 'email', 'phone', 'avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            return {"src": obj.avatar.url, "alt": obj.user.username}
        return {"src": "", "alt": "no avatar"}
