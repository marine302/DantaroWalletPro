"""
감사 및 컴플라이언스 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_sync_db
from app.models.audit import AuditEventType, AuditLog, ComplianceCheck, SuspiciousActivity
from app.schemas.audit_compliance import (
    AuditLogResponse,
    ComplianceCheckRequest,
    ComplianceCheckResponse,
    SuspiciousActivityResponse,
    AnomalyDetectionRequest,
    AuditStatsResponse
)
from app.services.audit.audit_service import AuditService
from app.services.audit.compliance_service import ComplianceService
from app.services.audit.ml_anomaly_service import MLAnomalyDetectionService

router = APIRouter(prefix="/audit-compliance", tags=["audit-compliance"])

@router.post("/log-event")
async def log_audit_event(
    event_type: AuditEventType,
    entity_type: str,
    entity_id: str,
    event_data: Dict[str, Any],
    user_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    severity: str = "info",
    db: Session = Depends(get_sync_db)
):
    """감사 이벤트 로깅"""
    try:
        audit_service = AuditService(db)
        
        audit_log = await audit_service.log_event(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=event_data,
            user_id=user_id,
            partner_id=partner_id,
            severity=severity
        )
        
        return {"message": "감사 이벤트가 기록되었습니다", "audit_log_id": audit_log.id}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"감사 이벤트 로깅 실패: {str(e)}"
        )

@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    partner_id: Optional[int] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_sync_db)
):
    """감사 로그 조회"""
    try:
        audit_service = AuditService(db)
        
        logs = await audit_service.get_audit_logs(
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            partner_id=partner_id,
            limit=limit,
            offset=offset
        )
        
        return [AuditLogResponse.from_orm(log) for log in logs]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"감사 로그 조회 실패: {str(e)}"
        )

@router.post("/kyc-check", response_model=ComplianceCheckResponse)
async def perform_kyc_check(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_sync_db)
):
    """KYC 체크 수행"""
    try:
        compliance_service = ComplianceService(db)
        
        result = await compliance_service.perform_kyc_check(
            user_id=request.user_id,
            check_data=request.check_data
        )
        
        return ComplianceCheckResponse.from_orm(result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KYC 체크 실패: {str(e)}"
        )

@router.post("/aml-check", response_model=ComplianceCheckResponse)
async def perform_aml_check(
    user_id: int,
    transaction_amount: float,
    transaction_data: Dict[str, Any],
    db: Session = Depends(get_sync_db)
):
    """AML 체크 수행"""
    try:
        compliance_service = ComplianceService(db)
        
        result = await compliance_service.perform_aml_check(
            user_id=user_id,
            transaction_amount=transaction_amount,
            transaction_data=transaction_data
        )
        
        return ComplianceCheckResponse.from_orm(result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AML 체크 실패: {str(e)}"
        )

@router.post("/sanctions-check", response_model=ComplianceCheckResponse)
async def check_sanctions_list(
    name: str,
    address: Optional[str] = None,
    nationality: Optional[str] = None,
    db: Session = Depends(get_sync_db)
):
    """제재 목록 체크"""
    try:
        compliance_service = ComplianceService(db)
        
        result = await compliance_service.check_sanctions_list(
            name=name,
            address=address,
            nationality=nationality
        )
        
        return ComplianceCheckResponse.from_orm(result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"제재 목록 체크 실패: {str(e)}"
        )

@router.post("/pep-check", response_model=ComplianceCheckResponse)
async def check_pep_status(
    name: str,
    position: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_sync_db)
):
    """PEP 체크"""
    try:
        compliance_service = ComplianceService(db)
        
        result = await compliance_service.check_pep_status(
            name=name,
            position=position,
            country=country
        )
        
        return ComplianceCheckResponse.from_orm(result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PEP 체크 실패: {str(e)}"
        )

@router.post("/detect-anomalies", response_model=List[SuspiciousActivityResponse])
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: Session = Depends(get_sync_db)
):
    """이상 활동 탐지"""
    try:
        ml_service = MLAnomalyDetectionService(db)
        
        if request.transaction_data:
            # 트랜잭션 이상 탐지
            result = await ml_service.detect_transaction_anomalies(
                user_id=request.user_id,
                transaction_data=request.transaction_data
            )
            return [SuspiciousActivityResponse.from_orm(result)] if result else []
        else:
            # 사용자 행동 이상 탐지
            results = await ml_service.detect_user_behavior_anomalies(
                user_id=request.user_id,
                time_window_days=request.time_window_days or 30
            )
            return [SuspiciousActivityResponse.from_orm(result) for result in results]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이상 탐지 실패: {str(e)}"
        )

@router.get("/suspicious-activities", response_model=List[SuspiciousActivityResponse])
async def get_suspicious_activities(
    user_id: Optional[int] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_sync_db)
):
    """의심스러운 활동 목록 조회"""
    try:
        query = db.query(SuspiciousActivity)
        
        if user_id:
            query = query.filter(SuspiciousActivity.user_id == user_id)
        if severity:
            query = query.filter(SuspiciousActivity.severity == severity)
        
        activities = query.order_by(SuspiciousActivity.detected_at.desc()).offset(offset).limit(limit).all()
        
        return [SuspiciousActivityResponse.from_orm(activity) for activity in activities]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"의심스러운 활동 조회 실패: {str(e)}"
        )

@router.get("/compliance-history", response_model=List[ComplianceCheckResponse])
async def get_compliance_history(
    entity_type: str,
    entity_id: str,
    check_type: Optional[str] = None,
    limit: int = Query(50, le=500),
    db: Session = Depends(get_sync_db)
):
    """컴플라이언스 체크 이력 조회"""
    try:
        compliance_service = ComplianceService(db)
        
        history = await compliance_service.get_compliance_history(
            entity_type=entity_type,
            entity_id=entity_id,
            check_type=check_type,
            limit=limit
        )
        
        return [ComplianceCheckResponse.from_orm(check) for check in history]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"컴플라이언스 이력 조회 실패: {str(e)}"
        )

@router.get("/pending-reviews", response_model=List[ComplianceCheckResponse])
async def get_pending_reviews(db: Session = Depends(get_sync_db)):
    """수동 검토 대기 목록"""
    try:
        compliance_service = ComplianceService(db)
        
        pending = await compliance_service.get_pending_reviews()
        
        return [ComplianceCheckResponse.from_orm(check) for check in pending]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대기 목록 조회 실패: {str(e)}"
        )

@router.get("/audit-chain-verification")
async def verify_audit_chain(
    start_id: Optional[int] = None,
    db: Session = Depends(get_sync_db)
):
    """감사 체인 무결성 검증"""
    try:
        audit_service = AuditService(db)
        
        verification_result = await audit_service.verify_audit_chain(start_id)
        
        return verification_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"감사 체인 검증 실패: {str(e)}"
        )

@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_sync_db)
):
    """감사 및 컴플라이언스 통계"""
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 감사 로그 통계
        total_logs = db.query(AuditLog).filter(AuditLog.timestamp >= start_date).count()
        critical_logs = db.query(AuditLog).filter(
            AuditLog.timestamp >= start_date,
            AuditLog.severity == "critical"
        ).count()
        
        # 컴플라이언스 체크 통계
        total_checks = db.query(ComplianceCheck).filter(
            ComplianceCheck.initiated_at >= start_date
        ).count()
        failed_checks = db.query(ComplianceCheck).filter(
            ComplianceCheck.initiated_at >= start_date,
            ComplianceCheck.status == "failed"
        ).count()
        
        # 의심스러운 활동 통계
        suspicious_activities = db.query(SuspiciousActivity).filter(
            SuspiciousActivity.detected_at >= start_date
        ).count()
        
        return AuditStatsResponse(
            period_days=days,
            total_audit_logs=total_logs,
            critical_logs=critical_logs,
            total_compliance_checks=total_checks,
            failed_checks=failed_checks,
            suspicious_activities=suspicious_activities,
            compliance_success_rate=((total_checks - failed_checks) / total_checks * 100) if total_checks > 0 else 0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 실패: {str(e)}"
        )
