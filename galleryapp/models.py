from django.db import models

# Create your models here.
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid


# 定义默认过期时间的函数
def default_expire_time():
    return timezone.now() + timedelta(days=1)


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # 关联用户，确保标签是用户独立的

    def __str__(self):
        return self.name


class Image(models.Model):
    title = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, null=True)  # 留空，可以后续编辑
    file = models.ImageField(upload_to='images/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.title


class ShareLink(models.Model):
    images = models.ManyToManyField('Image', related_name="share_links")
    share_code = models.CharField(max_length=64, unique=True, default=uuid.uuid4().hex)
    is_protected = models.BooleanField(default=False)
    password = models.CharField(max_length=128, blank=True, null=True)  # 可选的保护密码
    expire_time = models.DateTimeField()  # 默认1天有效
    created_time = models.DateTimeField(auto_now_add=True)  # 创建时间

    class Meta:
        ordering = ['-expire_time', 'created_time']

    def is_expired(self):
        return timezone.now() > self.expire_time
