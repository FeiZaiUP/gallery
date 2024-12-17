from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10  # 默认每页显示 10 条
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_size(self, request):
        """
        可根据不同的请求上下文动态设置分页大小。
        """
        if request.user.is_staff:  # 比如管理员可以看到更多数据
            return 50
        return super().get_page_size(request)

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
