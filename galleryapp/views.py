from django.shortcuts import render

# Create your views here.
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from django.utils.timezone import now
from django.utils.timezone import make_aware
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Image, ShareLink, Tag
from .serializers import ImageSerializer, ImageDetailSerializer, ShareLinkSerializer, TagSerializer

import uuid
import logging
import json
import logging

logger = logging.getLogger(__name__)


class CustomPagination(PageNumberPagination):
    page_size = 16  # 每页显示12张图片
    page_size_query_param = 'page_size'  # 可通过查询参数控制每页大小
    max_page_size = 100  # 最大支持100条数据


# 图片标签
class UserTagListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 只返回当前用户创建的标签
        tags = Tag.objects.filter(uploaded_by=request.user)
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    def post(self, request):
        # 创建标签
        serializer = TagSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()  # 保存并创建标签
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 图片上传
class ImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 仅接受 title 和 file、tags 字段上传

        # 获取标签ID列表，如果未提供则默认为空
        tags = request.data.get('tags', [])
        # 确保 tags 是一个列表，即使前端传递多个值
        if isinstance(tags, str):  # 如果是字符串（JSON字符串）
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                return Response({'detail': '标签格式无效。'}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(tags, list):  # 如果是列表
            try:
                tags = [int(tag) for tag in tags]  # 确保列表里的标签是整数类型
            except ValueError:
                return Response({'detail': '标签列表中的值必须为整数。'}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(tags, int):  # 如果是单个整数
            tags = [tags]  # 转换为列表
        else:
            return Response({'detail': '标签格式无效，应为整数或整数列表。'}, status=status.HTTP_400_BAD_REQUEST)

        # 如果提供了 tags，验证是否是有效的标签ID
        if tags:
            user_tags = Tag.objects.filter(uploaded_by=request.user)  # 获取当前用户的标签
            valid_tags = user_tags.filter(id__in=tags)  # 确保标签是用户创建的
        else:
            valid_tags = []  # 如果未提供 tags，则设置为空列表

        serializer = ImageSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.save(uploaded_by=request.user)  # 关联当前用户

            # 获取用户的标签列表，确保只能为当前用户创建的标签关联
            user_tags = Tag.objects.filter(uploaded_by=request.user)
            valid_tags = user_tags.filter(id__in=tags)  # 确保标签是当前用户创建的
            image.tags.set(valid_tags)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BulkDeleteImagesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 获取图片ID列表
        image_ids = request.data.get('image_ids', [])
        print(request.data)
        if not image_ids:
            return Response({"detail": "未找到图片。"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取当前用户的图片，确保这些图片是当前用户上传的
        images = Image.objects.filter(id__in=image_ids, uploaded_by=request.user)

        if images.count() != len(image_ids):
            return Response({"detail": "这些图像不属于您或无效。"},
                            status=status.HTTP_400_BAD_REQUEST)

        # 批量删除图片
        images.delete()

        return Response({"detail": "选定的图像已成功删除。"},
                        status=status.HTTP_204_NO_CONTENT)


# 获取图片列表、支持标签过滤
class UserImageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取标签过滤参数
        tag_ids = request.query_params.getlist('tags', [])

        # 获取当前用户的图片
        images = Image.objects.filter(uploaded_by=request.user)  # 只返回当前用户的图片
        # 如果用户选择了标签，进行过滤，确保只查看当前用户的标签
        if tag_ids:
            images = images.filter(tags__id__in=tag_ids).distinct()

        serializer = ImageSerializer(images, many=True)
        return Response(serializer.data)


# 获取图片详情

class ImageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, image_id):
        image = Image.objects.filter(id=image_id, uploaded_by=request.user).first()  # 确保图片属于当前用户
        if image:
            serializer = ImageDetailSerializer(image)
            return Response(serializer.data)
        return Response({"detail": "图片未找到或者您没有权限。"}, status=status.HTTP_404_NOT_FOUND)


# 图片信息编辑

class ImageEditView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, image_id):
        try:
            # 获取当前用户的图片
            return Image.objects.get(pk=image_id, uploaded_by=self.request.user)
        except Image.DoesNotExist:
            return None

    def put(self, request, image_id):
        # 用 PUT 方法更新图片信息
        image = self.get_object(image_id)
        if image is None:
            return Response({"detail": "未找到图像或访问被拒绝"}, status=status.HTTP_404_NOT_FOUND)

        # 序列化并更新数据
        serializer = ImageSerializer(image, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            # 更新标签
            tags = request.data.get('tags', [])
            if tags:
                user_tags = Tag.objects.filter(uploaded_by=request.user)
                valid_tags = user_tags.filter(id__in=tags)
                image.tags.set(valid_tags)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, image_id):
        # 用 PATCH 方法部分更新图片信息
        image = self.get_object(image_id)
        if image is None:
            return Response({"detail": "未找到图像或访问被拒绝"}, status=status.HTTP_404_NOT_FOUND)

            # 序列化并更新数据
        serializer = ImageSerializer(image, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # 更新标签
            tags = request.data.get('tags', [])
            if tags:
                user_tags = Tag.objects.filter(uploaded_by=request.user)
                valid_tags = user_tags.filter(id__in=tags)
                image.tags.set(valid_tags)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 分享链接生成

class CreateShareLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("Received data:", request.data)  # 打印前端发送的数据

        # 确保请求中有图片ID列表
        image_ids = request.data.get('images', [])
        if not image_ids:
            return Response({"detail": "必须至少选择一张图片。"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查所有图片ID是否有效
        images = Image.objects.filter(id__in=image_ids)
        if images.count() != len(image_ids):
            return Response({"detail": "未找到一张或多张图像。"}, status=status.HTTP_404_NOT_FOUND)

        # 处理过期时间
        expire_time = None
        expire_duration = request.data.get('expire_duration', None)  # 获取过期时长（分钟）
        if expire_duration:
            try:
                expire_duration = int(expire_duration)
                if expire_duration <= 0:
                    return Response({"detail": "过期时长必须为正整数。"}, status=status.HTTP_400_BAD_REQUEST)
                expire_time = now() + timedelta(minutes=expire_duration)
            except (ValueError, TypeError):
                return Response({"detail": "无效的过期时长。"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # 如果未指定时长，检查是否传递具体时间
            expire_time_input = request.data.get('expire_time', None)
            if expire_time_input:
                try:
                    expire_time = make_aware(datetime.fromisoformat(expire_time_input))
                    if expire_time <= now():
                        return Response({"detail": "过期时间必须大于当前时间。"}, status=status.HTTP_400_BAD_REQUEST)
                except ValueError:
                    return Response({"detail": "无效的时间格式，应为 ISO 格式。"}, status=status.HTTP_400_BAD_REQUEST)

        # 如果未提供时长和时间，使用默认值（例如 24 小时）
        if not expire_time:
            expire_time = now() + timedelta(hours=24)

        # 准备序列化数据
        data = request.data.copy()
        data['expire_time'] = expire_time  # 设置计算后的过期时间

        # 序列化并保存
        serializer = ShareLinkSerializer(data=data)
        if not serializer.is_valid():
            print("Serializer Errors:", serializer.errors)  # 打印序列化错误
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()  # 保存并创建 ShareLink
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# 通过分享链接访问图片
class AccessShareLinkView(APIView):
    permission_classes = []

    def get(self, request, share_code):
        # 查找分享链接
        try:
            share_link = ShareLink.objects.prefetch_related('images').get(share_code=share_code)
        except ShareLink.DoesNotExist:
            raise NotFound("Invalid share code.")

        # 检查是否过期
        if share_link.is_expired():
            raise PermissionDenied("This share link has expired.")

            # 打印请求中的密码
        print("Received password:", request.query_params.get('password'))

        # 如果分享链接有密码保护
        if share_link.is_protected:
            # 获取请求中的密码参数
            password = request.query_params.get('password', '')
            # 校验密码
            if share_link.password != password:
                print(f"Password mismatch: expected {share_link.password}, got {password}")
                raise PermissionDenied("Incorrect password.")

        # 获取关联图片并序列化返回
        images = share_link.images.all()
        serializer = ImageSerializer(images, many=True)

        # 添加密码保护字段
        return Response({
            "share_code": share_code,
            "images": serializer.data,
            "expire_time": share_link.expire_time,
            "is_protected": share_link.is_protected,  # 返回是否受保护字段

        })


# 管理分享链接
# 分页类
class ShareLinkPagination(PageNumberPagination):
    page_size = 5  # 默认每页5条数据
    page_size_query_param = 'page_size'  # 可通过 query 参数指定每页条数
    max_page_size = 100  # 最大每页条数


class ManageShareLinksView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 获取当前用户的所有分享链接，确保分享链接不重复
        share_links = ShareLink.objects.filter(images__uploaded_by=request.user).distinct()

        # 过滤掉已过期的分享链接
        share_links = share_links.filter(expire_time__gte=timezone.now())

        # 分页处理
        paginator = ShareLinkPagination()
        paginated_share_links = paginator.paginate_queryset(share_links, request)

        # 序列化分页后的分享链接数据
        serializer = ShareLinkSerializer(paginated_share_links, many=True)

        return paginator.get_paginated_response(serializer.data)

    def delete(self, request):
        """
        批量删除分享链接
        """
        # 从请求体中获取 share_codes
        share_codes = request.data.get('share_codes', [])
        if not share_codes:
            return Response({"detail": "No share codes provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 获取所有要删除的分享链接
        share_links = ShareLink.objects.filter(share_code__in=share_codes, images__uploaded_by=request.user)

        if not share_links:
            return Response({"detail": "No valid share links found or permission denied."},
                            status=status.HTTP_404_NOT_FOUND)

        # 批量删除
        share_links.delete()

        return Response({"detail": "Share links deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
