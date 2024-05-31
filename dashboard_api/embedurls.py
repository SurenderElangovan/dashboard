from django.urls import path
from .views import EmbedCodeView

urlpatterns = [
    path('view/embed', EmbedCodeView.as_view(), name='embed-template')
]