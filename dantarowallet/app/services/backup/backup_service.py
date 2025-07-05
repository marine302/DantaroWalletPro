"""
백업 및 복구 서비스.
DB 백업/복구 및 백업 이력 관리.
"""
import os
from datetime import datetime
from typing import List, Optional

from app.schemas.admin import BackupCreateRequest, BackupInfoResponse
from sqlalchemy.ext.asyncio import AsyncSession

BACKUP_DIR = "backups"


class BackupService:
    def __init__(self, db: AsyncSession):
        self.db = db
        os.makedirs(BACKUP_DIR, exist_ok=True)

    async def create_backup(
        self, backup_type: str, description: Optional[str] = None
    ) -> BackupInfoResponse:
        # 파일명 생성
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{backup_type}_{now}.sql"
        file_path = os.path.join(BACKUP_DIR, filename)
        # DB 덤프 (sqlite 기준, 실제 운영환경에 맞게 조정 필요)
        os.system(f"sqlite3 ../dev.db .dump > {file_path}")
        file_size = os.path.getsize(file_path)
        return BackupInfoResponse(
            id=int(now),
            backup_type=backup_type,
            file_path=file_path,
            file_size=file_size,
            status="completed",
            created_at=datetime.now(),
            completed_at=datetime.now(),
            error_message=None,
        )

    async def list_backups(self) -> List[BackupInfoResponse]:
        backups = []
        for fname in os.listdir(BACKUP_DIR):
            if fname.endswith(".sql"):
                fpath = os.path.join(BACKUP_DIR, fname)
                stat = os.stat(fpath)
                backups.append(
                    BackupInfoResponse(
                        id=int(stat.st_mtime),
                        backup_type="manual" if "manual" in fname else "auto",
                        file_path=fpath,
                        file_size=stat.st_size,
                        status="completed",
                        created_at=datetime.fromtimestamp(stat.st_ctime),
                        completed_at=datetime.fromtimestamp(stat.st_mtime),
                        error_message=None,
                    )
                )
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups

    async def restore_backup(self, file_path: str) -> bool:
        # DB 복구 (sqlite 기준, 실제 운영환경에 맞게 조정 필요)
        if not os.path.exists(file_path):
            return False
        os.system(f"sqlite3 ../dev.db < {file_path}")
        return True
