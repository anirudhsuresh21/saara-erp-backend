from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages"""
    
    class Meta:
        model = ChatMessage
        fields = ['message_id', 'role', 'content', 'timestamp', 'tokens_used']
        read_only_fields = ['message_id', 'timestamp']


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['session_id', 'title', 'created_at', 'updated_at', 'is_active', 'messages', 'message_count']
        read_only_fields = ['session_id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class ChatSessionListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing sessions without messages"""
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['session_id', 'title', 'created_at', 'updated_at', 'is_active', 'message_count', 'last_message']
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return {
                'content': last_msg.content[:100] + '...' if len(last_msg.content) > 100 else last_msg.content,
                'role': last_msg.role,
                'timestamp': last_msg.timestamp
            }
        return None


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for chat request"""
    query = serializers.CharField(max_length=2000, help_text="User's question or message")
    session_id = serializers.UUIDField(required=False, allow_null=True, help_text="Optional session ID to continue conversation")


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for chat response"""
    response = serializers.CharField()
    intent = serializers.CharField()
    parsed = serializers.DictField()
    session_id = serializers.UUIDField()
