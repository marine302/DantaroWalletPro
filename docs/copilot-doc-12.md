# Copilot 문서 #12: 자동 백업 및 복구 시스템

## 목표
데이터베이스와 중요 파일의 자동 백업 시스템을 구축합니다. 일일 백업, 암호화, 외부 저장소 업로드, 복구 스크립트, 백업 상태 모니터링을 포함합니다.

## 전제 조건
- Copilot 문서 #1-11이 완료되어 있어야 합니다.
- AWS S3 또는 다른 클라우드 저장소 계정이 있어야 합니다.
- PostgreSQL pg_dump가 설치되어 있어야 합니다.

## 상세 지시사항

### 1. 백업 설정 모델 (app/models/backup.py)

```python
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Text, BigInteger
from datetime import datetime
from enum import Enum
from app.models.base import BaseModel

class BackupType(str, Enum):
    """백업 타입"""
    DATABASE = "database"
    FILES = "files"
    FULL = "full"
    INCREMENTAL = "incremental"

class BackupStatus(str, Enum):
    """백업 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    UPLOADED = "uploaded"
    VERIFIED = "verified"

class Backup(BaseModel):
    """백업 기록 모델"""
    
    # 백업 정보
    backup_type = Column(SQLEnum(BackupType), nullable=False)
    status = Column(SQLEnum(BackupStatus), nullable=False, default=BackupStatus.PENDING)
    
    # 파일 정보
    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=True)  # bytes
    file_hash = Column(String(64), nullable=True)  # SHA256
    
    # 저장소 정보
    storage_location = Column(String(500), nullable=True)  # S3 URL 등
    encrypted = Column(Boolean, default=True)
    
    # 시간 정보
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 백업 범위
    from_date = Column(DateTime(timezone=True), nullable=True)
    to_date = Column(DateTime(timezone=True), nullable=True)
    
    # 추가 정보
    metadata = Column(Text, nullable=True)  # JSON
    error_message = Column(Text, nullable=True)
    
    # 통계
    tables_backed_up = Column(Integer, nullable=True)
    records_backed_up = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Backup(id={self.id}, type={self.backup_type}, status={self.status})>"
```

### 2. 백업 서비스 (app/services/backup_service.py)

