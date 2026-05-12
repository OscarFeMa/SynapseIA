"""
Synapse Security: JWT Authentication with Rotation
Manages Access/Refresh token lifecycle for secure worker-master communication.
"""
import jwt
import datetime
import hashlib
import os
import secrets
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"

@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_at: datetime.datetime
    refresh_expires_at: datetime.datetime

class SecurityConfig:
    """Centralized security configuration."""
    # Use environment variables, fallback to secure random if not set (for dev)
    SECRET_KEY = os.getenv("SYNAPSE_JWT_SECRET", secrets.token_hex(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SYNAPSE_ACCESS_EXPIRY", 15))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("SYNAPSE_REFRESH_EXPIRY", 7))
    
    # Security flags
    REQUIRE_SECURE_CONTEXT = os.getenv("SYNAPSE_REQUIRE_TLS", "false").lower() == "true"

class AuditLogger:
    """Immutable-style audit logger for security events."""
    
    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = log_file
        # In production, this should write to a write-only file descriptor or remote syslog
        
    def log(self, event_type: str, subject: str, details: Dict[str, Any], success: bool):
        timestamp = datetime.datetime.utcnow().isoformat()
        status = "SUCCESS" if success else "FAILURE"
        # Simple immutable append pattern
        entry = f"[{timestamp}] [{status}] [{event_type}] Subject: {subject} | Details: {details}\n"
        
        try:
            with open(self.log_file, "a") as f:
                f.write(entry)
        except Exception as e:
            # Fallback to stderr if file write fails (critical security event)
            print(f"AUDIT LOG FAILURE: {e} | Entry: {entry.strip()}")

audit_logger = AuditLogger()

class AuthManager:
    """Handles JWT issuance, validation, and rotation."""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or SecurityConfig.SECRET_KEY
        self.algorithm = SecurityConfig.ALGORITHM
        self._revoked_tokens: set = set()  # In-memory revocation list (use Redis in prod)

    def _generate_token(self, subject: str, token_type: TokenType, expires_delta: datetime.timedelta) -> str:
        now = datetime.datetime.utcnow()
        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + expires_delta,
            "type": token_type.value,
            "jti": secrets.token_hex(16)  # Unique ID for revocation
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_token_pair(self, worker_id: str) -> TokenPair:
        """Generate a new access/refresh token pair."""
        access_exp = datetime.timedelta(minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_exp = datetime.timedelta(days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = self._generate_token(worker_id, TokenType.ACCESS, access_exp)
        refresh_token = self._generate_token(worker_id, TokenType.REFRESH, refresh_exp)
        
        audit_logger.log("TOKEN_ISSUE", worker_id, {"type": "pair"}, True)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.datetime.utcnow() + access_exp,
            refresh_expires_at=datetime.datetime.utcnow() + refresh_exp
        )

    def verify_token(self, token: str, expected_type: Optional[TokenType] = None) -> Dict[str, Any]:
        """Verify token validity and type."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check revocation
            if payload.get("jti") in self._revoked_tokens:
                audit_logger.log("TOKEN_VERIFY", payload.get("sub"), {"reason": "revoked"}, False)
                raise jwt.InvalidTokenError("Token has been revoked")
            
            # Check type
            if expected_type and payload.get("type") != expected_type.value:
                audit_logger.log("TOKEN_VERIFY", payload.get("sub"), {"reason": "wrong_type"}, False)
                raise jwt.InvalidTokenError(f"Invalid token type. Expected {expected_type.value}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            audit_logger.log("TOKEN_VERIFY", "unknown", {"reason": "expired"}, False)
            raise
        except jwt.InvalidTokenError as e:
            audit_logger.log("TOKEN_VERIFY", "unknown", {"reason": str(e)}, False)
            raise

    def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Use a refresh token to get a new token pair."""
        try:
            payload = self.verify_token(refresh_token, TokenType.REFRESH)
            worker_id = payload["sub"]
            
            # Revoke old refresh token to prevent reuse (Rotation)
            self._revoked_tokens.add(payload["jti"])
            
            # Issue new pair
            return self.create_token_pair(worker_id)
            
        except jwt.InvalidTokenError:
            audit_logger.log("TOKEN_REFRESH", "unknown", {"reason": "invalid_refresh"}, False)
            raise

    def revoke_all_for_user(self, subject: str):
        """Logic to revoke all tokens for a user (requires persistent store in prod)."""
        # In a real implementation, this would query a DB for all JTIs for this subject
        # and add them to the revocation list or a blacklist database.
        audit_logger.log("TOKEN_REVOKE_ALL", subject, {}, True)

# Global instance
auth_manager = AuthManager()
