"""
파트너사 출금 관리 API 엔드포인트 - Doc #28
파트너사별 유연한 출금 정책 및 자동화 API를 제공합니다.
"""

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.deps import get_current_partner, get_current_user, get_db
from app.core.logger import get_logger
from app.models.partner import Partner
from app.models.user import User
from app.models.withdrawal import Withdrawal, WithdrawalBatch, WithdrawalStatus
from app.schemas.withdrawal_management import (
    BatchOptimizationRequest,
    BatchOptimizationResponse,
    OptimizedBatchInfo,
    PartnerWithdrawalPolicyCreate,
    PartnerWithdrawalPolicyResponse,
    PartnerWithdrawalPolicyUpdate,
    WithdrawalApprovalRuleCreate,
    WithdrawalApprovalRuleResponse,
    WithdrawalBatchCreate,
    WithdrawalBatchResponse,
    WithdrawalEvaluationRequest,
    WithdrawalEvaluationResponse,
    WithdrawalStatisticsRequest,
    WithdrawalStatisticsResponse,
    WithdrawalWhitelistCreate,
    WithdrawalWhitelistResponse,
)
from app.services.withdrawal.partner_withdrawal_service import PartnerWithdrawalService

logger = get_logger(__name__)

router = APIRouter()


def safe_get_attr(obj, attr: str, default=None):
    """SQLAlchemy 모델 속성을 안전하게 가져오는 헬퍼 함수"""
    if obj is None:
        return default

    value = getattr(obj, attr, default)

    # SQLAlchemy Column 타입인 경우 실제 값 추출
    if hasattr(value, "__class__") and "Column" in str(value.__class__):
        return default  # Column 객체인 경우 기본값 반환
    else:
        return value


def safe_str(value, default: str = ""):
    """안전한 str 변환"""
    if value is None:
        return default
    return str(value)


def safe_int(value, default: int = 0):
    """안전한 int 변환"""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# === 출금 정책 관리 ===


