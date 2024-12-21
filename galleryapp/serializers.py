from .models import Image, ShareLink, Tag
from rest_framework import serializers
from django.db import IntegrityError
from django.utils.timezone import now, localtime
from datetime import timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


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
        read_only_fields = ['id', 'uploaded_by', 'created_at']  # id 和 created_at 不允许修改

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

    expire_duration = serializers.IntegerField(write_only=True, required=False)  # 以分钟为单位

    class Meta:
        model = ShareLink
        fields = ['id', 'images', 'share_code', 'is_protected', 'password', 'expire_time', 'expire_duration']
        read_only_fields = ['id', 'share_code']

        def validate_expire_duration(self, value):
            if value is not None and value <= 0:
                raise serializers.ValidationError("过期时长必须为正整数分钟。")
            return value

        def get_expire_time(self, obj):
            # 将 expire_time 转换为本地时间 (北京时间)
            expire_time = timezone.localtime(obj.expire_time, timezone.get_current_timezone())
            return expire_time.isoformat()  # 返回 ISO 格式

    def create(self, validated_data):
        # 提取并移除 `expire_duration`, 如果没填则默认为24小时
        expire_duration = validated_data.pop('expire_duration', 1440)

        # 获取当前时间，并转换为本地时区（确保时区正确）
        current_time = localtime(now())
        # 动态计算过期时间，确保计算时间准确
        expire_time = current_time + timedelta(minutes=expire_duration)

        # 调试输出
        print(f"Current time: {current_time}")
        print(f"Expire time: {expire_time}")

        # 将过期时间添加到 validated_data 中
        validated_data['expire_time'] = expire_time

        # 继续正常创建逻辑
        images = validated_data.pop('images', [])
        share_code = generate_unique_share_code()
        validated_data['share_code'] = share_code
        is_protected = bool(validated_data.get('password'))
        validated_data['is_protected'] = is_protected

        share_link = ShareLink.objects.create(**validated_data)
        share_link.images.set(images)
        return share_link
