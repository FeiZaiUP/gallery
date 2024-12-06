from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response


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

    def get(self, request):
        user = request.user
        print(f"Authenticated User: {user}")  # 添加日志查看 user 对象
        return Response({
            'username': user.username,
            'email': user.email,
            'store_name': user.store_name,
            'user_type': user.user_type,
        })
