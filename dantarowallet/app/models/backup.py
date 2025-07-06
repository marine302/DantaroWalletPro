from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime
import enum

from app.models.base import Base


class BackupType(enum.Enum):
    DATABASE = "database"
    FILES = "files"
    FULL = "full"


class BackupStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    backup_type = Column(SQLEnum(BackupType), nullable=False)
    status = Column(SQLEnum(BackupStatus), default=BackupStatus.PENDING, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    compression_type = Column(String(50), default="gzip", nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Configuration and metadata
    config = Column(JSON, nullable=True)  # Store backup-specific config
    checksum = Column(String(64), nullable=True)  # SHA-256 hash
    
    # Auto-deletion settings
    auto_delete = Column(Boolean, default=False, nullable=False)
    retention_days = Column(Integer, default=30, nullable=False)
    
    def __repr__(self):
        return f"<Backup(id={self.id}, type={self.backup_type}, status={self.status})>"
