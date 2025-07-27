"""
파트너사 에너지 관리 서비스
문서 41번에 따른 파트너사 에너지 계산, 충전, 모니터링 기능
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from app.models.partner import Partner
from app.models.energy_pool import EnergyPool, EnergySourceType
from app.models.energy_allocation import EnergyAllocation
from app.core.logging import get_logger
from app.core.tron import TronService

logger = get_logger(__name__)


class PartnerEnergyService:
    """파트너사 에너지 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.tron_service = TronService()

    async def calculate_withdrawal_energy(
        self, withdrawal_requests: List[Dict], batch_mode: bool = False
    ) -> Decimal:
        """
        출금 요청에 필요한 총 에너지 계산
        USDT 전송당 약 32,000 에너지 필요 (기본값)
        """
        base_energy_per_tx = Decimal("32000")  # USDT 전송 기본 에너지
        total_energy = Decimal("0")

        if batch_mode:
            # 배치 모드: 트랜잭션 수 기반 계산
            total_energy = len(withdrawal_requests) * base_energy_per_tx
            # 배치 처리 시 10% 절약
            total_energy *= Decimal("0.9")
        else:
            # 개별 모드: 각 요청별 계산
            for request in withdrawal_requests:
                # 긴급 출금은 20% 추가 에너지 필요
                energy_multiplier = Decimal("1.2") if request.get("type") == "immediate" else Decimal("1.0")
                total_energy += base_energy_per_tx * energy_multiplier

        logger.info(f"계산된 총 에너지: {total_energy} (배치모드: {batch_mode})")
        return total_energy

    async def calculate_energy_cost(
        self, partner_id: str, energy_amount: Decimal, batch_mode: bool = False
    ) -> Dict[str, Decimal]:
        """
        에너지 비용 계산 (마진 및 SaaS 수수료 포함)
        """
        # 현재 에너지 시세 조회 (자체 스테이킹 기준)
        base_energy_price = Decimal("0.00002")  # TRX per energy
        
        # 기본 비용
        base_cost = energy_amount * base_energy_price
        
        # 마진 적용 (17.5%)
        margin_rate = Decimal("0.175")
        margin = base_cost * margin_rate
        
        # SaaS 수수료 조회
        saas_fee = await self._get_partner_saas_fee(partner_id, batch_mode)
        
        # 총 비용
        total_cost = base_cost + margin + saas_fee

        return {
            "base_cost": base_cost,
            "margin": margin,
            "saas_fee": saas_fee,
            "total_cost": total_cost,
            "energy_price": base_energy_price
        }

    async def _get_partner_saas_fee(self, partner_id: str, batch_mode: bool = False) -> Decimal:
        """파트너사별 SaaS 수수료 조회"""
        # 실제로는 DB에서 파트너사별 설정을 조회
        # 기본값: 건당 1 TRX
        base_fee = Decimal("1.0")
        
        if batch_mode:
            # 배치 모드 시 최소 수수료 적용 (5 TRX)
            return max(base_fee, Decimal("5.0"))
        
        return base_fee

    async def calculate_fallback_burn_cost(self, withdrawal_requests: List[Dict]) -> Decimal:
        """
        폴백 TRX 소각량 계산
        에너지 공급 실패 시 파트너사 직접 처리용
        """
        # USDT 전송 시 필요한 TRX 소각량 (약 13.2 TRX per 100 USDT)
        base_burn_per_100_usdt = Decimal("13.2")
        
        total_burn = Decimal("0")
        for request in withdrawal_requests:
            amount = Decimal(str(request.get("amount", 0)))
            burn_amount = (amount / 100) * base_burn_per_100_usdt
            total_burn += burn_amount

        return total_burn

    async def verify_trx_payment(
        self, partner_id: str, trx_amount: Decimal, tx_hash: str, reference_id: str
    ) -> bool:
        """
        TRX 송금 확인
        실제로는 트론 네트워크에서 트랜잭션 확인
        """
        try:
            # TODO: 실제 트론 네트워크 연동 구현
            # tx_info = await self.tron_service.get_transaction_info(tx_hash)
            
            # 현재는 더미 검증 (tx_hash 길이만 확인)
            if len(tx_hash) != 64:
                logger.error(f"잘못된 트랜잭션 해시 형식: {tx_hash}")
                return False
                
            # 송금 확인 기록
            logger.info(f"TRX 송금 확인 완료: {partner_id} -> {trx_amount} TRX")
            return True
            
        except Exception as e:
            logger.error(f"TRX 송금 확인 실패: {e}")
            return False

    async def delegate_energy(
        self, partner_id: str, target_address: str, energy_amount: Decimal, duration_days: int = 1
    ) -> Dict[str, Any]:
        """
        에너지 위임 처리
        1. 최적 공급원 선택
        2. 에너지 위임 실행
        3. 결과 반환
        """
        try:
            # 최적 에너지 공급원 선택
            from app.services.energy_pool_service import EnergyPoolService
            pool_service = EnergyPoolService(self.db)
            
            source = await pool_service.get_optimal_energy_source(energy_amount)
            if not source:
                return {"success": False, "error": "사용 가능한 에너지 공급원이 없습니다"}

            # 에너지 할당
            source_id = source.__dict__['id']  # SQLAlchemy 모델에서 실제 값 추출
            allocation_success = await pool_service.allocate_energy(
                source_id=source_id,
                amount=energy_amount,
                partner_wallet=target_address
            )
            
            if not allocation_success:
                return {"success": False, "error": "에너지 할당에 실패했습니다"}

            # TODO: 실제 위임 트랜잭션 구현
            # delegation_tx = await self.tron_service.delegate_energy(...)
            
            # 현재는 더미 트랜잭션 해시 생성
            dummy_tx_hash = f"DELEGATION_{partner_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # 만료 시간 계산
            expires_at = datetime.utcnow() + timedelta(days=duration_days)

            return {
                "success": True,
                "tx_hash": dummy_tx_hash,
                "energy_amount": energy_amount,
                "expires_at": expires_at.isoformat() + "Z"
            }

        except Exception as e:
            logger.error(f"에너지 위임 실패: {e}")
            return {"success": False, "error": str(e)}

    async def optimize_withdrawal_batch(
        self, partner_id: str, withdrawal_requests: List[Dict]
    ) -> List[Dict]:
        """
        출금 배치 최적화
        문서 41번 4.3절 배치 그룹핑 로직 구현
        """
        batch_groups = []
        urgent_requests = []
        normal_requests = []

        # 긴급/일반 출금 분리
        for request in withdrawal_requests:
            if request.get("type") == "immediate":
                urgent_requests.append(request)
            else:
                normal_requests.append(request)

        # 배치 그룹핑 로직 적용
        if len(withdrawal_requests) < 10:
            # 개별 처리
            for request in withdrawal_requests:
                batch_groups.append({
                    "group_id": f"SINGLE_{request['request_id']}",
                    "requests": [request],
                    "processing_type": "individual"
                })
        else:
            # 긴급 건 우선 처리
            if urgent_requests:
                batch_groups.append({
                    "group_id": f"URGENT_BATCH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "requests": urgent_requests,
                    "processing_type": "urgent_batch"
                })

            # 일반 건 배치 처리
            if normal_requests:
                # 동일 수신 주소별 그룹핑
                address_groups = {}
                for request in normal_requests:
                    addr = request.get("to_address")
                    if addr not in address_groups:
                        address_groups[addr] = []
                    address_groups[addr].append(request)

                for addr, requests in address_groups.items():
                    batch_groups.append({
                        "group_id": f"NORMAL_BATCH_{addr[:8]}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        "requests": requests,
                        "processing_type": "normal_batch"
                    })

        logger.info(f"배치 최적화 완료: {len(withdrawal_requests)} 요청 -> {len(batch_groups)} 그룹")
        return batch_groups

    async def calculate_batch_saas_fee(self, withdrawal_count: int, has_urgent: bool = False) -> Decimal:
        """
        배치 SaaS 수수료 계산
        """
        base_fee_per_tx = Decimal("1.0")
        minimum_batch_fee = Decimal("5.0")

        if withdrawal_count < 10:
            # 개별 처리
            return withdrawal_count * base_fee_per_tx
        else:
            # 배치 처리
            total_fee = withdrawal_count * base_fee_per_tx
            return max(total_fee, minimum_batch_fee)

    async def get_wallet_energy_status(self, partner_id: str) -> Dict[str, Any]:
        """
        파트너사 지갑 에너지 상태 조회
        """
        # 실제로는 DB에서 파트너사 지갑 정보 조회
        # 현재는 더미 데이터 반환
        return {
            "hot_wallet_address": f"PARTNER_{partner_id}_HOT",
            "cold_wallet_address": f"PARTNER_{partner_id}_COLD",
            "hot_wallet_usdt_balance": Decimal("10000"),
            "hot_wallet_trx_balance": Decimal("500"),
            "current_energy": Decimal("150000"),
            "daily_average_usage": Decimal("480000"),
            "estimated_depletion": "6 hours",
            "auto_recharge_threshold": Decimal("100000")
        }

    async def get_partner_fee_settings(self, partner_id: str) -> Dict[str, Any]:
        """파트너사 수수료 설정 조회"""
        # 실제로는 DB에서 조회
        return {
            "per_transaction_fee": Decimal("1.0"),
            "minimum_batch_fee": Decimal("5.0"),
            "fee_type": "fixed",
            "last_updated": datetime.utcnow().isoformat(),
            "effective_from": datetime.utcnow().isoformat()
        }

    async def get_energy_usage_history(self, partner_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """파트너사 에너지 사용 이력 조회"""
        # 실제로는 DB에서 조회
        history = []
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "energy_used": Decimal("45000") + (Decimal("5000") * i % 3),
                "transactions_count": 15 + (i % 5),
                "total_cost_trx": Decimal("1.2") + (Decimal("0.3") * i % 3)
            })
        
        return history