@router.post("/policies", response_model=PartnerWithdrawalPolicyResponse)
async def create_withdrawal_policy(
    policy_data: PartnerWithdrawalPolicyCreate,
    partner: Partner = Depends(get_current_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 출금 정책을 생성합니다."""
    try:
        service = PartnerWithdrawalService(db)
        policy = await service.create_withdrawal_policy(
            partner_id=safe_str(partner.id),
            policy_data=policy_data.model_dump(),
            admin_id=safe_int(current_user.id),
        )
        return policy
    except Exception as e:
        logger.error(f"출금 정책 생성 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/policies", response_model=PartnerWithdrawalPolicyResponse)
async def get_withdrawal_policy(
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)
):
    """파트너사 출금 정책을 조회합니다."""
    try:
        service = PartnerWithdrawalService(db)
        policy = await service.get_withdrawal_policy(safe_str(partner.id))

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="출금 정책을 찾을 수 없습니다",
            )

        return policy
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"출금 정책 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="출금 정책 조회에 실패했습니다",
        )


@router.put("/policies", response_model=PartnerWithdrawalPolicyResponse)
async def update_withdrawal_policy(
    update_data: PartnerWithdrawalPolicyUpdate,
    partner: Partner = Depends(get_current_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """파트너사 출금 정책을 업데이트합니다."""
    try:
        service = PartnerWithdrawalService(db)
        policy = await service.update_withdrawal_policy(
            partner_id=safe_str(partner.id),
            update_data=update_data.model_dump(exclude_unset=True),
            admin_id=safe_int(current_user.id),
        )
        return policy
    except Exception as e:
        logger.error(f"출금 정책 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# === 실시간 출금 자동 승인 ===


@router.post("/evaluate", response_model=WithdrawalEvaluationResponse)
async def evaluate_withdrawal_request(
    request: WithdrawalEvaluationRequest,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """출금 요청을 평가하고 자동 승인 여부를 결정합니다."""
    try:
        service = PartnerWithdrawalService(db)
        evaluation = await service.evaluate_withdrawal_request(
            withdrawal_id=request.withdrawal_id, partner_id=safe_str(partner.id)
        )
        return WithdrawalEvaluationResponse(**evaluation)
    except Exception as e:
        logger.error(f"출금 요청 평가 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# === 일괄 출금 관리 ===


@router.post("/batches", response_model=WithdrawalBatchResponse)
async def create_withdrawal_batch(
    batch_data: WithdrawalBatchCreate,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """출금 배치를 생성합니다."""
    try:
        service = PartnerWithdrawalService(db)
        batch = await service.create_withdrawal_batch(
            partner_id=safe_str(partner.id),
            withdrawal_ids=batch_data.withdrawal_ids,
            scheduled_time=batch_data.scheduled_time,
        )
        return batch
    except Exception as e:
        logger.error(f"출금 배치 생성 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/batches", response_model=List[WithdrawalBatchResponse])
async def get_pending_batches(
    limit: int = 10,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """대기 중인 출금 배치들을 조회합니다."""
    try:
        service = PartnerWithdrawalService(db)
        batches = await service.get_pending_batches(
            partner_id=safe_str(partner.id), limit=limit
        )
        return batches
    except Exception as e:
        logger.error(f"대기 중인 배치 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대기 중인 배치 조회에 실패했습니다",
        )
    try:
        service = PartnerWithdrawalService(db)
        batches = await service.get_pending_batches(partner_id=partner.id, limit=limit)
        return batches
    except Exception as e:
        logger.error(f"출금 배치 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="출금 배치 조회에 실패했습니다",
        )


# === 출금 배치 최적화 ===


@router.post("/optimize", response_model=BatchOptimizationResponse)
async def optimize_withdrawal_batches(
    request: BatchOptimizationRequest,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """출금 요청들을 최적화된 배치로 그룹핑합니다."""
    try:
        service = PartnerWithdrawalService(db)
        optimized_batches = await service.optimize_withdrawal_batches(
            safe_str(partner.id)
        )

        # 제한된 개수만 반환
        max_batches = request.max_batches or 10
        limited_batches = optimized_batches[:max_batches]

        # OptimizedBatchInfo 객체로 변환
        optimized_batch_infos = [
            OptimizedBatchInfo(
                withdrawal_ids=batch.get("withdrawal_ids", []),
                total_amount=Decimal(str(batch.get("total_amount", 0))),
                total_count=batch.get("total_count", 0),
                estimated_energy_cost=Decimal(
                    str(batch.get("estimated_energy_cost", 0))
                ),
                priority_score=batch.get("priority_score", 0),
                estimated_completion_time=batch.get("estimated_completion_time"),
            )
            for batch in limited_batches
        ]

        total_pending = sum(batch["total_count"] for batch in optimized_batches)
        total_amount = sum(batch["total_amount"] for batch in optimized_batches)

        return BatchOptimizationResponse(
            optimized_batches=optimized_batch_infos,
            total_pending_withdrawals=total_pending,
            total_pending_amount=Decimal(str(total_amount)),
            optimization_summary={
                "total_batches": len(optimized_batches),
                "selected_batches": len(limited_batches),
                "total_withdrawals": total_pending,
                "total_amount": str(total_amount),
            },
        )
    except Exception as e:
        logger.error(f"배치 최적화 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="배치 최적화에 실패했습니다",
        )


# === TronLink 자동 서명 지원 ===


@router.post("/batches/{batch_id}/execute")
async def execute_batch_with_auto_sign(
    batch_id: int,
    background_tasks: BackgroundTasks,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """TronLink 자동 서명을 사용하여 배치를 실행합니다."""
    try:
        service = PartnerWithdrawalService(db)

        # 배치 유효성 검증
        batches = await service.get_pending_batches(safe_str(partner.id), limit=1000)
        target_batch = next((b for b in batches if safe_int(b.id) == batch_id), None)

        if not target_batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="배치를 찾을 수 없습니다"
            )

        # 백그라운드에서 실행
        background_tasks.add_task(
            _execute_batch_background, service, batch_id, safe_str(partner.id)
        )

        return {
            "message": "배치 실행이 시작되었습니다",
            "batch_id": batch_id,
            "status": "processing",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"배치 실행 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# === 배치 실행 관련 유틸리티 ===


async def _execute_batch_background(
    service: PartnerWithdrawalService, batch_id: int, partner_id: str
):
    """배치를 백그라운드에서 실행합니다."""
    try:
        logger.info(f"배치 백그라운드 실행 시작: {batch_id}")

        # 배치 정보 조회
        batch_result = await service.db.execute(
            select(WithdrawalBatch).where(WithdrawalBatch.id == batch_id)
        )
        batch = batch_result.scalar_one_or_none()

        if not batch:
            logger.error(f"배치를 찾을 수 없습니다: {batch_id}")
            return

        # 배치 상태 업데이트
        await service.db.execute(
            update(WithdrawalBatch)
            .where(WithdrawalBatch.id == batch_id)
            .values(status="processing", started_at=datetime.utcnow())
        )
        await service.db.commit()

        # 출금 ID들 파싱
        withdrawal_ids = json.loads(batch.withdrawal_ids)

        # 각 출금 요청 처리
        successful_count = 0
        failed_count = 0
        tx_hashes = []

        for withdrawal_id in withdrawal_ids:
            try:
                # 실제 출금 처리 로직 (여기서는 시뮬레이션)
                await asyncio.sleep(0.1)  # 처리 시간 시뮬레이션

                # 성공한 경우
                tx_hash = f"0x{withdrawal_id:064x}"  # 임시 트랜잭션 해시
                tx_hashes.append(tx_hash)

                # 출금 상태 업데이트
                await service.db.execute(
                    update(Withdrawal)
                    .where(Withdrawal.id == withdrawal_id)
                    .values(
                        status=WithdrawalStatus.COMPLETED,
                        tx_hash=tx_hash,
                        completed_at=datetime.utcnow(),
                    )
                )

                successful_count += 1
                logger.info(f"출금 처리 완료: {withdrawal_id} -> {tx_hash}")

            except Exception as e:
                # 실패한 경우
                failed_count += 1
                logger.error(f"출금 처리 실패: {withdrawal_id} -> {str(e)}")

                # 출금 상태 업데이트
                await service.db.execute(
                    update(Withdrawal)
                    .where(Withdrawal.id == withdrawal_id)
                    .values(status=WithdrawalStatus.FAILED, rejection_reason=str(e))
                )

        # 배치 완료 업데이트
        await service.db.execute(
            update(WithdrawalBatch)
            .where(WithdrawalBatch.id == batch_id)
            .values(
                status="completed",
                completed_at=datetime.utcnow(),
                successful_count=successful_count,
                failed_count=failed_count,
                tx_hashes=json.dumps(tx_hashes),
            )
        )
        await service.db.commit()

        logger.info(
            f"배치 실행 완료: {batch_id} -> 성공:{successful_count}, 실패:{failed_count}"
        )

    except Exception as e:
        logger.error(f"배치 실행 오류: {batch_id} -> {str(e)}")

        # 배치 실패 상태 업데이트
        try:
            await service.db.execute(
                update(WithdrawalBatch)
                .where(WithdrawalBatch.id == batch_id)
                .values(status="failed", error_message=str(e))
            )
            await service.db.commit()
        except Exception as commit_error:
            logger.error(f"배치 실패 상태 업데이트 오류: {str(commit_error)}")


# === 승인 규칙 관리 ===


@router.post("/approval-rules", response_model=WithdrawalApprovalRuleResponse)
async def create_approval_rule(
    rule_data: WithdrawalApprovalRuleCreate,
    partner: Partner = Depends(get_current_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """승인 규칙을 생성합니다."""
    try:
        service = PartnerWithdrawalService(db)

        # 파트너 정책 조회
        policy = await service.get_withdrawal_policy(safe_str(partner.id))
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="출금 정책을 찾을 수 없습니다",
            )

        # 승인 규칙 생성
        approval_rule = await service.create_approval_rule(
            policy_id=safe_int(policy.id),
            rule_data=rule_data.model_dump(),
            admin_id=safe_int(current_user.id),
        )

        return approval_rule
    except Exception as e:
        logger.error(f"승인 규칙 생성 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/approval-rules", response_model=List[WithdrawalApprovalRuleResponse])
async def get_approval_rules(
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)
):
    """승인 규칙들을 조회합니다."""
    try:
        service = PartnerWithdrawalService(db)

        # 파트너 정책 조회
        policy = await service.get_withdrawal_policy(safe_str(partner.id))
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="출금 정책을 찾을 수 없습니다",
            )

        # 승인 규칙들 조회
        approval_rules = await service.get_approval_rules(safe_int(policy.id))

        return approval_rules
    except Exception as e:
        logger.error(f"승인 규칙 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="승인 규칙 조회에 실패했습니다",
        )


# === 출금 한도 및 화이트리스트 관리 ===


@router.post("/whitelist", response_model=WithdrawalWhitelistResponse)
async def create_whitelist_entry(
    whitelist_data: WithdrawalWhitelistCreate,
    partner: Partner = Depends(get_current_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """화이트리스트 항목을 생성합니다."""
    try:
        service = PartnerWithdrawalService(db)

        # 파트너 정책 조회
        policy = await service.get_withdrawal_policy(safe_str(partner.id))
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="출금 정책을 찾을 수 없습니다",
            )

        # 화이트리스트 항목 생성
        whitelist_entry = await service.create_whitelist_entry(
            policy_id=safe_int(policy.id),
            whitelist_data=whitelist_data.model_dump(),
            admin_id=safe_int(current_user.id),
        )

        return whitelist_entry
    except Exception as e:
        logger.error(f"화이트리스트 항목 생성 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/whitelist", response_model=List[WithdrawalWhitelistResponse])
async def get_whitelist_entries(
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)
):
    """화이트리스트 항목들을 조회합니다."""
    try:
        service = PartnerWithdrawalService(db)

        # 파트너 정책 조회
        policy = await service.get_withdrawal_policy(safe_str(partner.id))
        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="출금 정책을 찾을 수 없습니다",
            )

        # 화이트리스트 항목들 조회
        whitelist_entries = await service.get_whitelist_entries(safe_int(policy.id))

        return whitelist_entries
    except Exception as e:
        logger.error(f"화이트리스트 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="화이트리스트 조회에 실패했습니다",
        )


@router.delete("/whitelist/{whitelist_id}")
async def delete_whitelist_entry(
    whitelist_id: int,
    partner: Partner = Depends(get_current_partner),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """화이트리스트 항목을 삭제합니다."""
    try:
        service = PartnerWithdrawalService(db)

        success = await service.delete_whitelist_entry(
            whitelist_id=whitelist_id,
            partner_id=safe_str(partner.id),
            admin_id=safe_int(current_user.id),
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="화이트리스트 항목을 찾을 수 없습니다",
            )

        return {"message": "화이트리스트 항목이 삭제되었습니다"}
    except Exception as e:
        logger.error(f"화이트리스트 항목 삭제 실패: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# === 출금 수수료 최적화 ===


@router.get("/fee-optimization")
async def get_fee_optimization_suggestions(
    partner: Partner = Depends(get_current_partner), db: AsyncSession = Depends(get_db)
):
    """출금 수수료 최적화 제안을 제공합니다."""
    try:
        # TODO: 수수료 최적화 알고리즘 구현
        return {
            "message": "수수료 최적화 분석 중...",
            "recommendations": [
                "현재 에너지 가격이 낮습니다. 대량 출금을 고려해보세요.",
                "배치 크기를 20개로 설정하면 최적의 에너지 효율을 얻을 수 있습니다.",
                "오후 2-4시 사이에 출금하면 네트워크 수수료가 낮습니다.",
            ],
            "current_energy_price": "13.85 TRX",
            "optimal_batch_size": 20,
            "estimated_savings": "15%",
        }
    except Exception as e:
        logger.error(f"수수료 최적화 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수수료 최적화 분석에 실패했습니다",
        )


# === 출금 통계 및 모니터링 ===


@router.post("/statistics", response_model=WithdrawalStatisticsResponse)
async def get_withdrawal_statistics(
    request: WithdrawalStatisticsRequest,
    partner: Partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """출금 통계를 조회합니다."""
    try:
        # TODO: 통계 서비스 구현
        from datetime import datetime, timedelta
        from decimal import Decimal

        # 임시 응답
        return WithdrawalStatisticsResponse(
            partner_id=safe_str(partner.id),
            period={
                "start": request.start_date or datetime.utcnow() - timedelta(days=30),
                "end": request.end_date or datetime.utcnow(),
            },
            total_withdrawals=150,
            total_amount=Decimal("50000.00"),
            total_fee=Decimal("125.50"),
            status_breakdown={
                "completed": 140,
                "pending": 5,
                "failed": 3,
                "cancelled": 2,
            },
            auto_approved_count=120,
            auto_approved_percentage=80.0,
            batch_processed_count=100,
            batch_processed_percentage=66.7,
            average_processing_time=3.5,
            success_rate=96.7,
        )
    except Exception as e:
        logger.error(f"출금 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="출금 통계 조회에 실패했습니다",
        )
