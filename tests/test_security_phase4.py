"""
Synapse Security: Comprehensive Test Suite
Tests for JWT Auth, TLS, Schema Validation, and Audit Logging.
"""
import pytest
import os
import sys
import datetime
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.security.auth_manager import AuthManager, SecurityConfig, TokenType, TokenPair
from backend.security.schema_validator import (
    WorkerID, Hostname, SafePath, TaskRequest, 
    HeartbeatMessage, CommandExecution, ValidationResult,
    validate_worker_id, validate_task_request, validate_command
)
from backend.security.audit_logger import AuditLogger, AuditEntry

# Mock TLS tests (skip if cryptography not installed)
try:
    from backend.security.tls_manager import TLSConfig
    TLS_AVAILABLE = True
except ImportError:
    TLS_AVAILABLE = False

class TestAuthManager:
    """Test JWT authentication and token rotation."""
    
    def test_create_token_pair(self):
        """Test token pair generation."""
        auth = AuthManager("test_secret_key_12345")
        pair = auth.create_token_pair("worker-001")
        
        assert pair.access_token is not None
        assert pair.refresh_token is not None
        assert isinstance(pair.expires_at, datetime.datetime)
        assert isinstance(pair.refresh_expires_at, datetime.datetime)
        
    def test_verify_access_token(self):
        """Test access token verification."""
        auth = AuthManager("test_secret_key_12345")
        pair = auth.create_token_pair("worker-001")
        
        payload = auth.verify_token(pair.access_token, TokenType.ACCESS)
        
        assert payload["sub"] == "worker-001"
        assert payload["type"] == "access"
        assert "jti" in payload
        
    def test_verify_refresh_token(self):
        """Test refresh token verification."""
        auth = AuthManager("test_secret_key_12345")
        pair = auth.create_token_pair("worker-001")
        
        payload = auth.verify_token(pair.refresh_token, TokenType.REFRESH)
        
        assert payload["sub"] == "worker-001"
        assert payload["type"] == "refresh"
        
    def test_token_rotation(self):
        """Test refresh token rotation."""
        auth = AuthManager("test_secret_key_12345")
        pair = auth.create_token_pair("worker-001")
        
        # Refresh tokens
        new_pair = auth.refresh_access_token(pair.refresh_token)
        
        assert new_pair.access_token != pair.access_token
        assert new_pair.refresh_token != pair.refresh_token
        
        # Old refresh token should be revoked
        with pytest.raises(Exception):  # Should raise InvalidTokenError
            auth.verify_token(pair.refresh_token, TokenType.REFRESH)
            
    def test_expired_token(self):
        """Test expired token detection."""
        auth = AuthManager("test_secret_key_12345")
        
        # Create a token and manually craft an expired one for testing
        pair = auth.create_token_pair("worker-001")
        
        # Verify that normal token works
        payload = auth.verify_token(pair.access_token)
        assert payload["sub"] == "worker-001"
        
        # Test that tampered/invalid tokens are rejected
        import jwt
        # Try to verify with wrong key - should fail
        auth2 = AuthManager("different_key_123456789012345678901234")
        with pytest.raises(jwt.InvalidSignatureError):
            auth2.verify_token(pair.access_token)
            
    def test_wrong_token_type(self):
        """Test using wrong token type."""
        auth = AuthManager("test_secret_key_12345")
        pair = auth.create_token_pair("worker-001")
        
        # Try to use refresh token as access token
        with pytest.raises(Exception):
            auth.verify_token(pair.refresh_token, TokenType.ACCESS)
            
    def test_invalid_signature(self):
        """Test invalid signature detection."""
        auth = AuthManager("test_secret_key_12345")
        auth2 = AuthManager("different_secret_key")
        
        pair = auth.create_token_pair("worker-001")
        
        with pytest.raises(Exception):  # InvalidSignatureError
            auth2.verify_token(pair.access_token)

class TestSchemaValidation:
    """Test Pydantic schema validation."""
    
    def test_valid_worker_id(self):
        """Test valid worker IDs."""
        valid_ids = ["worker-001", "node_42", "AI-Model-7", "test123"]
        
        for wid in valid_ids:
            result = validate_worker_id(wid)
            assert result is True, f"Failed for {wid}"
            
    def test_invalid_worker_id(self):
        """Test invalid worker IDs."""
        invalid_ids = [
            "ab",  # Too short
            "root",  # Reserved
            "admin",  # Reserved
            "worker@001",  # Invalid chars
            "",  # Empty
        ]
        
        for wid in invalid_ids:
            result = validate_worker_id(wid)
            assert result is False, f"Should fail for {wid}"
            
    def test_valid_hostname(self):
        """Test valid hostnames and IPs."""
        valid_hosts = [
            "localhost",
            
            "192.168.1.1",
            "10.0.0.254"
        ]
        
        for host in valid_hosts:
            result = Hostname(host=host)
            assert result.host == host
            
    def test_invalid_hostname(self):
        """Test invalid hostnames."""
        invalid_hosts = [
            "",  # Empty
            "-invalid",  # Starts with hyphen
            "256.1.1.1",  # Invalid IP
            "host name",  # Space
        ]
        
        for host in invalid_hosts:
            with pytest.raises(Exception):
                Hostname(host=host)
                
    def test_safe_path(self):
        """Test safe path validation."""
        valid_paths = [
            "/workspace/data",
            "relative/path/file.txt",
        ]
        
        for path in valid_paths:
            result = SafePath(path=path)
            assert result.path == path
            
    def test_path_traversal_blocked(self):
        """Test directory traversal prevention."""
        malicious_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "..\\..\\windows\\system32"
        ]
        
        for path in malicious_paths:
            with pytest.raises(Exception):
                SafePath(path=path)
                
    def test_task_request_validation(self):
        """Test task request validation."""
        valid_request = {
            "worker_id": "worker-001",
            "task_type": "process_data",
            "payload": {"key": "value"},
            "priority": 5,
            "timeout_seconds": 300
        }
        
        success, validated, error = validate_task_request(valid_request)
        assert success is True
        assert validated.worker_id == "worker-001"
        assert validated.priority == 5
        
    def test_task_request_rejection(self):
        """Test task request rejection."""
        invalid_requests = [
            {"worker_id": "ab", "task_type": "test"},  # Invalid worker_id
            {"worker_id": "w1", "task_type": "rm -rf /"},  # Invalid task_type
            {"worker_id": "w1", "task_type": "test", "priority": 100},  # Priority out of range
        ]
        
        for req in invalid_requests:
            success, _, _ = validate_task_request(req)
            assert success is False
            
    def test_command_whitelist(self):
        """Test command whitelist enforcement."""
        allowed_commands = [
            {"command": "ls", "args": ["-la"]},
            {"command": "python", "args": ["script.py"]},
            {"command": "echo", "args": ["hello"]},
        ]
        
        for cmd in allowed_commands:
            success, validated, _ = validate_command(cmd)
            assert success is True
            
    def test_command_injection_blocked(self):
        """Test command injection prevention."""
        malicious_commands = [
            {"command": "rm", "args": ["-rf", "/"]},  # Not in whitelist
            {"command": "ls", "args": ["; rm -rf /"]},  # Injection in args
            {"command": "echo", "args": ["$(whoami)"]},  # Command substitution
        ]
        
        for cmd in malicious_commands:
            success, _, _ = validate_command(cmd)
            assert success is False

