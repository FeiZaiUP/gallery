from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


# login
class CustomTokenObtainPairView(TokenObtainPairView):
    # 可以重写 `TokenObtainPairView` 来自定义返回内容
    pass


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # 只允许认证用户访问
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        avatar_url = user.avatar.url if user.avatar else getattr(settings, 'DEFAULT_AVATAR_URL',
                                                                 '/media/default/avatar.png')
        return Response({
            'username': user.username,
            'email': user.email,
            'store_name': user.store_name,
            'user_type': user.user_type,
            'avatar': request.build_absolute_uri(avatar_url),
        })

    def put(self, request):
        user = request.user
        avatar = request.FILES.get('avatar')  # 获取上传的头像文件
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            if avatar:
                user.avatar = avatar  # 保存上传的头像到用户实例
                user.save()  # 确保保存头像到数据库
            serializer.save()
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        user = request.user
        avatar = request.FILES.get('avatar')

        if avatar:
            allowed_types = ['image/jpeg', 'image/png']
            if avatar.content_type not in allowed_types:
                return Response({'error': '仅支持 JPG 和 PNG 格式'}, status=status.HTTP_400_BAD_REQUEST)

            user.avatar = avatar
            user.save()
            return Response({'avatar': request.build_absolute_uri(user.avatar.url)})

        return Response({'error': '未上传头像'}, status=status.HTTP_400_BAD_REQUEST)

