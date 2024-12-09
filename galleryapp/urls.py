from django.urls import path
from .views import UserTagListView, BulkDeleteImagesView, ImageUploadView, UserImageListView, ImageDetailView, \
    ImageEditView, CreateShareLinkView, AccessShareLinkView, ManageShareLinksView

urlpatterns = [
    path('images/', UserImageListView.as_view(), name='user-images'),
    path('images/upload/', ImageUploadView.as_view(), name='image-upload'),
    path('images/bulk_delete/', BulkDeleteImagesView.as_view(), name='bulk_delete_images'),
    path('images/<int:image_id>/', ImageDetailView.as_view(), name='image-detail'),
    path('images/<int:image_id>/edit/', ImageEditView.as_view(), name='image-edit'),
    path('images/share/', CreateShareLinkView.as_view(), name='create-share-link'),
    path('share/<str:share_code>/', AccessShareLinkView.as_view(), name='access-share-link'),
    path('images/share/manage/', ManageShareLinksView.as_view(), name='manage-share-links'),
    path('images/share/manage/delete/', ManageShareLinksView.as_view(), name='delete-multiple-share-links'),  # 批量删除分享链接
    # 标签管理
    path('tags/', UserTagListView.as_view(), name='user-tag-list'),
]