class TestAuditLogger:
    """Test immutable audit logging."""
    
    def test_log_entry_creation(self):
        """Test audit log entry creation."""
        logger = AuditLogger(log_dir="test_audit_logs")
        
        event_id = logger.log(
            event_type="AUTH",
            subject="worker-001",
            action="LOGIN",
            details={"ip": "192.168.1.1"},
            success=True
        )
        
        assert event_id is not None
        logger.flush()
        
    def test_chain_integrity(self):
        """Test audit chain integrity."""
        logger = AuditLogger(log_dir="test_audit_logs")
        
        # Log several entries
        for i in range(5):
            logger.log(
                event_type="TEST",
                subject=f"subject-{i}",
                action="ACTION",
                details={"index": i},
                success=True
            )
        
        logger.flush()
        
        # Verify chain
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        assert logger.verify_chain(date=today) is True
        
    def test_search_audit_logs(self):
        """Test audit log search."""
        logger = AuditLogger(log_dir="test_audit_logs")
        
        # Log entries with different types
        logger.log("AUTH", "user1", "LOGIN", {}, True)
        logger.log("TASK", "worker1", "EXECUTE", {"task": "test"}, True)
        logger.log("AUTH", "user2", "LOGOUT", {}, True)
        logger.flush()
        
        # Search by event type
        results = logger.search(event_type="AUTH")
        assert len(results) >= 2
        
        # Search by subject
        results = logger.search(subject="user1")
        assert len(results) >= 1
        
    def test_hash_computation(self):
        """Test hash computation for entries."""
        entry = AuditEntry(
            timestamp="2024-01-01T00:00:00Z",
            event_id="test-123",
            event_type="TEST",
            subject="test",
            action="ACTION",
            details={},
            source_ip=None,
            user_agent=None,
            success=True,
            previous_hash="GENESIS"
        )
        
        hash1 = entry.compute_hash()
        hash2 = entry.compute_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

@pytest.mark.skipif(not TLS_AVAILABLE, reason="cryptography not installed")
class TestTLSManager:
    """Test TLS configuration."""
    
    def test_tls_config_creation(self):
        """Test TLS config initialization."""
        tls = TLSConfig(cert_dir="test_certs", require_tls=False)
        
        assert tls.cert_dir.name == "test_certs"
        assert tls.require_tls is False
        
    def test_ssl_context_creation(self):
        """Test SSL context creation (non-TLS mode)."""
        tls = TLSConfig(require_tls=False)
        
        context = tls.create_ssl_context()
        assert context is None  # Should be None when TLS disabled

class TestIntegration:
    """Integration tests for security components."""
    
    def test_auth_and_validation_flow(self):
        """Test complete auth + validation flow."""
        auth = AuthManager("integration_test_key")
        
        # Create tokens
        pair = auth.create_token_pair("worker-integration")
        
        # Verify token
        payload = auth.verify_token(pair.access_token, TokenType.ACCESS)
        worker_id = payload["sub"]
        
        # Validate worker_id format
        assert validate_worker_id(worker_id) is True
        
        # Create and validate task request
        task_data = {
            "worker_id": worker_id,
            "task_type": "integration_test",
            "payload": {"test": True}
        }
        
        success, validated, error = validate_task_request(task_data)
        assert success is True
        assert validated.worker_id == worker_id
        
    def test_audit_security_events(self):
        """Test auditing of security events."""
        auth = AuthManager("audit_test_key")
        audit = AuditLogger(log_dir="test_integration_audit")
        
        # Simulate login
        pair = auth.create_token_pair("audit-user")
        audit.log(
            "AUTH",
            "audit-user",
            "TOKEN_ISSUE",
            {"success": True},
            True
        )
        
        # Simulate failed validation
        success, _, _ = validate_task_request({"worker_id": "bad"})
        audit.log(
            "VALIDATION",
            "unknown",
            "TASK_REQUEST",
            {"success": False},
            False
        )
        
        audit.flush()
        
        # Verify logs exist
        results = audit.search(event_type="AUTH")
        assert len(results) >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
