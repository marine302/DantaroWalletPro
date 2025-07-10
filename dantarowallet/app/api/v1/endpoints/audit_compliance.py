"""
감사 및 컴플라이언스 API 엔드포인트 - Doc #30
트랜잭션 감사 및 컴플라이언스 관련 API
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_admin_user, get_current_user
from app.services.audit.audit_service import AuditService, safe_int
from app.services.audit.compliance_service import ComplianceService
from app.services.audit.ml_anomaly_service import MLAnomalyDetectionService
from app.models.audit import (
    AuditEventType, ComplianceCheckType, ComplianceStatus, RiskLevel
)
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Pydantic 스키마
class AuditLogResponse(BaseModel):
    """감사 로그 응답"""
    id: int
    timestamp: datetime
    event_type: str
    event_category: str
    severity: str
    entity_type: str
    entity_id: str
    partner_id: Optional[int]
    user_id: Optional[int]
    event_data: Dict[str, Any]
    ip_address: Optional[str]
    risk_score: int
    requires_review: bool
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """감사 로그 목록 응답"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    size: int


class ComplianceCheckResponse(BaseModel):
    """컴플라이언스 체크 응답"""
    id: int
    check_type: str
    entity_type: str
    entity_id: str
    status: str
    risk_level: str
    score: int
    check_data: Dict[str, Any]
    initiated_at: datetime
    completed_at: Optional[datetime]
    manual_review_notes: Optional[str]
    
    class Config:
        from_attributes = True


class SuspiciousActivityResponse(BaseModel):
    """의심스러운 활동 응답"""
    id: int
    detection_type: str
    severity: str
    user_id: int
    transaction_ids: List[str]
    pattern_name: Optional[str]
    pattern_data: Dict[str, Any]
    confidence_score: float
    description: Optional[str]
    action_taken: Optional[str]
    detected_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]
    
    class Config:
        from_attributes = True


class AuditStatisticsResponse(BaseModel):
    """감사 통계 응답"""
    period: Dict[str, str]
    total_logs: int
    event_type_stats: Dict[str, int]
    severity_stats: Dict[str, int]
    review_required: int


class ComplianceStatisticsResponse(BaseModel):
    """컴플라이언스 통계 응답"""
    period: Dict[str, str]
    total_checks: int
    check_type_stats: Dict[str, int]
    status_stats: Dict[str, int]
    risk_stats: Dict[str, int]


class DetectionStatisticsResponse(BaseModel):
    """탐지 통계 응답"""
    period: Dict[str, str]
    total_detections: int
    detection_type_stats: Dict[str, int]
    severity_stats: Dict[str, int]
    resolution_stats: Dict[str, Any]


class KYCCheckRequest(BaseModel):
    """KYC 체크 요청"""
    user_id: int
    kyc_level: str = Field(default="basic", description="KYC 레벨")
    documents: List[str] = Field(default_factory=list, description="제출된 문서 목록")
    method: str = Field(default="automated", description="검증 방법")


class AMLCheckRequest(BaseModel):
    """AML 체크 요청"""
    transaction_id: str
    amount: str
    currency: str = "USDT"
    from_address: str
    to_address: str
    transaction_type: str
    user_id: Optional[int] = None
    partner_id: Optional[int] = None


class SanctionsCheckRequest(BaseModel):
    """제재 목록 체크 요청"""
    entity_type: str
    entity_id: str
    entity_data: Dict[str, Any]


class ResolveSuspiciousActivityRequest(BaseModel):
    """의심스러운 활동 해결 요청"""
    resolution_notes: str
    action_taken: str = Field(default="reviewed", description="취한 조치")


