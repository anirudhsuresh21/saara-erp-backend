import jwt 
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from saara.authapp.models import User


class SupabaseAuthBackend(BaseBackend):
    """
    Authenticate against Supabase JWT tokens
    """
    def authenticate(self, request, token=None):
        if token is None:
            return None
        
        try:
            # Decode the Supabase JWT token
            # Token is already validated by Supabase, we just need to extract claims
            payload = jwt.decode(
                token,
                options={"verify_signature": False}
            )
            
            # Extract user info from Token
            user_id = payload.get('sub')
            email = payload.get('email')
            role = payload.get('role','student')
            
            if not user_id or not email:
                return None
            
            # Get or create user
            user, created = User.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'email':email,
                    'role':role,
                    'is_active': True
                }
            )
            return user
        
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception:
            return None
        
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None