```python
import os
import subprocess
import asyncio
import boto3
import hashlib
import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.backup import Backup, BackupType, BackupStatus
from app.services.alert_service import alert_service, AlertLevel
from sqlalchemy import select

logger = logging.getLogger(__name__)

class BackupService:
    """백업 서비스"""
    
    def __init__(self):
        self.backup_dir = Path("/app/backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # S3 클라이언트
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.BACKUP_S3_BUCKET
        
        # 암호화 키
        self.encryption_key = settings.BACKUP_ENCRYPTION_KEY.encode()
        self.fernet = Fernet(self.encryption_key)
    
    async def backup_database(self) -> Backup:
        """데이터베이스 백업"""
        async with AsyncSessionLocal() as db:
            # 백업 기록 생성
            backup = Backup(
                backup_type=BackupType.DATABASE,
                status=BackupStatus.IN_PROGRESS,
                filename=f"db_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql.gz.enc"
            )
            db.add(backup)
            await db.commit()
            
            try:
                # 1. PostgreSQL 덤프
                dump_file = self.backup_dir / f"temp_dump_{backup.id}.sql"
                await self._run_pg_dump(dump_file)
                
                # 2. 압축
                compressed_file = await self._compress_file(dump_file)
                
                # 3. 암호화
                encrypted_file = await self._encrypt_file(compressed_file)
                
                # 4. 해시 계산
                file_hash = await self._calculate_hash(encrypted_file)
                
                # 5. S3 업로드
                s3_key = f"database/{backup.filename}"
                await self._upload_to_s3(encrypted_file, s3_key)
                
                # 6. 백업 정보 업데이트
                backup.status = BackupStatus.UPLOADED
                backup.completed_at = datetime.utcnow()
                backup.file_size = encrypted_file.stat().st_size
                backup.file_hash = file_hash
                backup.storage_location = f"s3://{self.bucket_name}/{s3_key}"
                
                # 통계 수집
                stats = await self._get_database_stats()
                backup.tables_backed_up = stats["tables"]
                backup.records_backed_up = stats["records"]
                backup.metadata = json.dumps(stats)
                
                await db.commit()
                
                # 임시 파일 정리
                await self._cleanup_temp_files([dump_file, compressed_file, encrypted_file])
                
                # 알림
                await alert_service.send_alert(
                    "Database Backup Completed",
                    f"Size: {backup.file_size / 1024 / 1024:.2f} MB\n"
                    f"Tables: {backup.tables_backed_up}\n"
                    f"Records: {backup.records_backed_up}",
                    AlertLevel.INFO,
                    "backup_completed"
                )
                
                logger.info(f"Database backup completed: {backup.filename}")
                
            except Exception as e:
                backup.status = BackupStatus.FAILED
                backup.error_message = str(e)
                await db.commit()
                
                logger.error(f"Database backup failed: {e}")
                
                await alert_service.send_alert(
                    "Database Backup Failed",
                    f"Error: {str(e)}",
                    AlertLevel.ERROR,
                    "backup_failed"
                )
                
                raise
            
            return backup
    
    async def _run_pg_dump(self, output_file: Path):
        """PostgreSQL 덤프 실행"""
        # DATABASE_URL 파싱
        from urllib.parse import urlparse
        db_url = urlparse(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
        
        cmd = [
            "pg_dump",
            "-h", db_url.hostname,
            "-p", str(db_url.port or 5432),
            "-U", db_url.username,
            "-d", db_url.path[1:],  # Remove leading slash
            "-f", str(output_file),
            "--no-owner",
            "--no-privileges",
            "--no-tablespaces",
            "--if-exists",
            "--clean"
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = db_url.password
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"pg_dump failed: {stderr.decode()}")
    
    async def _compress_file(self, input_file: Path) -> Path:
        """파일 압축"""
        output_file = input_file.with_suffix(input_file.suffix + '.gz')
        
        with open(input_file, 'rb') as f_in:
            with gzip.open(output_file, 'wb', compresslevel=9) as f_out:
                f_out.writelines(f_in)
        
        return output_file
    
    async def _encrypt_file(self, input_file: Path) -> Path:
        """파일 암호화"""
        output_file = input_file.with_suffix(input_file.suffix + '.enc')
        
        with open(input_file, 'rb') as f_in:
            encrypted_data = self.fernet.encrypt(f_in.read())
        
        with open(output_file, 'wb') as f_out:
            f_out.write(encrypted_data)
        
        return output_file
    
    async def _calculate_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    async def _upload_to_s3(self, file_path: Path, s3_key: str):
        """S3 업로드"""
        try:
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def _get_database_stats(self) -> Dict[str, Any]:
        """데이터베이스 통계 수집"""
        async with AsyncSessionLocal() as db:
            # 테이블 수
            result = await db.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            )
            table_count = result.scalar()
            
            # 주요 테이블별 레코드 수
            record_counts = {}
            tables = ['users', 'transactions', 'deposits', 'withdrawals', 'wallets']
            
            total_records = 0
            for table in tables:
                result = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                record_counts[table] = count
                total_records += count
            
            return {
                "tables": table_count,
                "records": total_records,
                "details": record_counts,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _cleanup_temp_files(self, files: List[Path]):
        """임시 파일 정리"""
        for file in files:
            try:
                if file.exists():
                    file.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp file {file}: {e}")
    
    async def backup_files(self) -> Backup:
        """중요 파일 백업 (설정, 로그 등)"""
        async with AsyncSessionLocal() as db:
            backup = Backup(
                backup_type=BackupType.FILES,
                status=BackupStatus.IN_PROGRESS,
                filename=f"files_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz.enc"
            )
            db.add(backup)
            await db.commit()
            
            try:
                # 백업할 디렉토리
                backup_targets = [
                    "/app/logs",
                    "/app/.env",
                    "/app/alembic",
                    "/app/scripts"
                ]
                
                # tar 생성
                tar_file = self.backup_dir / f"temp_files_{backup.id}.tar.gz"
                tar_cmd = ["tar", "-czf", str(tar_file)] + backup_targets
                
                process = await asyncio.create_subprocess_exec(
                    *tar_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                # 암호화
                encrypted_file = await self._encrypt_file(tar_file)
                
                # 해시 계산
                file_hash = await self._calculate_hash(encrypted_file)
                
                # S3 업로드
                s3_key = f"files/{backup.filename}"
                await self._upload_to_s3(encrypted_file, s3_key)
                
                # 백업 정보 업데이트
                backup.status = BackupStatus.UPLOADED
                backup.completed_at = datetime.utcnow()
                backup.file_size = encrypted_file.stat().st_size
                backup.file_hash = file_hash
                backup.storage_location = f"s3://{self.bucket_name}/{s3_key}"
                
                await db.commit()
                
                # 임시 파일 정리
                await self._cleanup_temp_files([tar_file, encrypted_file])
                
                logger.info(f"Files backup completed: {backup.filename}")
                
            except Exception as e:
                backup.status = BackupStatus.FAILED
                backup.error_message = str(e)
                await db.commit()
                
                logger.error(f"Files backup failed: {e}")
                raise
            
            return backup
    
    async def verify_backup(self, backup_id: int) -> bool:
        """백업 검증"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Backup).filter(Backup.id == backup_id)
            )
            backup = result.scalar_one_or_none()
            
            if not backup:
                raise ValueError(f"Backup {backup_id} not found")
            
            try:
                # S3에서 메타데이터 확인
                s3_key = backup.storage_location.replace(f"s3://{self.bucket_name}/", "")
                response = self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                
                # 파일 크기 확인
                if response['ContentLength'] != backup.file_size:
                    raise ValueError("File size mismatch")
                
                backup.status = BackupStatus.VERIFIED
                await db.commit()
                
                logger.info(f"Backup {backup_id} verified successfully")
                return True
                
            except Exception as e:
                logger.error(f"Backup verification failed: {e}")
                return False
    
    async def restore_database(self, backup_id: int, target_db: Optional[str] = None):
        """데이터베이스 복구"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Backup).filter(
                    Backup.id == backup_id,
                    Backup.backup_type == BackupType.DATABASE
                )
            )
            backup = result.scalar_one_or_none()
            
            if not backup:
                raise ValueError(f"Database backup {backup_id} not found")
            
            try:
                # 1. S3에서 다운로드
                s3_key = backup.storage_location.replace(f"s3://{self.bucket_name}/", "")
                encrypted_file = self.backup_dir / f"restore_{backup_id}.sql.gz.enc"
                
                self.s3_client.download_file(
                    self.bucket_name,
                    s3_key,
                    str(encrypted_file)
                )
                
                # 2. 복호화
                compressed_file = self.backup_dir / f"restore_{backup_id}.sql.gz"
                with open(encrypted_file, 'rb') as f_in:
                    decrypted_data = self.fernet.decrypt(f_in.read())
                
                with open(compressed_file, 'wb') as f_out:
                    f_out.write(decrypted_data)
                
                # 3. 압축 해제
                sql_file = self.backup_dir / f"restore_{backup_id}.sql"
                with gzip.open(compressed_file, 'rb') as f_in:
                    with open(sql_file, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                # 4. 데이터베이스 복구
                await self._run_pg_restore(sql_file, target_db)
                
                # 5. 임시 파일 정리
                await self._cleanup_temp_files([encrypted_file, compressed_file, sql_file])
                
                logger.info(f"Database restored from backup {backup_id}")
                
                await alert_service.send_alert(
                    "Database Restore Completed",
                    f"Backup ID: {backup_id}\n"
                    f"Original date: {backup.completed_at}",
                    AlertLevel.INFO,
                    "restore_completed"
                )
                
            except Exception as e:
                logger.error(f"Database restore failed: {e}")
                
                await alert_service.send_alert(
                    "Database Restore Failed",
                    f"Backup ID: {backup_id}\n"
                    f"Error: {str(e)}",
                    AlertLevel.CRITICAL,
                    "restore_failed"
                )
                
                raise
    
    async def _run_pg_restore(self, sql_file: Path, target_db: Optional[str] = None):
        """PostgreSQL 복구 실행"""
        from urllib.parse import urlparse
        db_url = urlparse(settings.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://'))
        
        # 타겟 DB 지정 가능 (테스트용)
        database = target_db or db_url.path[1:]
        
        cmd = [
            "psql",
            "-h", db_url.hostname,
            "-p", str(db_url.port or 5432),
            "-U", db_url.username,
            "-d", database,
            "-f", str(sql_file)
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = db_url.password
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"pg_restore failed: {stderr.decode()}")
    
    async def cleanup_old_backups(self, retention_days: int = 30):
        """오래된 백업 정리"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        async with AsyncSessionLocal() as db:
            # 오래된 백업 조회
            result = await db.execute(
                select(Backup).filter(
                    Backup.completed_at < cutoff_date,
                    Backup.status == BackupStatus.VERIFIED
                )
            )
            old_backups = result.scalars().all()
            
            deleted_count = 0
            for backup in old_backups:
                try:
                    # S3에서 삭제
                    s3_key = backup.storage_location.replace(f"s3://{self.bucket_name}/", "")
                    self.s3_client.delete_object(
                        Bucket=self.bucket_name,
                        Key=s3_key
                    )
                    
                    # DB에서 삭제
                    await db.delete(backup)
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to delete old backup {backup.id}: {e}")
            
            await db.commit()
            
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} old backups")
                
                await alert_service.send_alert(
                    "Old Backups Cleaned",
                    f"Deleted {deleted_count} backups older than {retention_days} days",
                    AlertLevel.INFO,
                    "backup_cleanup"
                )

# 글로벌 백업 서비스
backup_service = BackupService()
```

