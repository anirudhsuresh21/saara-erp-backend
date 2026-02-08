import jwt 
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from saara.authapp.models import User


class DjangoJWTAuthBackend(BaseBackend):
    """
    Authenticate against Django JWT tokens signed with SECRET_KEY
    """
    def authenticate(self, request, token=None):
        if token is None:
            return None
        
        try:
            # Decode the JWT token using Django's SECRET_KEY
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Extract user info from Token
            user_id = payload.get('sub')
            email = payload.get('email')
            
            if not user_id and not email:
                return None
            
            # Get user by ID or email
            try:
                if user_id:
                    user = User.objects.get(user_id=user_id)
                else:
                    user = User.objects.get(email=email)
                
                if not user.is_active:
                    return None
                    
                return user
            except User.DoesNotExist:
                return None
        
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