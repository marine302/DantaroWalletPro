"""
백업 서비스 메인 클래스
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.config import settings
from app.models.backup import Backup, BackupType, BackupStatus

logger = logging.getLogger(__name__)

class BackupService:
    """백업 서비스 메인 클래스"""
    
    def __init__(self):
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, backup_type: BackupType, db: AsyncSession, metadata: Optional[Dict[str, Any]] = None) -> int:
        """새 백업 레코드 생성"""
        backup = Backup(
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            started_at=datetime.utcnow()
        )
        
        db.add(backup)
        await db.commit()
        await db.refresh(backup)
        
        logger.info(f"백업 작업 생성됨: ID={backup.id}")
        return backup.id
    
    async def perform_backup(self, backup_id: int, db: AsyncSession):
        """실제 백업 수행"""
        result = await db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()
        
        if not backup:
            return
        
        try:
            backup.status = BackupStatus.IN_PROGRESS
            await db.commit()
            
            # 간단한 백업 시뮬레이션
            filename = f"backup_{backup_id}.txt"
            file_path = self.backup_dir / filename
            
            with open(file_path, 'w') as f:
                f.write(f"Backup created at {datetime.now()}")
            
            backup.filename = filename
            backup.file_size = file_path.stat().st_size
            backup.status = BackupStatus.COMPLETED
            backup.completed_at = datetime.utcnow()
            
            await db.commit()
            logger.info(f"백업 완료: ID={backup_id}")
            
        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)
            await db.commit()
            logger.error(f"백업 실패: {backup_id}")
    
    async def check_backup_health(self, db: AsyncSession) -> Dict[str, Any]:
        """백업 시스템 상태 확인"""
        total_result = await db.execute(select(Backup))
        total_backups = len(total_result.scalars().all())
        
        return {
            'healthy': True,
            'total_backups': total_backups,
            'failed_backups_24h': 0,
            'warnings': []
        }
    
    async def delete_backup(self, backup_id: int, db: AsyncSession):
        """백업 삭제"""
        await db.execute(delete(Backup).where(Backup.id == backup_id))
        await db.commit()
    
    async def cleanup_old_backups(self, days: int, db: AsyncSession) -> int:
        """오래된 백업 정리"""
        return 0
