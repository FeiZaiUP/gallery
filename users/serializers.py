from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()  # 重写avatar字段，调用自定义方法

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'store_name', 'user_type', 'first_name', 'last_name', 'avatar']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return request.build_absolute_uri("/media/default/avatar.png") if request else "/media/default/avatar.png"


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password', 'password2', 'avatar']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match.")
        return data

    def create(self, validated_data):
        avatar = validated_data.pop('avatar', None)
        user = get_user_model().objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        if avatar:
            user.avatar = avatar
            user.save()
        return user
