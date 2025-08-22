"""
Security configuration for the AI Career Copilot system.
Centralizes all security-related settings and policies.
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    # Authentication
    enable_auth: bool = True
    jwt_secret: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_window: int = 60  # seconds
    rate_limit_max_requests: int = 100
    
    # Input Validation
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_string_length: int = 1000
    max_user_id_length: int = 100
    
    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True
    
    # Session Management
    session_timeout: int = 3600  # seconds
    max_failed_logins: int = 5
    account_lockout_duration: int = 900  # 15 minutes
    
    # CORS and Host Security
    allowed_origins: List[str] = None
    trusted_hosts: List[str] = None
    enable_cors: bool = True
    enable_trusted_hosts: bool = True
    
    # Security Headers
    enable_security_headers: bool = True
    enable_hsts: bool = True
    enable_csp: bool = True
    enable_xss_protection: bool = True
    
    # Logging and Monitoring
    enable_audit_logging: bool = True
    enable_security_monitoring: bool = True
    log_sensitive_data: bool = False
    
    # Database Security
    enable_input_sanitization: bool = True
    enable_query_validation: bool = True
    max_query_complexity: int = 10
    
    # API Security
    enable_api_rate_limiting: bool = True
    enable_request_validation: bool = True
    enable_response_encryption: bool = False
    
    def __post_init__(self):
        """Set default values after initialization"""
        if self.allowed_origins is None:
            self.allowed_origins = [
                "http://localhost:3000",
                "http://localhost:12000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:12000"
            ]
        
        if self.trusted_hosts is None:
            self.trusted_hosts = [
                "localhost",
                "127.0.0.1",
                "::1",
                "0.0.0.0"
            ]

def load_security_config() -> SecurityPolicy:
    """Load security configuration from environment variables"""
    
    return SecurityPolicy(
        # Authentication
        enable_auth=os.getenv("SECURITY_ENABLE_AUTH", "true").lower() == "true",
        jwt_secret=os.getenv("SECURITY_JWT_SECRET", "your-super-secret-jwt-key-change-in-production"),
        jwt_algorithm=os.getenv("SECURITY_JWT_ALGORITHM", "HS256"),
        jwt_expiry_hours=int(os.getenv("SECURITY_JWT_EXPIRY_HOURS", "24")),
        
        # Rate Limiting
        rate_limit_enabled=os.getenv("SECURITY_RATE_LIMIT_ENABLED", "true").lower() == "true",
        rate_limit_window=int(os.getenv("SECURITY_RATE_LIMIT_WINDOW", "60")),
        rate_limit_max_requests=int(os.getenv("SECURITY_RATE_LIMIT_MAX_REQUESTS", "100")),
        
        # Input Validation
        max_request_size=int(os.getenv("SECURITY_MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),
        max_string_length=int(os.getenv("SECURITY_MAX_STRING_LENGTH", "1000")),
        max_user_id_length=int(os.getenv("SECURITY_MAX_USER_ID_LENGTH", "100")),
        
        # Password Policy
        password_min_length=int(os.getenv("SECURITY_PASSWORD_MIN_LENGTH", "12")),
        password_require_uppercase=os.getenv("SECURITY_PASSWORD_REQUIRE_UPPERCASE", "true").lower() == "true",
        password_require_lowercase=os.getenv("SECURITY_PASSWORD_REQUIRE_LOWERCASE", "true").lower() == "true",
        password_require_digit=os.getenv("SECURITY_PASSWORD_REQUIRE_DIGIT", "true").lower() == "true",
        password_require_special=os.getenv("SECURITY_PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true",
        
        # Session Management
        session_timeout=int(os.getenv("SECURITY_SESSION_TIMEOUT", "3600")),
        max_failed_logins=int(os.getenv("SECURITY_MAX_FAILED_LOGINS", "5")),
        account_lockout_duration=int(os.getenv("SECURITY_ACCOUNT_LOCKOUT_DURATION", "900")),
        
        # CORS and Host Security
        allowed_origins=os.getenv("SECURITY_ALLOWED_ORIGINS", "").split(",") if os.getenv("SECURITY_ALLOWED_ORIGINS") else None,
        trusted_hosts=os.getenv("SECURITY_TRUSTED_HOSTS", "").split(",") if os.getenv("SECURITY_TRUSTED_HOSTS") else None,
        enable_cors=os.getenv("SECURITY_ENABLE_CORS", "true").lower() == "true",
        enable_trusted_hosts=os.getenv("SECURITY_ENABLE_TRUSTED_HOSTS", "true").lower() == "true",
        
        # Security Headers
        enable_security_headers=os.getenv("SECURITY_ENABLE_SECURITY_HEADERS", "true").lower() == "true",
        enable_hsts=os.getenv("SECURITY_ENABLE_HSTS", "true").lower() == "true",
        enable_csp=os.getenv("SECURITY_ENABLE_CSP", "true").lower() == "true",
        enable_xss_protection=os.getenv("SECURITY_ENABLE_XSS_PROTECTION", "true").lower() == "true",
        
        # Logging and Monitoring
        enable_audit_logging=os.getenv("SECURITY_ENABLE_AUDIT_LOGGING", "true").lower() == "true",
        enable_security_monitoring=os.getenv("SECURITY_ENABLE_SECURITY_MONITORING", "true").lower() == "true",
        log_sensitive_data=os.getenv("SECURITY_LOG_SENSITIVE_DATA", "false").lower() == "true",
        
        # Database Security
        enable_input_sanitization=os.getenv("SECURITY_ENABLE_INPUT_SANITIZATION", "true").lower() == "true",
        enable_query_validation=os.getenv("SECURITY_ENABLE_QUERY_VALIDATION", "true").lower() == "true",
        max_query_complexity=int(os.getenv("SECURITY_MAX_QUERY_COMPLEXITY", "10")),
        
        # API Security
        enable_api_rate_limiting=os.getenv("SECURITY_ENABLE_API_RATE_LIMITING", "true").lower() == "true",
        enable_request_validation=os.getenv("SECURITY_ENABLE_REQUEST_VALIDATION", "true").lower() == "true",
        enable_response_encryption=os.getenv("SECURITY_ENABLE_RESPONSE_ENCRYPTION", "false").lower() == "true",
    )

# Global security configuration instance
SECURITY_CONFIG = load_security_config()

def get_security_config() -> SecurityPolicy:
    """Get the global security configuration"""
    return SECURITY_CONFIG

def update_security_config(**kwargs) -> None:
    """Update security configuration at runtime"""
    global SECURITY_CONFIG
    
    for key, value in kwargs.items():
        if hasattr(SECURITY_CONFIG, key):
            setattr(SECURITY_CONFIG, key, value)

def validate_security_config() -> List[str]:
    """Validate security configuration and return any issues"""
    issues = []
    
    if SECURITY_CONFIG.jwt_secret == "your-super-secret-jwt-key-change-in-production":
        issues.append("JWT_SECRET is using default value - change in production")
    
    if SECURITY_CONFIG.jwt_secret == "":
        issues.append("JWT_SECRET is empty")
    
    if SECURITY_CONFIG.rate_limit_max_requests <= 0:
        issues.append("RATE_LIMIT_MAX_REQUESTS must be positive")
    
    if SECURITY_CONFIG.max_request_size <= 0:
        issues.append("MAX_REQUEST_SIZE must be positive")
    
    if SECURITY_CONFIG.password_min_length < 8:
        issues.append("PASSWORD_MIN_LENGTH should be at least 8")
    
    if SECURITY_CONFIG.session_timeout <= 0:
        issues.append("SESSION_TIMEOUT must be positive")
    
    return issues

def get_security_headers() -> Dict[str, str]:
    """Get security headers based on configuration"""
    headers = {}
    
    if not SECURITY_CONFIG.enable_security_headers:
        return headers
    
    # Basic security headers
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    
    if SECURITY_CONFIG.enable_xss_protection:
        headers["X-XSS-Protection"] = "1; mode=block"
    
    if SECURITY_CONFIG.enable_hsts:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    if SECURITY_CONFIG.enable_csp:
        headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https:;"
        )
    
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return headers

def is_production_environment() -> bool:
    """Check if running in production environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ["production", "prod", "live"]

def get_security_log_level() -> str:
    """Get appropriate log level for security events"""
    if is_production_environment():
        return "WARNING"
    return "INFO"
