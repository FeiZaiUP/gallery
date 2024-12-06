from .models import Image, ShareLink, Tag
from rest_framework import serializers
from django.db import IntegrityError
import uuid


def generate_unique_share_code():
    while True:
        # 每次生成新的 share_code
        share_code = uuid.uuid4().hex
        if not ShareLink.objects.filter(share_code=share_code).exists():
            return share_code


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

    def create(self, validated_data):
        user = self.context['request'].user  # 获取当前请求的用户
        validated_data['uploaded_by'] = user  # 将标签的上传用户设置为当前用户
        return super().create(validated_data)


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'title', 'file', 'created_at', 'tags']  # 只展示必要的字段
        read_only_fields = ['uploaded_by', 'created_at']  # id 和 created_at 不允许修改

    def validate_description(self, value):
        if not value:
            return "No description"  # 默认描述
        return value


class ImageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'title', 'description', 'file', 'created_at', 'tags']
        read_only_fields = ['id', 'created_at']  # 其他字段可以编辑


class ShareLinkSerializer(serializers.ModelSerializer):
    images = serializers.PrimaryKeyRelatedField(queryset=Image.objects.all(), many=True)  # 支持多个图片选择
    password = serializers.CharField(required=False, allow_blank=True)  # 密码可选

    class Meta:
        model = ShareLink
        fields = ['id', 'images', 'share_code', 'is_protected', 'password', 'expire_time']
        read_only_fields = ['id', 'share_code']

    def create(self, validated_data):
        images = validated_data.pop('images', [])  # 获取上传的图片列表
        share_code = generate_unique_share_code()  # 生成唯一的 share_code

        # 获取密码，决定 is_protected
        password = validated_data.get('password', None)
        is_protected = True if password else False  # 如果有密码，则设置为 True，否则为 False

        # 删除密码字段并只通过 validated_data 中的其他字段创建 ShareLink
        validated_data['is_protected'] = is_protected  # 设置 is_protected
        if password is None:
            validated_data.pop('password', None)  # 如果没有密码，则删除 'password' 字段

        # 创建 ShareLink 实例，确保只传递一次 password 和 is_protected
        share_link = ShareLink.objects.create(
            share_code=share_code,
            **validated_data  # 这里传递其余字段（包括 images, expire_time）
        )

        # 关联图片
        share_link.images.set(images)
        return share_link