### 3. 백업 태스크 (app/tasks/backup_task.py)

```python
import asyncio
from datetime import datetime, time
import logging
from app.services.backup_service import backup_service
from app.services.alert_service import alert_service, AlertLevel

logger = logging.getLogger(__name__)

class BackupTask:
    """일일 백업 태스크"""
    
    def __init__(self):
        self.backup_time = time(2, 0)  # UTC 02:00 (한국시간 11:00)
    
    async def run_daily_backup(self):
        """일일 백업 실행"""
        try:
            logger.info("Starting daily backup...")
            
            # 1. 데이터베이스 백업
            db_backup = await backup_service.backup_database()
            
            # 2. 파일 백업
            files_backup = await backup_service.backup_files()
            
            # 3. 백업 검증
            db_verified = await backup_service.verify_backup(db_backup.id)
            files_verified = await backup_service.verify_backup(files_backup.id)
            
            if not db_verified or not files_verified:
                raise Exception("Backup verification failed")
            
            # 4. 오래된 백업 정리
            await backup_service.cleanup_old_backups()
            
            logger.info("Daily backup completed successfully")
            
        except Exception as e:
            logger.error(f"Daily backup failed: {e}")
            
            await alert_service.send_alert(
                "Daily Backup Failed",
                f"Error: {str(e)}",
                AlertLevel.CRITICAL,
                "daily_backup_failed"
            )
    
    async def run_forever(self):
        """백업 태스크 무한 루프"""
        while True:
            try:
                # 다음 백업 시간 계산
                now = datetime.utcnow()
                next_backup = now.replace(
                    hour=self.backup_time.hour,
                    minute=self.backup_time.minute,
                    second=0,
                    microsecond=0
                )
                
                if next_backup <= now:
                    # 이미 지났으면 다음 날로
                    next_backup = next_backup.replace(day=next_backup.day + 1)
                
                wait_seconds = (next_backup - now).total_seconds()
                
                logger.info(
                    f"Next backup scheduled at {next_backup} UTC "
                    f"({wait_seconds/3600:.1f} hours)"
                )
                
                await asyncio.sleep(wait_seconds)
                
                # 백업 실행
                await self.run_daily_backup()
                
            except Exception as e:
                logger.error(f"Backup task error: {e}")
                # 에러 발생 시 1시간 후 재시도
                await asyncio.sleep(3600)
```

