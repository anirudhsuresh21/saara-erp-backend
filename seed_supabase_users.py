"""
Script to register seeded users in Supabase Auth.
This uses the Supabase Admin API with the service role key.

Prerequisites:
1. Set SUPABASE_SERVICE_KEY in your .env file
2. Run seed_data.py first to create Django users

Run with: python seed_supabase_users.py
"""

import os
import sys
import django
import time
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'saara.settings')
django.setup()

from django.conf import settings
from saara.authapp.models import User


# Supabase Admin API configuration
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_SERVICE_KEY = settings.SUPABASE_SERVICE_KEY

# Password mapping for seeded users
PASSWORD_MAP = {
    'admin': 'admin123',
    'faculty': 'faculty123',
    'student': 'student123',
}


def get_admin_headers():
    """Get headers for Supabase Admin API"""
    return {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json',
    }


def check_user_exists(email):
    """Check if user already exists in Supabase"""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = get_admin_headers()
    
    try:
        response = requests.get(url, headers=headers, params={'page': 1, 'per_page': 1000})
        if response.status_code == 200:
            users = response.json().get('users', [])
            for user in users:
                if user.get('email', '').lower() == email.lower():
                    return user.get('id')
        return None
    except Exception as e:
        print(f"   ⚠️ Error checking user: {e}")
        return None


def create_supabase_user(email, password, role, django_user_id):
    """Create a user in Supabase Auth using Admin API"""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = get_admin_headers()
    
    payload = {
        'email': email,
        'password': password,
        'email_confirm': True,  # Auto-confirm email
        'user_metadata': {
            'role': role,
            'django_user_id': str(django_user_id)
        },
        'app_metadata': {
            'role': role
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200 or response.status_code == 201:
            user_data = response.json()
            return True, user_data.get('id')
        elif response.status_code == 422:
            # User might already exist
            error_msg = response.json().get('message', response.json().get('msg', 'Unknown error'))
            if 'already been registered' in str(error_msg).lower() or 'duplicate' in str(error_msg).lower():
                existing_id = check_user_exists(email)
                return True, existing_id  # Already exists
            return False, error_msg
        else:
            error_msg = response.json().get('message', response.json().get('msg', response.text))
            return False, error_msg
            
    except Exception as e:
        return False, str(e)


def update_django_user_id(django_user, supabase_user_id):
    """Update Django user with Supabase user ID"""
    if supabase_user_id and str(django_user.user_id) != supabase_user_id:
        # Update the Django user's ID to match Supabase
        # This is tricky because user_id is the primary key
        # We'll create a new user with the correct ID and delete the old one
        try:
            from saara.erp.models import Student, Teacher, Admin as AdminProfile
            from saara.chatbot.models import ChatSession
            from saara.authapp.models import UserSession, AuditLog
            
            old_id = django_user.user_id
            
            # Check if we need to update (only if IDs don't match)
            # For now, we'll just note the mismatch
            print(f"      Note: Django ID {old_id} != Supabase ID {supabase_user_id}")
            
        except Exception as e:
            print(f"      Warning: Could not sync IDs: {e}")


def sync_users_to_supabase():
    """Main function to sync all Django users to Supabase"""
    print("\n" + "="*60)
    print("🔄 SYNCING USERS TO SUPABASE AUTH")
    print("="*60)
    
    # Validate configuration
    if not SUPABASE_URL or SUPABASE_URL == 'https://your-project.supabase.co':
        print("❌ Error: SUPABASE_URL not configured in .env")
        return
    
    if not SUPABASE_SERVICE_KEY:
        print("❌ Error: SUPABASE_SERVICE_KEY not configured in .env")
        print("   Get it from: Supabase Dashboard > Settings > API > service_role key")
        return
    
    print(f"\n📡 Supabase URL: {SUPABASE_URL}")
    print(f"🔑 Service Key: {SUPABASE_SERVICE_KEY[:20]}...")
    
    # Get all Django users
    users = User.objects.all()
    total = users.count()
    
    print(f"\n📊 Found {total} users in Django database")
    
    created = 0
    existed = 0
    failed = 0
    
    # Process users by role
    for role in ['admin', 'faculty', 'student']:
        role_users = users.filter(role=role)
        password = PASSWORD_MAP.get(role, 'password123')
        
        print(f"\n{'👔' if role == 'admin' else '👨‍🏫' if role == 'faculty' else '👨‍🎓'} Processing {role_users.count()} {role}s...")
        
        for i, user in enumerate(role_users):
            # Rate limiting - Supabase has rate limits
            if i > 0 and i % 10 == 0:
                print(f"   ... processed {i}/{role_users.count()}")
                time.sleep(0.5)  # Small delay to avoid rate limits
            
            success, result = create_supabase_user(
                email=user.email,
                password=password,
                role=role,
                django_user_id=user.user_id
            )
            
            if success:
                if result and 'already' not in str(result).lower():
                    created += 1
                else:
                    existed += 1
            else:
                failed += 1
                print(f"   ❌ Failed to create {user.email}: {result}")
    
    print("\n" + "="*60)
    print("✅ SUPABASE USER SYNC COMPLETED")
    print("="*60)
    print(f"\n📊 SUMMARY:")
    print(f"   • Created: {created}")
    print(f"   • Already existed: {existed}")
    print(f"   • Failed: {failed}")
    print(f"   • Total processed: {total}")
    
    print("\n🔐 LOGIN CREDENTIALS:")
    print("   • Admin: admin@sies.edu.in / admin123")
    print("   • Faculty: dr.sharma@sies.edu.in / faculty123")
    print("   • Student: <any student email> / student123")
    print("")


def delete_all_supabase_users():
    """Delete all users from Supabase (use with caution!)"""
    print("\n⚠️  WARNING: This will delete ALL users from Supabase Auth!")
    confirm = input("Type 'DELETE ALL' to confirm: ")
    
    if confirm != 'DELETE ALL':
        print("Aborted.")
        return
    
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = get_admin_headers()
    
    try:
        # Get all users
        response = requests.get(url, headers=headers, params={'page': 1, 'per_page': 1000})
        if response.status_code != 200:
            print(f"Failed to get users: {response.text}")
            return
        
        users = response.json().get('users', [])
        print(f"Found {len(users)} users to delete...")
        
        for user in users:
            user_id = user.get('id')
            delete_url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
            del_response = requests.delete(delete_url, headers=headers)
            
            if del_response.status_code == 200:
                print(f"   ✓ Deleted {user.get('email')}")
            else:
                print(f"   ✗ Failed to delete {user.get('email')}: {del_response.text}")
            
            time.sleep(0.1)
        
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")


def list_supabase_users():
    """List all users in Supabase"""
    url = f"{SUPABASE_URL}/auth/v1/admin/users"
    headers = get_admin_headers()
    
    try:
        response = requests.get(url, headers=headers, params={'page': 1, 'per_page': 100})
        if response.status_code == 200:
            users = response.json().get('users', [])
            print(f"\n📋 Supabase Users ({len(users)} total):")
            for user in users[:20]:  # Show first 20
                print(f"   • {user.get('email')} (ID: {user.get('id')[:8]}...)")
            if len(users) > 20:
                print(f"   ... and {len(users) - 20} more")
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync Django users to Supabase Auth')
    parser.add_argument('--delete-all', action='store_true', help='Delete all Supabase users (dangerous!)')
    parser.add_argument('--list', action='store_true', help='List all Supabase users')
    
    args = parser.parse_args()
    
    if args.delete_all:
        delete_all_supabase_users()
    elif args.list:
        list_supabase_users()
    else:
        sync_users_to_supabase()