# 감사 로그 관련 엔드포인트
@router.get("/audit/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(100, ge=1, le=1000, description="페이지 크기"),
    event_type: Optional[str] = Query(None, description="이벤트 타입"),
    entity_type: Optional[str] = Query(None, description="엔티티 타입"),
    entity_id: Optional[str] = Query(None, description="엔티티 ID"),
    user_id: Optional[int] = Query(None, description="사용자 ID"),
    partner_id: Optional[int] = Query(None, description="파트너 ID"),
    severity: Optional[str] = Query(None, description="심각도"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    requires_review: Optional[bool] = Query(None, description="검토 필요 여부"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """감사 로그 조회"""
    try:
        audit_service = AuditService(db)
        
        # 날짜 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # 이벤트 타입 변환
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 이벤트 타입: {event_type}"
                )
        
        # 오프셋 계산
        offset = (page - 1) * size
        
        # 로그 조회
        logs = await audit_service.get_audit_logs(
            limit=size,
            offset=offset,
            event_type=event_type_enum,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            partner_id=partner_id,
            severity=severity,
            start_date=start_datetime,
            end_date=end_datetime,
            requires_review=requires_review
        )
        
        # 총 개수 조회
        total = await audit_service.get_audit_log_count(
            event_type=event_type_enum,
            entity_type=entity_type,
            severity=severity,
            start_date=start_datetime,
            end_date=end_datetime,
            requires_review=requires_review
        )
        
        return AuditLogListResponse(
            logs=[AuditLogResponse.from_orm(log) for log in logs],
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        logger.error(f"감사 로그 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="감사 로그 조회 중 오류가 발생했습니다"
        )


@router.get("/audit/logs/{log_id}")
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """특정 감사 로그 조회"""
    try:
        audit_service = AuditService(db)
        
        logs = await audit_service.get_audit_logs(
            limit=1,
            offset=0,
            entity_id=str(log_id)
        )
        
        if not logs:
            raise HTTPException(
                status_code=404,
                detail="감사 로그를 찾을 수 없습니다"
            )
        
        log = logs[0]
        
        # 무결성 검증
        is_valid = await audit_service.verify_log_integrity(log_id)
        
        response = AuditLogResponse.from_orm(log)
        return {
            **response.dict(),
            "integrity_verified": is_valid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"감사 로그 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="감사 로그 조회 중 오류가 발생했습니다"
        )


@router.get("/audit/statistics", response_model=AuditStatisticsResponse)
async def get_audit_statistics(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """감사 통계 조회"""
    try:
        audit_service = AuditService(db)
        
        # 날짜 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        stats = await audit_service.get_audit_statistics(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return AuditStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"감사 통계 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="감사 통계 조회 중 오류가 발생했습니다"
        )


# 컴플라이언스 관련 엔드포인트
@router.post("/compliance/kyc", response_model=ComplianceCheckResponse)
async def perform_kyc_check(
    request: KYCCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """KYC 체크 수행"""
    try:
        audit_service = AuditService(db)
        compliance_service = ComplianceService(db, audit_service)
        
        kyc_data = {
            "kyc_level": request.kyc_level,
            "documents": request.documents,
            "method": request.method
        }
        
        compliance_check = await compliance_service.perform_kyc_check(
            user_id=request.user_id,
            kyc_data=kyc_data
        )
        
        if not compliance_check:
            raise HTTPException(
                status_code=500,
                detail="KYC 체크 수행 중 오류가 발생했습니다"
            )
        
        return ComplianceCheckResponse.from_orm(compliance_check)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"KYC 체크 수행 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="KYC 체크 수행 중 오류가 발생했습니다"
        )


@router.post("/compliance/aml", response_model=ComplianceCheckResponse)
async def perform_aml_check(
    request: AMLCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """AML 체크 수행"""
    try:
        audit_service = AuditService(db)
        compliance_service = ComplianceService(db, audit_service)
        
        transaction_data = {
            "amount": request.amount,
            "currency": request.currency,
            "from_address": request.from_address,
            "to_address": request.to_address,
            "transaction_type": request.transaction_type,
            "user_id": request.user_id,
            "partner_id": request.partner_id
        }
        
        compliance_check = await compliance_service.perform_aml_check(
            transaction_id=request.transaction_id,
            transaction_data=transaction_data
        )
        
        if not compliance_check:
            raise HTTPException(
                status_code=500,
                detail="AML 체크 수행 중 오류가 발생했습니다"
            )
        
        return ComplianceCheckResponse.from_orm(compliance_check)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AML 체크 수행 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="AML 체크 수행 중 오류가 발생했습니다"
        )


@router.post("/compliance/sanctions", response_model=ComplianceCheckResponse)
async def perform_sanctions_check(
    request: SanctionsCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """제재 목록 체크 수행"""
    try:
        audit_service = AuditService(db)
        compliance_service = ComplianceService(db, audit_service)
        
        compliance_check = await compliance_service.perform_sanctions_check(
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            entity_data=request.entity_data
        )
        
        if not compliance_check:
            raise HTTPException(
                status_code=500,
                detail="제재 목록 체크 수행 중 오류가 발생했습니다"
            )
        
        return ComplianceCheckResponse.from_orm(compliance_check)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"제재 목록 체크 수행 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="제재 목록 체크 수행 중 오류가 발생했습니다"
        )


@router.get("/compliance/checks")
async def get_compliance_checks(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(100, ge=1, le=1000, description="페이지 크기"),
    check_type: Optional[str] = Query(None, description="체크 타입"),
    entity_type: Optional[str] = Query(None, description="엔티티 타입"),
    entity_id: Optional[str] = Query(None, description="엔티티 ID"),
    status: Optional[str] = Query(None, description="상태"),
    risk_level: Optional[str] = Query(None, description="위험도"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """컴플라이언스 체크 조회"""
    try:
        audit_service = AuditService(db)
        compliance_service = ComplianceService(db, audit_service)
        
        # 열거형 변환
        check_type_enum = None
        if check_type:
            try:
                check_type_enum = ComplianceCheckType(check_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 체크 타입: {check_type}"
                )
        
        status_enum = None
        if status:
            try:
                status_enum = ComplianceStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 상태: {status}"
                )
        
        risk_level_enum = None
        if risk_level:
            try:
                risk_level_enum = RiskLevel(risk_level)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 위험도: {risk_level}"
                )
        
        # 날짜 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # 오프셋 계산
        offset = (page - 1) * size
        
        # 체크 조회
        checks = await compliance_service.get_compliance_checks(
            limit=size,
            offset=offset,
            check_type=check_type_enum,
            entity_type=entity_type,
            entity_id=entity_id,
            status=status_enum,
            risk_level=risk_level_enum,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return {
            "checks": [ComplianceCheckResponse.from_orm(check) for check in checks],
            "page": page,
            "size": size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"컴플라이언스 체크 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="컴플라이언스 체크 조회 중 오류가 발생했습니다"
        )


@router.get("/compliance/statistics", response_model=ComplianceStatisticsResponse)
async def get_compliance_statistics(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """컴플라이언스 통계 조회"""
    try:
        audit_service = AuditService(db)
        compliance_service = ComplianceService(db, audit_service)
        
        # 날짜 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        stats = await compliance_service.get_compliance_statistics(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return ComplianceStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"컴플라이언스 통계 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="컴플라이언스 통계 조회 중 오류가 발생했습니다"
        )


# ML 이상 탐지 관련 엔드포인트
@router.get("/suspicious-activities")
async def get_suspicious_activities(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(100, ge=1, le=1000, description="페이지 크기"),
    user_id: Optional[int] = Query(None, description="사용자 ID"),
    detection_type: Optional[str] = Query(None, description="탐지 타입"),
    severity: Optional[str] = Query(None, description="심각도"),
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    resolved: Optional[bool] = Query(None, description="해결 여부"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """의심스러운 활동 조회"""
    try:
        audit_service = AuditService(db)
        ml_service = MLAnomalyDetectionService(db, audit_service)
        
        # 심각도 변환
        severity_enum = None
        if severity:
            try:
                severity_enum = RiskLevel(severity)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"유효하지 않은 심각도: {severity}"
                )
        
        # 날짜 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # 오프셋 계산
        offset = (page - 1) * size
        
        # 활동 조회
        activities = await ml_service.get_suspicious_activities(
            limit=size,
            offset=offset,
            user_id=user_id,
            detection_type=detection_type,
            severity=severity_enum,
            start_date=start_datetime,
            end_date=end_datetime,
            resolved=resolved
        )
        
        return {
            "activities": [SuspiciousActivityResponse.from_orm(activity) for activity in activities],
            "page": page,
            "size": size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"의심스러운 활동 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="의심스러운 활동 조회 중 오류가 발생했습니다"
        )


@router.post("/suspicious-activities/{activity_id}/resolve")
async def resolve_suspicious_activity(
    activity_id: int,
    request: ResolveSuspiciousActivityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """의심스러운 활동 해결"""
    try:
        audit_service = AuditService(db)
        ml_service = MLAnomalyDetectionService(db, audit_service)
        
        success = await ml_service.resolve_suspicious_activity(
            activity_id=activity_id,
            resolver_user_id=safe_int(current_user.id, 0),
            resolution_notes=request.resolution_notes,
            action_taken=request.action_taken
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="의심스러운 활동을 찾을 수 없거나 해결할 수 없습니다"
            )
        
        return {"message": "의심스러운 활동이 성공적으로 해결되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"의심스러운 활동 해결 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="의심스러운 활동 해결 중 오류가 발생했습니다"
        )


@router.get("/detection/statistics", response_model=DetectionStatisticsResponse)
async def get_detection_statistics(
    start_date: Optional[date] = Query(None, description="시작 날짜"),
    end_date: Optional[date] = Query(None, description="종료 날짜"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """탐지 통계 조회"""
    try:
        audit_service = AuditService(db)
        ml_service = MLAnomalyDetectionService(db, audit_service)
        
        # 날짜 변환
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        stats = await ml_service.get_detection_statistics(
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        return DetectionStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"탐지 통계 조회 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="탐지 통계 조회 중 오류가 발생했습니다"
        )
