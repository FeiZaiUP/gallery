from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    store_name = models.CharField(max_length=255, blank=True, null=True)  # 商铺名称
    user_type = models.CharField(max_length=50, choices=[('business', 'Business'), ('admin', 'Admin')],
                                 default='business')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # 其他扩展字段可以根据需求添加

    def __str__(self):
        return self.username
