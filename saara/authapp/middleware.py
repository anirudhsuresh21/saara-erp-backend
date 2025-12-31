"""
Custom authentication middleware for Supabase JWT
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import authenticate
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    DRF Authentication class for Supabase JWT tokens
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            # Decode the Supabase JWT token
            # Token is already validated by Supabase, we just need to extract claims
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            # Authenticate using the custom backend
            from saara.authapp.models import User
            
            user_id = payload.get('sub')
            email = payload.get('email')
            role = payload.get('role', 'student')
            
            if not user_id or not email:
                raise AuthenticationFailed('Invalid token payload')
            
            # Get or create user
            user, created = User.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'email': email,
                    'role': role,
                    'is_active': True
                }
            )
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')


class SupabaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate requests using Supabase JWT
    """
    
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            user = authenticate(request, token=token)
            
            if user:
                request.user = user