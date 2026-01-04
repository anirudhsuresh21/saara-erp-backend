from django.urls import path
from django.views.generic import TemplateView
from .views import (
    ChatView,
    ChatSessionListView,
    ChatSessionDetailView,
    ClearChatHistoryView
)

urlpatterns = [
    # Main chat endpoint
    path('chat/', ChatView.as_view(), name='chat'),
    
    # Session management
    path('sessions/', ChatSessionListView.as_view(), name='chat-sessions'),
    path('sessions/<uuid:session_id>/', ChatSessionDetailView.as_view(), name='chat-session-detail'),
    path('sessions/clear/', ClearChatHistoryView.as_view(), name='clear-chat-history'),
]
