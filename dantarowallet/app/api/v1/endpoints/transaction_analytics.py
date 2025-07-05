"""
트랜잭션 분석 및 모니터링 API 엔드포인트
"""
from datetime import datetime
from typing import List, Optional

from app.api.deps import get_current_admin_user, get_current_user, get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.schemas.transaction_analytics import (
    AlertRequest,
    AlertResponse,
    RealTimeTransactionMetrics,
    SuspiciousPatternAlert,
    TransactionAnalyticsFilter,
    TransactionAnalyticsResponse,
    TransactionMonitoringConfig,
    TransactionTrendAnalysis,
    UserTransactionProfile,
)
from app.services.transaction_analytics_service import TransactionAnalyticsService
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
analytics_service = TransactionAnalyticsService()


# 메인 분석 엔드포인트
@router.get("/analytics", response_model=TransactionAnalyticsResponse)
async def get_analytics(
    start_date: Optional[datetime] = Query(None, description="분석 시작 날짜"),
    end_date: Optional[datetime] = Query(None, description="분석 종료 날짜"),
    user_id: Optional[int] = Query(None, description="특정 사용자 ID (관리자만)"),
    asset: Optional[str] = Query(None, description="자산 타입 (TRX, USDT 등)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """트랜잭션 분석 데이터 조회"""
    try:
        # 일반 사용자는 자신의 거래만 조회 가능
        if not current_user.is_admin and user_id and user_id != current_user.id:  # type: ignore
            raise HTTPException(status_code=403, detail="다른 사용자의 분석 데이터에 접근할 수 없습니다")

        # 일반 사용자인 경우 자동으로 자신의 ID 설정
        if not current_user.is_admin:  # type: ignore
            user_id = current_user.id  # type: ignore

        filters = TransactionAnalyticsFilter(
            start_date=start_date, end_date=end_date, user_id=user_id, asset=asset
        )

        return await analytics_service.get_transaction_analytics(db, filters)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 데이터 조회 실패: {str(e)}")


@router.get("/profile/{user_id}", response_model=UserTransactionProfile)
async def get_user_transaction_profile(
    user_id: int = Path(..., description="사용자 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    사용자 거래 프로필 조회
    """
    # 권한 확인을 try-catch 밖에서 먼저 수행
    if not current_user.is_admin and user_id != current_user.id:  # type: ignore
        raise HTTPException(status_code=403, detail="다른 사용자의 프로필에 접근할 수 없습니다")

    try:
        return await analytics_service.get_user_transaction_profile(db, user_id)

    except NotFoundError:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"프로필 조회 실패: {str(e)}")


@router.get("/trends", response_model=TransactionTrendAnalysis)
async def get_transaction_trends(
    period: str = Query("7d", description="분석 기간 (1d, 7d, 30d, 90d)"),
    asset: Optional[str] = Query(None, description="자산 타입"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    트랜잭션 트렌드 분석 (관리자만)
    """
    try:
        return await analytics_service.get_transaction_trends(db, period, asset)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트렌드 분석 실패: {str(e)}")


@router.get("/suspicious-patterns", response_model=List[SuspiciousPatternAlert])
async def detect_suspicious_patterns(
    severity: Optional[str] = Query(
        None, description="심각도 필터 (low, medium, high, critical)"
    ),
    limit: int = Query(50, description="최대 결과 수"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    의심스러운 거래 패턴 탐지 (관리자만)
    """
    try:
        return await analytics_service.detect_suspicious_patterns(
            db, None, limit
        )  # severity를 None으로 전달

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"패턴 탐지 실패: {str(e)}")


# 실시간 메트릭 (누락된 엔드포인트)
@router.get("/real-time-metrics", response_model=RealTimeTransactionMetrics)
async def get_real_time_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """실시간 트랜잭션 메트릭 조회 (관리자만)"""
    try:
        return await analytics_service.get_real_time_metrics(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"실시간 메트릭 조회 실패: {str(e)}")


# 알림 관련 엔드포인트
@router.post("/alerts", response_model=AlertResponse)
async def create_alert(
    alert_request: AlertRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    새로운 알림 생성 (관리자만)
    """
    try:
        return await analytics_service.create_alert(db, alert_request)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 생성 실패: {str(e)}")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    user_id: Optional[int] = Query(None, description="사용자 ID 필터"),
    alert_type: Optional[str] = Query(None, description="알림 타입 필터"),
    level: Optional[str] = Query(None, description="알림 레벨 필터"),
    is_resolved: Optional[bool] = Query(None, description="해결 상태 필터"),
    limit: int = Query(50, description="최대 결과 수"),
    offset: int = Query(0, description="결과 오프셋"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    알림 목록 조회

    - 일반 사용자: 자신의 알림만 조회 가능
    - 관리자: 모든 알림 조회 가능
    """
    try:
        # 일반 사용자는 자신의 알림만 조회 가능
        if not current_user.is_admin:  # type: ignore
            user_id = current_user.id  # type: ignore

        return await analytics_service.get_alerts(
            db, user_id, alert_type, level, is_resolved, limit, offset
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int = Path(..., description="알림 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    특정 알림 상세 조회
    """
    try:
        alert = await analytics_service.get_alert_by_id(db, alert_id)

        # 권한 확인 (일반 사용자는 자신의 알림만 조회 가능)
        if not current_user.is_admin and alert.user_id != current_user.id:  # type: ignore
            raise HTTPException(status_code=403, detail="이 알림에 접근할 권한이 없습니다")

        return alert

    except NotFoundError:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 조회 실패: {str(e)}")


@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int = Path(..., description="알림 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    알림 해결 처리 (관리자만)
    """
    try:
        await analytics_service.resolve_alert(db, alert_id, current_user.id)  # type: ignore
        return {"message": "알림이 해결되었습니다"}

    except NotFoundError:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"알림 해결 실패: {str(e)}")


# 통계 엔드포인트들 (누락된 부분)
@router.get("/stats/daily")
async def get_daily_stats(
    date: Optional[datetime] = Query(None, description="특정 날짜 (기본값: 오늘)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """일별 거래 통계 조회 (관리자만)"""
    try:
        if not date:
            from datetime import datetime

            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        return await analytics_service.get_daily_stats(db, date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일별 통계 조회 실패: {str(e)}")


@router.get("/stats/summary")
async def get_stats_summary(
    period: str = Query("30d", description="기간 (7d, 30d, 90d)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """기간별 통계 요약 조회 (관리자만)"""
    try:
        return await analytics_service.get_stats_summary(db, period)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 요약 조회 실패: {str(e)}")


# 모니터링 설정 엔드포인트들 (누락된 부분)
@router.get("/monitoring/config", response_model=TransactionMonitoringConfig)
async def get_monitoring_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """모니터링 설정 조회 (관리자만)"""
    try:
        return await analytics_service.get_monitoring_config(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모니터링 설정 조회 실패: {str(e)}")


@router.put("/monitoring/config")
async def update_monitoring_config(
    config: TransactionMonitoringConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """모니터링 설정 업데이트 (관리자만)"""
    try:
        return await analytics_service.update_monitoring_config(db, config)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모니터링 설정 업데이트 실패: {str(e)}")
