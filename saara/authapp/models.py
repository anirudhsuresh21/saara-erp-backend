from django.db import models
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
import uuid
# Create your models here.


class AllowedEmailDomain(models.Model):
    """"Allowed email domains for registration and login"""
    domain = models.CharField(max_length=255, unique=True, help_text="Email domain (e.g., sies.edu.in)")
    institution_name = models.CharField(max_length=255, help_text="Institution Name")
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this domain is currently allowed'
    )
    allow_subdomains = models.BooleanField(
        default=True,
        help_text="Allow subdomains (e.g., siescoms.sies.edu.in"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'allowed_email_domains'
        verbose_name = 'Allowed Email Domain'
        verbose_name_plural = 'Allowed Email Domains'
        ordering = ['domain']

    def clean(self):
        if self.domain:
            self.domain = self.domain.strip().lower()
            if self.domain.startswith("@"):
                self.domain = self.domain[1:]

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, *kwargs)
        
    def __str__(self):
        subdomain_info = " (+ subdomains)" if self.allow_subdomains else ""
        return f"{self.domain}{subdomain_info} ({self.institution_name})"
        # return super().__str__()
        
    @classmethod
    def is_domain_allowed(cls, email):
        """
        Check if the email domain is allowed (supports subdomains)
        Examples:
        - student@sies.edu.in ✓
        - student@siescoms.sies.edu.in ✓ (if allow_subdomains=True)
        """
        if not email or '@' not in email:
            return False
        
        email_domain = email.split('@')[1].lower()
        
        # check all active domains
        active_domains = cls.objects.filter(is_active=True)
        
        for allowed_domains in active_domains:
            domain_lower = allowed_domains.lower()
            
            #exact match
            if email_domain == domain_lower:
                return True
            
            # subdomain match
            if allowed_domains.allow_subdomains:
                if email_domain.endswith(f'.{domain_lower}'):
                    return True
        return False
    
    
    @classmethod
    def get_domain_from_email(cls, email):
        if not email or '@' not in email:
            return None
        return email.split('@')[1].lower()
    
class User(models.Model):
    """Base user model for Uthentication"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin')
    ]
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
    
    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)
        
    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)
    
    def clean(self):
        #validate email domain
        if self.email and not AllowedEmailDomain.is_domain_allowed(self.email):
            domain = AllowedEmailDomain.get_domain_from_email(self.email)
            raise ValidationError(
                f'Email Domain "{domain}" is not allowed. Please use an authorized institutional email' 
            )
    def __str__(self):
        return self.email
    
class UserSession(models.Model):
    """User Session Tracking"""
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    
class AuditLog(models.Model):
    """Audit log for tracking user actions"""
    log_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f'{self.user} - {self.action} - {self.timestamp}'