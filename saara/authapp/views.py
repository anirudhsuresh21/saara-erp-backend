"""
Authentication views using Django's default authentication
Replaces Supabase integration with local Django authentication
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import jwt
from datetime import datetime, timedelta
import uuid

from saara.authapp.models import User, UserSession, AllowedEmailDomain


def generate_jwt_token(user):
    """Generate a JWT token for the user"""
    payload = {
        'sub': str(user.user_id),
        'email': user.email,
        'role': user.role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token


def generate_refresh_token():
    """Generate a simple refresh token"""
    return f'refresh_{uuid.uuid4()}'


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_login(request):
    """
    Login using Django's local database authentication - Only allowed domains
    (Named supabase_login for backwards compatibility)
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if email domain is allowed
    if not AllowedEmailDomain.is_domain_allowed(email):
        domain = AllowedEmailDomain.get_domain_from_email(email)
        return Response(
            {
                'error': f'Email domain "{domain}" is not authorized. Please use an institutional email from an approved domain.',
                'allowed_domains_hint': 'Contact your administrator to add your institution domain.'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        # Find user by email
        user = User.objects.get(email=email)
        
        # Check password using Django's password hasher
        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update last login
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save()
        
        # Generate JWT token
        access_token = generate_jwt_token(user)
        refresh_token = generate_refresh_token()
        
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': str(user.user_id),
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_register(request):
    """
    Register a new user with Django's local database - Only allowed domains
    (Named supabase_register for backwards compatibility)
    """
    email = request.data.get('email')
    password = request.data.get('password')
    role = request.data.get('role', 'student')
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if email domain is allowed
    if not AllowedEmailDomain.is_domain_allowed(email):
        domain = AllowedEmailDomain.get_domain_from_email(email)
        return Response(
            {
                'error': f'Registration with email domain "{domain}" is not allowed.',
                'message': 'Only institutional emails from approved domains can register.',
                'allowed_domains_hint': 'Contact your administrator to add your institution domain.'
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user already exists
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'A user with this email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create Django user
        user = User.objects.create(
            email=email,
            role=role,
            is_active=True
        )
        user.set_password(password)
        user.save()
        
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': str(user.user_id),
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def supabase_logout(request):
    """
    Logout user (invalidate session on client side)
    (Named supabase_logout for backwards compatibility)
    """
    return Response({
        'message': 'Logged out successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    """
    Get current authenticated user details
    """
    user = request.user
    
    return Response({
        'id': str(user.user_id),
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'last_login': user.last_login
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token
    For local Django auth, we just generate a new token if the user is valid
    """
    refresh_token_value = request.data.get('refresh_token')
    
    if not refresh_token_value:
        return Response(
            {'error': 'Refresh token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Try to get user from the Authorization header if present
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.replace('Bearer ', '')
        try:
            # Decode without verification to get user info (token might be expired)
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256'],
                options={"verify_exp": False}
            )
            
            user_id = payload.get('sub')
            if user_id:
                user = User.objects.get(user_id=user_id)
                if user.is_active:
                    new_access_token = generate_jwt_token(user)
                    new_refresh_token = generate_refresh_token()
                    
                    return Response({
                        'access_token': new_access_token,
                        'refresh_token': new_refresh_token
                    }, status=status.HTTP_200_OK)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            pass
    
    return Response(
        {'error': 'Invalid refresh token. Please login again.'},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_allowed_domains(request):
    """
    Get list of allowed email domains (public endpoint)
    """
    domains = AllowedEmailDomain.objects.filter(is_active=True).values('domain', 'institution_name')
    return Response({
        'allowed_domains': list(domains),
        'count': len(domains)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def dev_login(request):
    """
    Development login endpoint - same as supabase_login (Django auth)
    Kept for backwards compatibility
    """
    return supabase_login(request)
