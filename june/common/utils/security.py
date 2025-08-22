"""
Security utilities for the AI Career Copilot system.
Implements authentication, authorization, input validation, rate limiting, and security headers.
"""

import hashlib
import hmac
import time
import secrets
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import logging

logger = logging.getLogger(__name__)

# Security configuration
SECURITY_CONFIG = {
    "JWT_SECRET": "your-super-secret-jwt-key-change-in-production",
    "JWT_ALGORITHM": "HS256",
    "JWT_EXPIRY_HOURS": 24,
    "MAX_REQUEST_SIZE": 10 * 1024 * 1024,  # 10MB
    "RATE_LIMIT_WINDOW": 60,  # seconds
    "RATE_LIMIT_MAX_REQUESTS": 100,
    "PASSWORD_MIN_LENGTH": 12,
    "SESSION_TIMEOUT": 3600,  # seconds
}

@dataclass
class User:
    """User entity with security attributes"""
    id: str
    email: str
    role: str
    permissions: List[str]
    created_at: datetime
    last_login: datetime
    is_active: bool
    failed_login_attempts: int
    locked_until: Optional[datetime] = None

class SecurityValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', value)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """Validate password strength"""
        if len(password) < SECURITY_CONFIG["PASSWORD_MIN_LENGTH"]:
            return False
        
        # Must contain at least one uppercase, lowercase, digit, and special character
        has_upper = re.search(r'[A-Z]', password)
        has_lower = re.search(r'[a-z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        
        return all([has_upper, has_lower, has_digit, has_special])
    
    @staticmethod
    def sanitize_mongo_query(query: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize MongoDB query to prevent injection attacks"""
        sanitized = {}
        for key, value in query.items():
            # Only allow safe keys
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                if isinstance(value, str):
                    sanitized[key] = SecurityValidator.sanitize_string(value)
                elif isinstance(value, dict):
                    sanitized[key] = SecurityValidator.sanitize_mongo_query(value)
                elif isinstance(value, list):
                    sanitized[key] = [
                        SecurityValidator.sanitize_string(str(item)) if isinstance(item, str) else item
                        for item in value
                    ]
                else:
                    sanitized[key] = value
        
        return sanitized

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.requests = {}
        self.window = SECURITY_CONFIG["RATE_LIMIT_WINDOW"]
        self.max_requests = SECURITY_CONFIG["RATE_LIMIT_MAX_REQUESTS"]
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed based on rate limiting"""
        now = time.time()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window
        ]
        
        # Check if under limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for a client"""
        now = time.time()
        if client_id not in self.requests:
            return self.max_requests
        
        valid_requests = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window
        ]
        
        return max(0, self.max_requests - len(valid_requests))

class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def create_token(user_id: str, email: str, role: str) -> str:
        """Create JWT token for user"""
        payload = {
            "user_id": user_id,
            "email": email,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=SECURITY_CONFIG["JWT_EXPIRY_HOURS"]),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(32)
        }
        
        return jwt.encode(payload, SECURITY_CONFIG["JWT_SECRET"], algorithm=SECURITY_CONFIG["JWT_ALGORITHM"])
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECURITY_CONFIG["JWT_SECRET"], algorithms=[SECURITY_CONFIG["JWT_ALGORITHM"]])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

class AuthenticationMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self):
        self.security = HTTPBearer()
    
    async def authenticate(self, request: Request) -> Optional[User]:
        """Authenticate user from request"""
        try:
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            token = credentials.credentials
            
            payload = JWTManager.verify_token(token)
            
            # Here you would typically fetch user from database
            # For now, return a mock user
            return User(
                id=payload["user_id"],
                email=payload["email"],
                role=payload["role"],
                permissions=["read", "write"],  # Mock permissions
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                is_active=True,
                failed_login_attempts=0
            )
            
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            return None

class AuthorizationManager:
    """Authorization and permission management"""
    
    @staticmethod
    def check_permission(user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user.permissions
    
    @staticmethod
    def require_permission(permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # This would be implemented in the actual middleware
                # For now, just pass through
                return await func(*args, **kwargs)
            return wrapper
        return decorator

class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

class AuditLogger:
    """Security audit logging"""
    
    @staticmethod
    def log_security_event(event_type: str, user_id: str, details: Dict[str, Any], severity: str = "INFO"):
        """Log security-related events"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "severity": severity,
            "ip_address": "unknown",  # Would be extracted from request
            "user_agent": "unknown"   # Would be extracted from request
        }
        
        logger.info(f"SECURITY_EVENT: {log_entry}")
        
        # In production, this would be sent to a security monitoring system
        if severity in ["WARNING", "ERROR", "CRITICAL"]:
            logger.error(f"SECURITY_ALERT: {log_entry}")

# Global instances
rate_limiter = RateLimiter()
auth_middleware = AuthenticationMiddleware()
auth_manager = AuthorizationManager()
security_validator = SecurityValidator()
audit_logger = AuditLogger()

def get_client_id(request: Request) -> str:
    """Extract client identifier from request"""
    # Use IP address as client identifier
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{request.headers.get('user-agent', 'unknown')}"

def validate_request_size(request: Request) -> bool:
    """Validate request size to prevent large payload attacks"""
    content_length = request.headers.get("content-length")
    if content_length:
        size = int(content_length)
        if size > SECURITY_CONFIG["MAX_REQUEST_SIZE"]:
            return False
    return True

def sanitize_user_input(data: Any) -> Any:
    """Recursively sanitize user input"""
    if isinstance(data, str):
        return SecurityValidator.sanitize_string(data)
    elif isinstance(data, dict):
        return {k: sanitize_user_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_user_input(item) for item in data]
    else:
        return data
