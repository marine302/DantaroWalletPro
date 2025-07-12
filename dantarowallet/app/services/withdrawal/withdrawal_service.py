"""
파트너사 출금 관리 고도화 서비스 - Doc #28
실시간 출금 자동 승인 규칙 엔진, 일괄 출금 스케줄 관리, 출금 요청 그룹핑 및 배치 최적화를 제공합니다.
"""
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.sql import func

from app.models.withdrawal import Withdrawal, WithdrawalStatus
from app.models.withdrawal_policy import PartnerWithdrawalPolicy, WithdrawalPolicyType, ApprovalRuleType
from app.models.partner import Partner
from app.core.logging import get_logger
from app.core.database import get_db_session

logger = get_logger(__name__)

def safe_decimal_assign(obj, attr: str, value: Decimal):
    """SQLAlchemy 컬럼에 Decimal 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_str_assign(obj, attr: str, value: str):
    """SQLAlchemy 컬럼에 문자열 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_int_assign(obj, attr: str, value: int):
    """SQLAlchemy 컬럼에 정수 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_datetime_assign(obj, attr: str, value: datetime):
    """SQLAlchemy 컬럼에 datetime 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_bool_assign(obj, attr: str, value: bool):
    """SQLAlchemy 컬럼에 bool 값을 안전하게 할당"""
    setattr(obj, attr, value)