### 4. 백업 복구 스크립트 (scripts/restore_backup.py)

```python
#!/usr/bin/env python
"""
백업 복구 스크립트
사용법: python restore_backup.py [backup_id] [--target-db=test_db]
"""
import asyncio
import sys
import argparse
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.services.backup_service import backup_service
from app.core.database import AsyncSessionLocal
from app.models.backup import Backup, BackupType, BackupStatus
from sqlalchemy import select

async def list_backups():
    """사용 가능한 백업 목록 표시"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Backup)
            .filter(
                Backup.backup_type == BackupType.DATABASE,
                Backup.status.in_([BackupStatus.UPLOADED, BackupStatus.VERIFIED])
            )
            .order_by(Backup.completed_at.desc())
            .limit(10)
        )
        backups = result.scalars().all()
        
        print("\nAvailable Database Backups:")
        print("-" * 80)
        print(f"{'ID':<5} {'Filename':<40} {'Size (MB)':<10} {'Date':<20}")
        print("-" * 80)
        
        for backup in backups:
            size_mb = backup.file_size / 1024 / 1024 if backup.file_size else 0
            date_str = backup.completed_at.strftime('%Y-%m-%d %H:%M:%S')
            print(f"{backup.id:<5} {backup.filename:<40} {size_mb:<10.2f} {date_str:<20}")
        
        return backups

async def restore_backup(backup_id: int, target_db: str = None):
    """백업 복구 실행"""
    print(f"\nRestoring backup ID: {backup_id}")
    if target_db:
        print(f"Target database: {target_db}")
    
    # 확인
    confirm = input("\nThis will overwrite the current database. Continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Restore cancelled.")
        return
    
    print("\nStarting restore process...")
    
    try:
        await backup_service.restore_database(backup_id, target_db)
        print("\n✅ Restore completed successfully!")
    except Exception as e:
        print(f"\n❌ Restore failed: {e}")
        sys.exit(1)

async def main():
    parser = argparse.ArgumentParser(description='Restore database from backup')
    parser.add_argument('backup_id', type=int, nargs='?', help='Backup ID to restore')
    parser.add_argument('--target-db', help='Target database name (optional)')
    parser.add_argument('--list', action='store_true', help='List available backups')
    
    args = parser.parse_args()
    
    if args.list or not args.backup_id:
        await list_backups()
        if not args.backup_id:
            print("\nUsage: python restore_backup.py [backup_id] [--target-db=test_db]")
    else:
        await restore_backup(args.backup_id, args.target_db)

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. 수동 백업 스크립트 (scripts/manual_backup.py)

```python
#!/usr/bin/env python
"""
수동 백업 실행 스크립트
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.services.backup_service import backup_service

async def main():
    print("Starting manual backup...")
    
    try:
        # 데이터베이스 백업
        print("\n1. Backing up database...")
        db_backup = await backup_service.backup_database()
        print(f"   ✅ Database backup completed: {db_backup.filename}")
        
        # 파일 백업
        print("\n2. Backing up files...")
        files_backup = await backup_service.backup_files()
        print(f"   ✅ Files backup completed: {files_backup.filename}")
        
        # 검증
        print("\n3. Verifying backups...")
        db_verified = await backup_service.verify_backup(db_backup.id)
        files_verified = await backup_service.verify_backup(files_backup.id)
        
        if db_verified and files_verified:
            print("   ✅ All backups verified successfully!")
        else:
            print("   ⚠️  Some backups failed verification")
        
        print("\n✅ Manual backup completed!")
        
    except Exception as e:
        print(f"\n❌ Backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. 백그라운드 태스크 업데이트 (app/core/background.py)

기존 파일에 백업 태스크 추가:

```python
async def startup(self):
    """애플리케이션 시작 시 태스크 실행"""
    from app.tasks.daily_report import DailyReportTask
    from app.services.blockchain_monitor import blockchain_monitor
    from app.tasks.backup_task import BackupTask
    
    # 일일 리포트 태스크
    daily_report = DailyReportTask()
    self.add_task(daily_report.run_forever, "daily_report")
    
    # 블록체인 모니터 시작
    await blockchain_monitor.start()
    
    # 백업 태스크
    backup_task = BackupTask()
    self.add_task(backup_task.run_forever, "backup_task")
```

### 7. 백업 엔드포인트 (app/api/v1/endpoints/backup.py)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.backup import Backup
from app.services.backup_service import backup_service
from app.schemas.backup import BackupResponse, BackupListResponse

router = APIRouter()

@router.get("/list", response_model=BackupListResponse)
async def list_backups(
    current_user: User = Depends(deps.get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """백업 목록 조회 (관리자)"""
    result = await db.execute(
        select(Backup).order_by(Backup.created_at.desc()).limit(50)
    )
    backups = result.scalars().all()
    
    # 통계 계산
    total_size = sum(b.file_size or 0 for b in backups)
    successful_count = sum(1 for b in backups if b.status in ['uploaded', 'verified'])
    
    return BackupListResponse(
        items=backups,
        total_count=len(backups),
        total_size=total_size,
        successful_count=successful_count
    )

@router.post("/manual")
async def trigger_manual_backup(
    current_user: User = Depends(deps.get_current_admin_user)
):
    """수동 백업 실행 (관리자)"""
    try:
        # 백업 실행
        db_backup = await backup_service.backup_database()
        files_backup = await backup_service.backup_files()
        
        return {
            "message": "Backup initiated successfully",
            "database_backup_id": db_backup.id,
            "files_backup_id": files_backup.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{backup_id}/verify")
async def verify_backup(
    backup_id: int,
    current_user: User = Depends(deps.get_current_admin_user)
):
    """백업 검증 (관리자)"""
    verified = await backup_service.verify_backup(backup_id)
    return {"verified": verified}

@router.delete("/cleanup")
async def cleanup_old_backups(
    retention_days: int = 30,
    current_user: User = Depends(deps.get_current_admin_user)
):
    """오래된 백업 정리 (관리자)"""
    await backup_service.cleanup_old_backups(retention_days)
    return {"message": f"Cleaned up backups older than {retention_days} days"}
```

### 8. 백업 스키마 (app/schemas/backup.py)

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.backup import BackupType, BackupStatus

class BackupResponse(BaseModel):
    """백업 응답 스키마"""
    id: int
    backup_type: BackupType
    status: BackupStatus
    filename: str
    file_size: Optional[int]
    file_hash: Optional[str]
    storage_location: Optional[str]
    encrypted: bool
    started_at: datetime
    completed_at: Optional[datetime]
    tables_backed_up: Optional[int]
    records_backed_up: Optional[int]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class BackupListResponse(BaseModel):
    """백업 목록 응답"""
    items: List[BackupResponse]
    total_count: int
    total_size: int  # bytes
    successful_count: int
```

### 9. 환경 변수 추가 (.env)

```env
# 기존 변수들...

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=ap-northeast-2
BACKUP_S3_BUCKET=dantarowallet-backups

# Backup
BACKUP_ENCRYPTION_KEY=your-32-byte-encryption-key-base64
```

### 10. 설정 파일 업데이트 (app/core/config.py)

```python
class Settings(BaseSettings):
    # 기존 설정들...
    
    # AWS
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-northeast-2"
    BACKUP_S3_BUCKET: str
    
    # Backup
    BACKUP_ENCRYPTION_KEY: str
    
    # 기존 설정 계속...
```

### 11. 모델 업데이트 (app/models/__init__.py)

```python
from app.models.base import BaseModel
from app.models.user import User
from app.models.balance import Balance
from app.models.transaction import Transaction, TransactionType, TransactionStatus, TransactionDirection
from app.models.wallet import Wallet
from app.models.deposit import Deposit, DepositStatus
from app.models.withdrawal import Withdrawal, WithdrawalStatus, WithdrawalPriority
from app.models.backup import Backup, BackupType, BackupStatus

__all__ = [
    "BaseModel", "User", "Balance", "Transaction", "Wallet", "Deposit", "Withdrawal", "Backup",
    "TransactionType", "TransactionStatus", "TransactionDirection", 
    "DepositStatus", "WithdrawalStatus", "WithdrawalPriority",
    "BackupType", "BackupStatus"
]
```

### 12. API 라우터 업데이트 (app/api/v1/api.py)

```python
from fastapi import APIRouter
from app.api.v1.endpoints import auth, balance, wallet, monitoring, deposits, withdrawals, backup

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(balance.router, prefix="/balance", tags=["balance"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["wallet"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(deposits.router, prefix="/deposits", tags=["deposits"])
api_router.include_router(withdrawals.router, prefix="/withdrawals", tags=["withdrawals"])
api_router.include_router(backup.router, prefix="/backup", tags=["backup"])

@api_router.get("/test")
async def test_endpoint():
    return {"message": "API v1 is working"}
```

### 13. 마이그레이션 생성

```bash
# Backup 테이블 추가
poetry run alembic revision --autogenerate -m "Add backup table"
poetry run alembic upgrade head
```

### 14. 의존성 추가 (pyproject.toml)

```toml
# dependencies 섹션에 추가
boto3 = "^1.28.0"
cryptography = "^41.0.0"
```

### 15. 백업 복구 문서 (docs/backup-recovery.md)

```markdown
# DantaroWallet 백업 및 복구 가이드

## 백업 스케줄
- **일일 백업**: 매일 UTC 02:00 (한국시간 11:00)
- **보관 기간**: 30일
- **저장 위치**: AWS S3 (암호화)

## 백업 내용
1. **데이터베이스**: 모든 테이블과 데이터
2. **파일**: 로그, 설정, 스크립트

## 수동 백업
```bash
python scripts/manual_backup.py
```

## 백업 복구

### 1. 백업 목록 확인
```bash
python scripts/restore_backup.py --list
```

### 2. 백업 복구 실행
```bash
# 프로덕션 DB 복구 (주의!)
python scripts/restore_backup.py [backup_id]

# 테스트 DB로 복구
python scripts/restore_backup.py [backup_id] --target-db=test_db
```

## 재해 복구 절차

### 1. 시스템 장애 시
1. 새 서버 준비
2. Docker 및 의존성 설치
3. 애플리케이션 코드 배포
4. 환경 변수 설정
5. 최신 백업으로 DB 복구
6. 서비스 시작

### 2. 데이터 손실 시
1. 긴급 정지 활성화
2. 손실 범위 확인
3. 적절한 백업 선택
4. 테스트 DB로 먼저 복구
5. 데이터 검증
6. 프로덕션 복구

## 모니터링
- 백업 성공/실패 시 Telegram 알림
- 관리자 대시보드에서 백업 상태 확인
- S3 콘솔에서 백업 파일 확인

## 주의사항
⚠️ 복구는 되돌릴 수 없습니다
⚠️ 복구 전 현재 상태 백업 필수
⚠️ 테스트 환경에서 먼저 검증
```

## 실행 및 검증

1. S3 버킷 생성:
   ```bash
   aws s3 mb s3://dantarowallet-backups
   ```

2. 의존성 설치:
   ```bash
   poetry add boto3 cryptography
   ```

3. 마이그레이션 실행:
   ```bash
   make db-upgrade
   ```

4. 서버 재시작:
   ```bash
   make dev
   ```

5. 수동 백업 테스트:
   ```bash
   poetry run python scripts/manual_backup.py
   ```

6. 백업 목록 확인:
   ```bash
   poetry run python scripts/restore_backup.py --list
   ```

## 검증 포인트

- [ ] 일일 백업이 예약된 시간에 실행되는가?
- [ ] 데이터베이스 백업이 성공하는가?
- [ ] 파일 백업이 성공하는가?
- [ ] 백업이 암호화되어 저장되는가?
- [ ] S3에 업로드가 완료되는가?
- [ ] 백업 검증이 작동하는가?
- [ ] 복구 스크립트가 정상 작동하는가?
- [ ] 오래된 백업이 자동 삭제되는가?
- [ ] 백업 실패 시 알림이 전송되는가?

이 문서를 완료하면 자동화된 백업 및 복구 시스템이 구축되어, 재해 상황에서도 데이터를 안전하게 보호하고 신속하게 복구할 수 있습니다.