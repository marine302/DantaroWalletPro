"""
백업 서비스 모듈
데이터베이스와 파일 백업을 담당합니다.
"""
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import setup_logging

logger = setup_logging()


class BackupService:
    """백업 서비스 클래스"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_database_backup(self, backup_name: Optional[str] = None) -> str:
        """데이터베이스 백업 생성"""
        try:
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"db_backup_{timestamp}.db"
            
            backup_path = self.backup_dir / backup_name
            
            # SQLite 데이터베이스 백업
            db_path = "dev.db"
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                logger.info(f"✅ 데이터베이스 백업 생성: {backup_path}")
                return str(backup_path)
            else:
                logger.warning("❌ 데이터베이스 파일이 존재하지 않습니다")
                return ""
                
        except Exception as e:
            logger.error(f"❌ 백업 생성 실패: {e}")
            raise
    
    async def restore_database_backup(self, backup_path: str) -> bool:
        """데이터베이스 백업 복원"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"❌ 백업 파일이 존재하지 않습니다: {backup_path}")
                return False
            
            # 현재 DB 백업
            current_backup = await self.create_database_backup("current_backup.db")
            
            # 백업 복원
            shutil.copy2(backup_path, "dev.db")
            logger.info(f"✅ 데이터베이스 복원 완료: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 백업 복원 실패: {e}")
            return False
    
    async def list_backups(self) -> list:
        """백업 파일 목록 조회"""
        try:
            backups = []
            for backup_file in self.backup_dir.glob("*.db"):
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime)
                })
            
            return sorted(backups, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ 백업 목록 조회 실패: {e}")
            return []
    
    async def delete_backup(self, backup_name: str) -> bool:
        """백업 파일 삭제"""
        try:
            backup_path = self.backup_dir / backup_name
            if backup_path.exists():
                backup_path.unlink()
                logger.info(f"✅ 백업 파일 삭제: {backup_name}")
                return True
            else:
                logger.warning(f"❌ 백업 파일이 존재하지 않습니다: {backup_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 백업 파일 삭제 실패: {e}")
            return False