class WithdrawalService:
    """파트너사 출금 관리 고도화 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)
    
    async def create_withdrawal_request(
        self, 
        partner_id: str, 
        amount: Decimal, 
        destination_address: str,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """출금 요청 생성 - 자동 승인 규칙 엔진 적용"""
        try:
            # 파트너 정책 조회
            policy = self.db.query(PartnerWithdrawalPolicy).filter(
                PartnerWithdrawalPolicy.partner_id == partner_id
            ).first()
            
            if not policy:
                raise ValueError(f"파트너 {partner_id}의 출금 정책을 찾을 수 없습니다")
            
            # 출금 요청 생성
            withdrawal = Withdrawal()
            safe_str_assign(withdrawal, "partner_id", partner_id)
            safe_decimal_assign(withdrawal, "amount", amount)
            safe_str_assign(withdrawal, "destination_address", destination_address)
            safe_str_assign(withdrawal, "priority", priority)
            safe_datetime_assign(withdrawal, "created_at", datetime.utcnow())
            
            # 자동 승인 규칙 검증
            approval_result = await self._check_auto_approval_rules(policy, withdrawal)
            safe_str_assign(withdrawal, "status", approval_result["status"])
            
            if approval_result["auto_approved"]:
                safe_datetime_assign(withdrawal, "approved_at", datetime.utcnow())
                safe_str_assign(withdrawal, "approval_type", "auto")
            
            self.db.add(withdrawal)
            self.db.commit()
            
            # 실시간 처리 또는 배치 처리 결정
            policy_type = getattr(policy, "policy_type", None)
            batch_enabled = getattr(policy, "batch_enabled", False)
            
            if approval_result["auto_approved"] and policy_type == WithdrawalPolicyType.REALTIME:
                await self._process_realtime_withdrawal(withdrawal)
            elif batch_enabled:
                await self._add_to_batch_queue(withdrawal)
            
            return {
                "withdrawal_id": withdrawal.id,
                "status": getattr(withdrawal, "status"),
                "auto_approved": approval_result["auto_approved"],
                "processing_type": "realtime" if approval_result["auto_approved"] else "batch",
                "estimated_execution": approval_result.get("estimated_execution")
            }
            
        except Exception as e:
            self.logger.error(f"출금 요청 생성 실패: {str(e)}")
            self.db.rollback()
            raise
    
    async def _check_auto_approval_rules(
        self, 
        policy: PartnerWithdrawalPolicy, 
        withdrawal: Withdrawal
    ) -> Dict[str, Any]:
        """자동 승인 규칙 엔진"""
        try:
            amount = getattr(withdrawal, "amount", Decimal("0"))
            partner_id = getattr(withdrawal, "partner_id", "")
            destination = getattr(withdrawal, "destination_address", "")
            
            # 기본 결과
            result = {
                "auto_approved": False,
                "status": WithdrawalStatus.PENDING.value,
                "reasons": []
            }
            
            # 자동 승인이 비활성화된 경우
            if not getattr(policy, "auto_approve_enabled", False):
                result["reasons"].append("자동 승인이 비활성화됨")
                return result
            
            # 금액 제한 검증
            auto_approve_max = getattr(policy, "auto_approve_max_amount", None)
            if auto_approve_max and amount > auto_approve_max:
                result["reasons"].append(f"금액이 자동 승인 한도({auto_approve_max})를 초과")
                return result
            
            # 일일 한도 검증
            daily_limit = getattr(policy, "auto_approve_daily_limit", None)
            if daily_limit:
                today_total = await self._get_today_withdrawal_total(partner_id)
                if today_total + amount > daily_limit:
                    result["reasons"].append(f"일일 한도({daily_limit})를 초과")
                    return result
            
            # 화이트리스트 검증
            if getattr(policy, "whitelist_enabled", False):
                if not await self._is_whitelisted_address(partner_id, destination):
                    result["reasons"].append("화이트리스트에 없는 주소")
                    return result
            
            # 위험 점수 검증
            risk_threshold = getattr(policy, "risk_score_threshold", 50)
            risk_score = await self._calculate_risk_score(partner_id, amount, destination)
            if risk_score > risk_threshold:
                result["reasons"].append(f"위험 점수({risk_score})가 임계값({risk_threshold})을 초과")
                return result
            
            # 모든 검증 통과
            result["auto_approved"] = True
            result["status"] = WithdrawalStatus.APPROVED.value
            result["reasons"] = ["자동 승인 조건 만족"]
            
            return result
            
        except Exception as e:
            self.logger.error(f"자동 승인 규칙 검증 실패: {str(e)}")
            return {
                "auto_approved": False,
                "status": WithdrawalStatus.PENDING.value,
                "reasons": [f"규칙 검증 오류: {str(e)}"]
            }
    
    async def _get_today_withdrawal_total(self, partner_id: str) -> Decimal:
        """오늘 출금 총액 조회"""
        try:
            today = datetime.utcnow().date()
            total = self.db.query(func.sum(Withdrawal.amount)).filter(
                and_(
                    Withdrawal.partner_id == partner_id,
                    func.date(Withdrawal.created_at) == today,
                    Withdrawal.status.in_([WithdrawalStatus.APPROVED.value, WithdrawalStatus.COMPLETED.value])
                )
            ).scalar()
            
            return total or Decimal("0")
            
        except Exception as e:
            self.logger.error(f"오늘 출금 총액 조회 실패: {str(e)}")
            return Decimal("0")
    
    async def _is_whitelisted_address(self, partner_id: str, address: str) -> bool:
        """화이트리스트 주소 검증"""
        try:
            policy = self.db.query(PartnerWithdrawalPolicy).filter(
                PartnerWithdrawalPolicy.partner_id == partner_id
            ).first()
            
            if not policy:
                return False
            
            # 화이트리스트 주소 목록 조회 (JSON 컬럼에서)
            whitelist = getattr(policy, "whitelist_addresses", [])
            if not isinstance(whitelist, list):
                return False
            
            return address in whitelist
            
        except Exception as e:
            self.logger.error(f"화이트리스트 검증 실패: {str(e)}")
            return False
    
    async def _calculate_risk_score(self, partner_id: str, amount: Decimal, destination: str) -> int:
        """위험 점수 계산"""
        try:
            risk_score = 0
            
            # 금액 기반 위험 점수
            if amount > Decimal("10000"):
                risk_score += 30
            elif amount > Decimal("1000"):
                risk_score += 15
            
            # 새로운 주소 위험 점수
            is_new_address = await self._is_new_destination(partner_id, destination)
            if is_new_address:
                risk_score += 20
            
            # 시간대 기반 위험 점수 (업무 외 시간)
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:
                risk_score += 10
            
            return min(risk_score, 100)  # 최대 100점
            
        except Exception as e:
            self.logger.error(f"위험 점수 계산 실패: {str(e)}")
            return 100  # 오류 시 최대 위험 점수
    
    async def _is_new_destination(self, partner_id: str, destination: str) -> bool:
        """새로운 출금 주소 여부 확인"""
        try:
            count = self.db.query(Withdrawal).filter(
                and_(
                    Withdrawal.partner_id == partner_id,
                    Withdrawal.destination_address == destination,
                    Withdrawal.status == WithdrawalStatus.COMPLETED.value
                )
            ).count()
            
            return count == 0
            
        except Exception as e:
            self.logger.error(f"새로운 주소 확인 실패: {str(e)}")
            return True  # 오류 시 새로운 주소로 간주
    
    async def _process_realtime_withdrawal(self, withdrawal: Withdrawal):
        """실시간 출금 처리"""
        try:
            # 실시간 처리 로직
            safe_str_assign(withdrawal, "status", WithdrawalStatus.PROCESSING.value)
            safe_datetime_assign(withdrawal, "processing_started_at", datetime.utcnow())
            
            # TronLink 자동 서명 또는 수동 서명 요청
            partner_id = getattr(withdrawal, "partner_id", "")
            policy = self.db.query(PartnerWithdrawalPolicy).filter(
                PartnerWithdrawalPolicy.partner_id == partner_id
            ).first()
            
            if policy and getattr(policy, "auto_sign_enabled", False):
                await self._auto_sign_withdrawal(withdrawal, policy)
            else:
                await self._request_manual_signature(withdrawal)
            
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"실시간 출금 처리 실패: {str(e)}")
            safe_str_assign(withdrawal, "status", WithdrawalStatus.FAILED.value)
            self.db.commit()
    
    async def _auto_sign_withdrawal(self, withdrawal: Withdrawal, policy: PartnerWithdrawalPolicy):
        """TronLink 자동 서명 처리"""
        try:
            # 자동 서명 스크립트 실행
            script_path = getattr(policy, "auto_sign_script_path", "")
            if not script_path:
                raise ValueError("자동 서명 스크립트 경로가 설정되지 않음")
            
            # 실제 자동 서명 로직은 TronLink 연동 필요
            # 여기서는 성공으로 가정
            safe_str_assign(withdrawal, "status", WithdrawalStatus.SIGNED.value)
            safe_datetime_assign(withdrawal, "signed_at", datetime.utcnow())
            
            # 블록체인 전송 단계로 이동
            await self._execute_blockchain_transfer(withdrawal)
            
        except Exception as e:
            self.logger.error(f"자동 서명 실패: {str(e)}")
            safe_str_assign(withdrawal, "status", WithdrawalStatus.FAILED.value)
            raise
    
    async def _request_manual_signature(self, withdrawal: Withdrawal):
        """수동 서명 요청"""
        try:
            safe_str_assign(withdrawal, "status", WithdrawalStatus.PENDING_SIGNATURE.value)
            # 알림 전송 로직 추가 필요
            
        except Exception as e:
            self.logger.error(f"수동 서명 요청 실패: {str(e)}")
            raise
    
    async def _execute_blockchain_transfer(self, withdrawal: Withdrawal):
        """블록체인 전송 실행"""
        try:
            # 실제 TRON 블록체인 전송 로직
            # 여기서는 성공으로 가정
            safe_str_assign(withdrawal, "status", WithdrawalStatus.COMPLETED.value)
            safe_datetime_assign(withdrawal, "completed_at", datetime.utcnow())
            safe_str_assign(withdrawal, "transaction_hash", "mock_tx_hash")
            
        except Exception as e:
            self.logger.error(f"블록체인 전송 실패: {str(e)}")
            safe_str_assign(withdrawal, "status", WithdrawalStatus.FAILED.value)
            raise
    
    async def _add_to_batch_queue(self, withdrawal: Withdrawal):
        """배치 처리 큐에 추가"""
        try:
            safe_str_assign(withdrawal, "status", WithdrawalStatus.QUEUED.value)
            safe_datetime_assign(withdrawal, "queued_at", datetime.utcnow())
            
            # 배치 스케줄 확인 및 예상 실행 시간 계산
            partner_id = getattr(withdrawal, "partner_id", "")
            policy = self.db.query(PartnerWithdrawalPolicy).filter(
                PartnerWithdrawalPolicy.partner_id == partner_id
            ).first()
            
            if policy:
                estimated_execution = await self._calculate_next_batch_execution(policy)
                safe_datetime_assign(withdrawal, "estimated_execution_at", estimated_execution)
            
            self.db.commit()
            
        except Exception as e:
            self.logger.error(f"배치 큐 추가 실패: {str(e)}")
            raise
    
    async def _calculate_next_batch_execution(self, policy: PartnerWithdrawalPolicy) -> datetime:
        """다음 배치 실행 시간 계산"""
        try:
            execution_time = getattr(policy, "batch_execution_time", "14:00:00")
            execution_days = getattr(policy, "batch_execution_days", ["monday", "wednesday", "friday"])
            
            # 현재 시간 기준으로 다음 실행 시간 계산
            now = datetime.utcnow()
            
            # 간단한 계산 (실제로는 더 복잡한 로직 필요)
            next_execution = now + timedelta(days=1)
            next_execution = next_execution.replace(hour=14, minute=0, second=0, microsecond=0)
            
            return next_execution
            
        except Exception as e:
            self.logger.error(f"배치 실행 시간 계산 실패: {str(e)}")
            return datetime.utcnow() + timedelta(days=1)
    
    async def process_batch_withdrawals(self, partner_id: str) -> Dict[str, Any]:
        """배치 출금 처리 실행"""
        try:
            # 배치 처리 대기 중인 출금 조회
            queued_withdrawals = self.db.query(Withdrawal).filter(
                and_(
                    Withdrawal.partner_id == partner_id,
                    Withdrawal.status == WithdrawalStatus.QUEUED.value
                )
            ).order_by(asc(Withdrawal.created_at)).all()
            
            if not queued_withdrawals:
                return {"message": "처리할 배치 출금이 없습니다", "count": 0}
            
            # 배치 최적화
            optimized_batches = await self._optimize_withdrawal_batches(queued_withdrawals)
            
            results = []
            for batch in optimized_batches:
                batch_result = await self._execute_withdrawal_batch(batch)
                results.append(batch_result)
            
            return {
                "message": "배치 출금 처리 완료",
                "total_withdrawals": len(queued_withdrawals),
                "batch_count": len(optimized_batches),
                "results": results
            }
            
        except Exception as e:
            self.logger.error(f"배치 출금 처리 실패: {str(e)}")
            raise
    
    async def _optimize_withdrawal_batches(self, withdrawals: List[Withdrawal]) -> List[List[Withdrawal]]:
        """출금 배치 최적화"""
        try:
            # 간단한 배치 최적화 로직
            batches = []
            current_batch = []
            batch_size = 20  # 최적 배치 크기
            
            for withdrawal in withdrawals:
                current_batch.append(withdrawal)
                if len(current_batch) >= batch_size:
                    batches.append(current_batch)
                    current_batch = []
            
            if current_batch:
                batches.append(current_batch)
            
            return batches
            
        except Exception as e:
            self.logger.error(f"배치 최적화 실패: {str(e)}")
            return [[w] for w in withdrawals]  # 개별 처리로 폴백
    
    async def _execute_withdrawal_batch(self, batch: List[Withdrawal]) -> Dict[str, Any]:
        """배치 출금 실행"""
        try:
            batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # 배치 내 모든 출금을 처리 중 상태로 변경
            for withdrawal in batch:
                safe_str_assign(withdrawal, "status", WithdrawalStatus.PROCESSING.value)
                safe_datetime_assign(withdrawal, "processing_started_at", datetime.utcnow())
            
            self.db.commit()
            
            # 실제 배치 실행 로직
            successful_count = 0
            failed_count = 0
            
            for withdrawal in batch:
                try:
                    await self._execute_blockchain_transfer(withdrawal)
                    successful_count += 1
                except Exception as e:
                    self.logger.error(f"개별 출금 실행 실패: {str(e)}")
                    failed_count += 1
            
            return {
                "batch_id": batch_id,
                "total_count": len(batch),
                "successful_count": successful_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            self.logger.error(f"배치 실행 실패: {str(e)}")
            raise
    
    def get_withdrawal_status(self, withdrawal_id: str) -> Dict[str, Any]:
        """출금 상태 조회"""
        try:
            withdrawal = self.db.query(Withdrawal).filter(
                Withdrawal.id == withdrawal_id
            ).first()
            
            if not withdrawal:
                raise ValueError(f"출금 요청 {withdrawal_id}를 찾을 수 없습니다")
            
            return {
                "withdrawal_id": withdrawal_id,
                "status": getattr(withdrawal, "status", ""),
                "amount": float(getattr(withdrawal, "amount", 0)),
                "destination_address": getattr(withdrawal, "destination_address", ""),
                "created_at": getattr(withdrawal, "created_at", None),
                "completed_at": getattr(withdrawal, "completed_at", None),
                "transaction_hash": getattr(withdrawal, "transaction_hash", "")
            }
            
        except Exception as e:
            self.logger.error(f"출금 상태 조회 실패: {str(e)}")
            raise
    
    def get_withdrawal_history(self, partner_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """출금 내역 조회"""
        try:
            withdrawals = self.db.query(Withdrawal).filter(
                Withdrawal.partner_id == partner_id
            ).order_by(desc(Withdrawal.created_at)).limit(limit).all()
            
            return [
                {
                    "withdrawal_id": getattr(w, "id", ""),
                    "amount": float(getattr(w, "amount", 0)),
                    "status": getattr(w, "status", ""),
                    "destination_address": getattr(w, "destination_address", ""),
                    "created_at": getattr(w, "created_at", None),
                    "completed_at": getattr(w, "completed_at", None),
                    "transaction_hash": getattr(w, "transaction_hash", "")
                }
                for w in withdrawals
            ]
            
        except Exception as e:
            self.logger.error(f"출금 내역 조회 실패: {str(e)}")
            raise
