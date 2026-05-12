"""
Synapse Security: Pydantic Schema Validation
Strict validation for all incoming requests and data structures.
"""
from pydantic import BaseModel, Field, field_validator, ValidationError, ConfigDict
from typing import Optional, List, Dict, Any, ClassVar
import re
import logging

logger = logging.getLogger(__name__)

# Regex patterns for strict validation
WORKER_ID_PATTERN = r'^[a-zA-Z0-9_-]{3,64}$'
HOSTNAME_PATTERN = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$'
IP_PATTERN = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
SAFE_PATH_PATTERN = r'^[a-zA-Z0-9_/\-\.\s]+$'

class WorkerID(BaseModel):
    """Validated Worker ID."""
    worker_id: str = Field(
        ...,
        min_length=3,
        max_length=64,
        pattern=WORKER_ID_PATTERN,
        description="Worker identifier (alphanumeric, underscore, hyphen)"
    )
    
    @field_validator('worker_id')
    @classmethod
    @classmethod
    def validate_worker_id(cls, v):
        if not re.match(WORKER_ID_PATTERN, v):
            raise ValueError("Invalid worker_id format")
        if v.lower() in ['root', 'admin', 'system', 'master']:
            raise ValueError("Reserved worker_id not allowed")
        return v

class Hostname(BaseModel):
    """Validated Hostname or IP."""
    host: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('host')
    @classmethod
    @classmethod
    def validate_host(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Host cannot be empty")
        
        # Check if IP
        if re.match(IP_PATTERN, v):
            parts = v.split('.')
            for part in parts:
                if int(part) > 255:
                    raise ValueError("Invalid IP address")
            return v
        
        # Check if hostname
        if re.match(HOSTNAME_PATTERN, v):
            return v
        
        raise ValueError("Invalid hostname or IP address")

class SafePath(BaseModel):
    """Validated file system path (prevents directory traversal)."""
    path: str = Field(..., min_length=1, max_length=500)
    
    @field_validator('path')
    @classmethod
    @classmethod
    def validate_path(cls, v):
        if not re.match(SAFE_PATH_PATTERN, v):
            raise ValueError("Path contains invalid characters")
        
        # Prevent directory traversal
        if '..' in v:
            raise ValueError("Directory traversal not allowed")
        
        # Prevent absolute paths outside allowed areas
        if v.startswith('/') and not v.startswith('/workspace'):
            raise ValueError("Absolute path not in allowed directory")
        
        return v

class TaskRequest(BaseModel):
    """Strictly validated task request."""
    worker_id: str
    task_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=-10, le=10)
    timeout_seconds: Optional[int] = Field(default=None, ge=1, le=3600)
    
    @field_validator('worker_id')
    @classmethod
    def validate_worker_id(cls, v):
        return WorkerID(worker_id=v).worker_id
    
    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        if not v or len(v) > 100:
            raise ValueError("Invalid task_type")
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("task_type must be alphanumeric")
        return v
    
    @field_validator('payload')
    @classmethod
    def validate_payload(cls, v):
        # Limit payload size indirectly by limiting keys/depth
        if len(v) > 100:
            raise ValueError("Payload too large")
        return v

class HeartbeatMessage(BaseModel):
    """Strictly validated heartbeat message."""
    worker_id: str
    status: str = Field(..., pattern=r'^(alive|busy|idle|offline)$')
    health_score: int = Field(default=100, ge=0, le=100)
    timestamp: float
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('worker_id')
    @classmethod
    def validate_worker_id(cls, v):
        return WorkerID(worker_id=v).worker_id
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        if v and len(v) > 20:
            raise ValueError("Metadata too large")
        return v

class AuthTokenRequest(BaseModel):
    """Token request validation."""
    worker_id: str
    refresh_token: Optional[str] = None
    
    @field_validator('worker_id')
    @classmethod
    def validate_worker_id(cls, v):
        return WorkerID(worker_id=v).worker_id
    
    @field_validator('refresh_token')
    @classmethod
    def validate_refresh_token(cls, v):
        if v and len(v) < 10:
            raise ValueError("Invalid refresh token")
        return v

class CommandExecution(BaseModel):
    """Validated command for execution (whitelist approach)."""
    command: str = Field(..., max_length=200)
    args: List[str] = Field(default_factory=list)
    working_dir: Optional[str] = None
    
    ALLOWED_COMMANDS: ClassVar[set] = {'ls', 'dir', 'pwd', 'echo', 'python', 'pip', 'git'}
    
    @field_validator('command')
    @classmethod
    def validate_command(cls, v):
        v = v.strip().lower()
        if v not in cls.ALLOWED_COMMANDS:
            raise ValueError(f"Command '{v}' not in whitelist")
        return v
    
    @field_validator('args')
    @classmethod
    def validate_args(cls, v):
        for arg in v:
            if any(char in arg for char in [';', '|', '&', '$', '`', '>', '<']):
                raise ValueError("Invalid characters in arguments")
            if len(arg) > 500:
                raise ValueError("Argument too long")
        return v
    
    @field_validator('working_dir')
    @classmethod
    def validate_working_dir(cls, v):
        if v:
            return SafePath(path=v).path
        return v

class ValidationResult:
    """Wrapper for validation results."""
    
    @staticmethod
    def validate(model_class, data: dict) -> tuple[bool, Any, Optional[str]]:
        """
        Validate data against a Pydantic model.
        Returns: (success, validated_data_or_none, error_message_or_none)
        """
        try:
            validated = model_class(**data)
            return True, validated, None
        except ValidationError as e:
            logger.warning(f"Validation failed: {e}")
            return False, None, str(e)
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return False, None, f"Validation error: {str(e)}"

# Convenience functions
def validate_worker_id(worker_id: str) -> bool:
    success, _, _ = ValidationResult.validate(WorkerID, {"worker_id": worker_id})
    return success

def validate_hostname(host: str) -> bool:
    success, _, _ = ValidationResult.validate(Hostname, {"host": host})
    return success

def validate_task_request(data: dict) -> tuple[bool, Optional[TaskRequest], Optional[str]]:
    return ValidationResult.validate(TaskRequest, data)

def validate_heartbeat(data: dict) -> tuple[bool, Optional[HeartbeatMessage], Optional[str]]:
    return ValidationResult.validate(HeartbeatMessage, data)

def validate_command(data: dict) -> tuple[bool, Optional[CommandExecution], Optional[str]]:
    return ValidationResult.validate(CommandExecution, data)
