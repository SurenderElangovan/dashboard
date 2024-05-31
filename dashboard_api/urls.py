from django.urls import path
from .views import ProjectCreateOrUploadView, ProjectGetListView, ProjectGetView, ProjectDeleteView

urlpatterns = [
    path('projects/create-or-upload/', ProjectCreateOrUploadView.as_view(), name='project-create-or-upload'),
    path('projects/list/', ProjectGetListView.as_view(), name='project-list'),
    path('projects/detail/', ProjectGetView.as_view(), name='project-detail'),
    path('projects/delete/', ProjectDeleteView.as_view(), name='project-delete'),
]
