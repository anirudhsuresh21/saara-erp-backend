"""
Custom authentication middleware for Django JWT
Replaces Supabase authentication with local Django authentication
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import authenticate
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from django.conf import settings


class DjangoJWTAuthentication(BaseAuthentication):
    """
    DRF Authentication class for Django JWT tokens
    Uses Django's SECRET_KEY to sign and verify tokens
    """
    
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        
        try:
            # Decode the JWT token using Django's SECRET_KEY
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            
            from saara.authapp.models import User
            
            user_id = payload.get('sub')
            email = payload.get('email')
            
            if not user_id and not email:
                raise AuthenticationFailed('Invalid token payload')
            
            # Try to find user by user_id first, then by email
            try:
                if user_id:
                    user = User.objects.get(user_id=user_id)
                else:
                    user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise AuthenticationFailed('User not found')
            
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')


class DjangoAuthMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate requests using Django JWT
    """
    
    def process_request(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.replace('Bearer ', '')
            user = authenticate(request, token=token)
            
            if user:
                request.user = user