"""
Authentication views for Supabase integration
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login
from supabase import create_client, Client
from django.conf import settings
import jwt
from datetime import datetime

from saara.authapp.models import User, UserSession, AllowedEmailDomain


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_login(request):
    """
    Login using Supabase credentials - Only allowed domains
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
        # Initialize Supabase client
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        
        # Extract token and user info
        access_token = auth_response.session.access_token
        user_data = auth_response.user
        
        # Decode token to get user details (without verification to get payload)
        # The token is already validated by Supabase
        payload = jwt.decode(
            access_token,
            options={"verify_signature": False}
        )
        
        # Get or create Django user
        user, created = User.objects.get_or_create(
            user_id=user_data.id,
            defaults={
                'email': user_data.email,
                'role': payload.get('role', 'student'),
                'is_active': True,
                'last_login': datetime.now()
            }
        )
        
        if not created:
            user.last_login = datetime.now()
            user.save()
        
        return Response({
            'access_token': access_token,
            'refresh_token': auth_response.session.refresh_token,
            'user': {
                'id': str(user.user_id),
                'email': user.email,
                'role': user.role
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_register(request):
    """
    Register a new user with Supabase - Only allowed domains
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
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Register with Supabase
        auth_response = supabase.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {
                    'role': role
                }
            }
        })
        
        user_data = auth_response.user
        
        # Create Django user
        user = User.objects.create(
            user_id=user_data.id,
            email=user_data.email,
            role=role,
            is_active=True
        )
        
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
    Logout user from Supabase
    """
    try:
        # Initialize Supabase client
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Sign out from Supabase
        supabase.auth.sign_out()
        
        return Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


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
    """
    refresh_token = request.data.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        
        # Refresh the session
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        return Response({
            'access_token': auth_response.session.access_token,
            'refresh_token': auth_response.session.refresh_token
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
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
