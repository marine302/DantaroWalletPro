from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum


class BackupType(str, Enum):
    DATABASE = "database"
    FILES = "files"
    FULL = "full"


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupCreateRequest(BaseModel):
    backup_type: BackupType
    auto_delete: Optional[bool] = False
    retention_days: Optional[int] = 30
    config: Optional[Dict[str, Any]] = None


class BackupResponse(BaseModel):
    id: int
    backup_type: BackupType
    status: BackupStatus
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    compression_type: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    config: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    auto_delete: bool = False
    retention_days: int = 30

    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    total: int
    backups: list[BackupResponse]


class BackupRestoreRequest(BaseModel):
    backup_id: int
    target_path: Optional[str] = None
    verify_checksum: Optional[bool] = True


class BackupRestoreResponse(BaseModel):
    success: bool
    message: str
    restored_files: Optional[list[str]] = None
