"""파트너사 종합 대시보드 서비스"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.energy_pool import EnergyPoolModel
from app.models.partner import Partner
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.services.balance.balance_service import BalanceService
from app.services.external_energy_service import safe_get_value
from app.services.wallet.wallet_service import WalletService

logger = get_logger(__name__)

# FastAPI Router
router = APIRouter(prefix="/integrated-dashboard", tags=["Integrated Dashboard"])


class IntegratedDashboard:
    """파트너사 종합 대시보드 서비스"""

    def __init__(self, db: AsyncSession, partner_id: int):
        self.db = db
        self.partner_id = partner_id
        self.cache_key = f"dashboard:{partner_id}"
        self.cache_data = {}  # 간단한 메모리 캐시
        self.cache_ttl = 30  # 30초
        self.wallet_service = WalletService(db)
        # 임시 balance_service 대신 직접 구현
        self.balance_cache = {}  # 간단한 잔액 캐시

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """종합 대시보드 데이터 조회"""
        try:
            # 간단한 캐시 확인
            now = datetime.utcnow()
            if (
                self.cache_key in self.cache_data
                and (now - self.cache_data[self.cache_key]["timestamp"]).seconds
                < self.cache_ttl
            ):
                return self.cache_data[self.cache_key]["data"]

            # 병렬 처리로 성능 최적화
            tasks = [
                self.get_wallet_overview(),
                self.get_transaction_flow(),
                self.get_energy_status(),
                self.get_user_analytics(),
                self.get_revenue_metrics(),
                self.get_risk_alerts(),
                self.get_predictions(),
                self.get_system_health(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            dashboard_data = {
                "wallet_overview": (
                    results[0] if not isinstance(results[0], Exception) else {}
                ),
                "transaction_flow": (
                    results[1] if not isinstance(results[1], Exception) else {}
                ),
                "energy_status": (
                    results[2] if not isinstance(results[2], Exception) else {}
                ),
                "user_analytics": (
                    results[3] if not isinstance(results[3], Exception) else {}
                ),
                "revenue_metrics": (
                    results[4] if not isinstance(results[4], Exception) else {}
                ),
                "risk_alerts": (
                    results[5] if not isinstance(results[5], Exception) else []
                ),
                "predictions": (
                    results[6] if not isinstance(results[6], Exception) else {}
                ),
                "system_health": (
                    results[7] if not isinstance(results[7], Exception) else {}
                ),
                "last_updated": datetime.utcnow(),
            }

            # 캐시 저장
            self.cache_data[self.cache_key] = {"data": dashboard_data, "timestamp": now}

            return dashboard_data

        except Exception as e:
            logger.error(f"대시보드 데이터 조회 실패: {str(e)}")
            return self._get_empty_dashboard()

    async def get_wallet_overview(self) -> Dict[str, Any]:
        """멀티 지갑 통합 현황"""
        try:
            stmt = select(Wallet).where(Wallet.partner_id == self.partner_id)
            result = await self.db.execute(stmt)
            wallets = result.scalars().all()

            total_balance = Decimal("0")
            wallet_distribution = {
                "hot": {"balance": Decimal("0"), "percentage": 0, "wallets": []},
                "warm": {"balance": Decimal("0"), "percentage": 0, "wallets": []},
                "cold": {"balance": Decimal("0"), "percentage": 0, "wallets": []},
            }

            for wallet in wallets:
                # safe_get_value 사용으로 안전한 주소 접근
                address = safe_get_value(wallet, "address", "")
                balance = await self.get_wallet_balance(address)
                total_balance += balance

                wallet_type = self.classify_wallet_type(wallet)
                wallet_distribution[wallet_type]["balance"] += balance
                wallet_distribution[wallet_type]["wallets"].append(
                    {
                        "address": address,
                        "balance": float(balance),
                        "status": safe_get_value(wallet, "status", "active"),
                        "last_activity": safe_get_value(
                            wallet, "updated_at", datetime.utcnow()
                        ),
                    }
                )

            # 비율 계산
            if total_balance > 0:
                for wallet_type in wallet_distribution:
                    wallet_distribution[wallet_type]["percentage"] = float(
                        wallet_distribution[wallet_type]["balance"]
                        / total_balance
                        * 100
                    )

            return {
                "total_balance": float(total_balance),
                "wallet_count": len(wallets),
                "distribution": wallet_distribution,
                "security_score": self.calculate_security_score(wallet_distribution),
                "diversification_index": self.calculate_diversification_index(
                    wallet_distribution
                ),
            }

        except Exception as e:
            logger.error(f"지갑 현황 조회 실패: {str(e)}")
            return {}

    async def get_transaction_flow(self) -> Dict[str, Any]:
        """실시간 거래 흐름 분석"""
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)

            # 24시간 거래 통계
            stmt = select(
                func.count(Transaction.id).label("total_count"),
                func.sum(Transaction.amount).label("total_volume"),
                func.avg(Transaction.amount).label("avg_amount"),
            ).where(
                and_(
                    Transaction.partner_id == self.partner_id,
                    Transaction.created_at >= last_24h,
                )
            )

            result = await self.db.execute(stmt)
            row = result.first()

            # 안전한 결과 처리
            total_count = int(row.total_count) if row and row.total_count else 0
            total_volume = float(row.total_volume) if row and row.total_volume else 0.0
            avg_amount = float(row.avg_amount) if row and row.avg_amount else 0.0

            # 시간대별 거래 분포
            hourly_stats = await self.get_hourly_transaction_stats(last_24h)

            # 거래 유형별 분포
            type_distribution = await self.get_transaction_type_distribution(last_24h)

            return {
                "total_transactions": total_count,
                "total_volume": total_volume,
                "average_amount": avg_amount,
                "hourly_distribution": hourly_stats,
                "type_distribution": type_distribution,
                "flow_velocity": self.calculate_flow_velocity(hourly_stats),
                "peak_hours": self.identify_peak_hours(hourly_stats),
            }

        except Exception as e:
            logger.error(f"거래 흐름 분석 실패: {str(e)}")
            return {}

    async def get_energy_status(self) -> Dict[str, Any]:
        """에너지 풀 현황"""
        try:
            stmt = select(EnergyPoolModel).where(
                EnergyPoolModel.partner_id == self.partner_id
            )
            result = await self.db.execute(stmt)
            energy_pools = result.scalars().all()

            total_energy = Decimal("0")
            available_energy = Decimal("0")
            frozen_energy = Decimal("0")

            for pool in energy_pools:
                # safe_get_value 사용으로 안전한 값 처리
                pool_total = Decimal(str(safe_get_value(pool, "total_energy", 0)))
                pool_available = Decimal(
                    str(safe_get_value(pool, "available_energy", 0))
                )
                pool_frozen = Decimal(str(safe_get_value(pool, "frozen_energy", 0)))

                total_energy += pool_total
                available_energy += pool_available
                frozen_energy += pool_frozen

            # 에너지 사용률
            usage_rate = 0
            if total_energy > 0:
                usage_rate = float(
                    (total_energy - available_energy) / total_energy * 100
                )

            # 에너지 트랜잭션 통계
            energy_tx_stats = await self.get_energy_transaction_stats()

            return {
                "total_energy": float(total_energy),
                "available_energy": float(available_energy),
                "frozen_energy": float(frozen_energy),
                "usage_rate": usage_rate,
                "pool_count": len(energy_pools),
                "energy_efficiency": self.calculate_energy_efficiency(energy_tx_stats),
                "cost_per_transaction": self.calculate_cost_per_transaction(
                    energy_tx_stats
                ),
                "burn_rate": self.calculate_energy_burn_rate(energy_tx_stats),
            }

        except Exception as e:
            logger.error(f"에너지 현황 조회 실패: {str(e)}")
            return {}

    async def get_user_analytics(self) -> Dict[str, Any]:
        """사용자 분석"""
        try:
            stmt = select(
                func.count(User.id).label("total_users"),
                func.count(
                    User.id.where(
                        User.last_login >= datetime.utcnow() - timedelta(days=30)
                    )
                ).label("active_users"),
                func.count(
                    User.id.where(
                        User.created_at >= datetime.utcnow() - timedelta(days=30)
                    )
                ).label("new_users"),
            ).where(User.partner_id == self.partner_id)

            result = await self.db.execute(stmt)
            row = result.first()

            # 안전한 결과 처리
            total_users = int(row.total_users) if row and row.total_users else 0
            active_users = int(row.active_users) if row and row.active_users else 0
            new_users = int(row.new_users) if row and row.new_users else 0

            # 사용자 세그먼트 분석
            segments = await self.get_user_segments()

            # 활동 패턴 분석
            activity_patterns = await self.get_user_activity_patterns()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users": new_users,
                "retention_rate": self.calculate_retention_rate(row),
                "user_segments": segments,
                "activity_patterns": activity_patterns,
                "churn_risk": self.calculate_churn_risk(activity_patterns),
            }

        except Exception as e:
            logger.error(f"사용자 분석 실패: {str(e)}")
            return {}

    async def get_revenue_metrics(self) -> Dict[str, Any]:
        """수익 지표"""
        try:
            now = datetime.utcnow()
            last_30d = now - timedelta(days=30)

            # 수수료 수익 계산
            fee_revenue = await self.calculate_fee_revenue(last_30d)

            # 에너지 수익 계산
            energy_revenue = await self.calculate_energy_revenue(last_30d)

            # 기타 수익원
            other_revenue = await self.calculate_other_revenue(last_30d)

            total_revenue = fee_revenue + energy_revenue + other_revenue

            return {
                "total_revenue": float(total_revenue),
                "fee_revenue": float(fee_revenue),
                "energy_revenue": float(energy_revenue),
                "other_revenue": float(other_revenue),
                "revenue_growth": await self.calculate_revenue_growth(),
                "arpu": await self.calculate_arpu(),  # Average Revenue Per User
                "ltv": await self.calculate_ltv(),  # Lifetime Value
                "revenue_forecast": await self.forecast_revenue(),
            }

        except Exception as e:
            logger.error(f"수익 지표 계산 실패: {str(e)}")
            return {}

    async def get_risk_alerts(self) -> List[Dict[str, Any]]:
        """리스크 알림"""
        try:
            alerts = []

            # 잔액 부족 알림
            low_balance_alerts = await self.check_low_balance_alerts()
            alerts.extend(low_balance_alerts)

            # 에너지 부족 알림
            low_energy_alerts = await self.check_low_energy_alerts()
            alerts.extend(low_energy_alerts)

            # 이상 거래 알림
            anomaly_alerts = await self.check_anomaly_alerts()
            alerts.extend(anomaly_alerts)

            # 시스템 상태 알림
            system_alerts = await self.check_system_alerts()
            alerts.extend(system_alerts)

            # 우선순위별 정렬
            alerts.sort(key=lambda x: x.get("priority", 0), reverse=True)

            return alerts

        except Exception as e:
            logger.error(f"리스크 알림 조회 실패: {str(e)}")
            return []

    async def get_predictions(self) -> Dict[str, Any]:
        """예측 분석"""
        try:
            # 거래량 예측
            volume_prediction = await self.predict_transaction_volume()

            # 에너지 소비 예측
            energy_prediction = await self.predict_energy_consumption()

            # 수익 예측
            revenue_prediction = await self.predict_revenue()

            return {
                "volume_prediction": volume_prediction,
                "energy_prediction": energy_prediction,
                "revenue_prediction": revenue_prediction,
                "confidence_score": self.calculate_prediction_confidence(),
                "forecast_horizon": "7d",
                "model_accuracy": await self.get_model_accuracy(),
            }

        except Exception as e:
            logger.error(f"예측 분석 실패: {str(e)}")
            return {}

    async def get_system_health(self) -> Dict[str, Any]:
        """시스템 상태"""
        try:
            # 데이터베이스 상태
            db_health = await self.check_database_health()

            # 지갑 연결 상태
            wallet_health = await self.check_wallet_connections()

            # 외부 서비스 상태
            external_health = await self.check_external_services()

            # 전체 시스템 점수
            overall_score = (
                db_health["score"] + wallet_health["score"] + external_health["score"]
            ) / 3

            return {
                "overall_score": overall_score,
                "database": db_health,
                "wallets": wallet_health,
                "external_services": external_health,
                "uptime": await self.get_system_uptime(),
                "last_maintenance": await self.get_last_maintenance(),
                "performance_metrics": await self.get_performance_metrics(),
            }

        except Exception as e:
            logger.error(f"시스템 상태 조회 실패: {str(e)}")
            return {}

    # 헬퍼 메서드들
    async def get_wallet_balance(self, address: str) -> Decimal:
        """지갑 잔액 조회"""
        try:
            # 캐시에서 잔액 확인
            if address in self.balance_cache:
                return self.balance_cache[address]

            # 실제 구현 시 TRON API 호출로 대체
            # 임시로 기본값 반환
            balance = Decimal("0")

            # 캐시 저장
            self.balance_cache[address] = balance
            return balance
        except Exception:
            return Decimal("0")

    def classify_wallet_type(self, wallet: Wallet) -> str:
        """지갑 타입 분류"""
        # 지갑 활동 빈도와 잔액에 따라 분류
        wallet_type = safe_get_value(wallet, "wallet_type", "warm")
        if wallet_type in ["hot", "warm", "cold"]:
            return wallet_type
        return "warm"

    def calculate_security_score(self, distribution: Dict) -> float:
        """보안 점수 계산"""
        # 지갑 분산도에 따른 보안 점수
        hot_ratio = distribution["hot"]["percentage"]
        cold_ratio = distribution["cold"]["percentage"]

        if hot_ratio > 80:
            return 30  # 위험
        elif hot_ratio > 60:
            return 60  # 보통
        elif cold_ratio > 40:
            return 90  # 안전
        else:
            return 75  # 양호

    def calculate_diversification_index(self, distribution: Dict) -> float:
        """분산 지수 계산"""
        # 지갑 분산도 계산 (0-1 사이)
        ratios = [dist["percentage"] for dist in distribution.values()]
        return 1 - sum([(r / 100) ** 2 for r in ratios])

    def _get_empty_dashboard(self) -> Dict[str, Any]:
        """빈 대시보드 데이터 반환"""
        return {
            "wallet_overview": {},
            "transaction_flow": {},
            "energy_status": {},
            "user_analytics": {},
            "revenue_metrics": {},
            "risk_alerts": [],
            "predictions": {},
            "system_health": {},
            "last_updated": datetime.utcnow(),
            "error": True,
        }

    # 추가 헬퍼 메서드들은 필요에 따라 구현
    async def get_hourly_transaction_stats(self, since: datetime) -> List[Dict]:
        """시간대별 거래 통계"""
        # 구현 예정
        return []

    async def get_transaction_type_distribution(self, since: datetime) -> Dict:
        """거래 유형별 분포"""
        # 구현 예정
        return {}

    def calculate_flow_velocity(self, hourly_stats: List) -> float:
        """거래 흐름 속도 계산"""
        # 구현 예정
        return 0.0

    def identify_peak_hours(self, hourly_stats: List) -> List[int]:
        """피크 시간대 식별"""
        # 구현 예정
        return []

    async def get_energy_transaction_stats(self) -> Dict:
        """에너지 거래 통계"""
        # 구현 예정
        return {}

    def calculate_energy_efficiency(self, stats: Dict) -> float:
        """에너지 효율성 계산"""
        # 구현 예정
        return 0.0

    def calculate_cost_per_transaction(self, stats: Dict) -> float:
        """거래당 비용 계산"""
        # 구현 예정
        return 0.0

    def calculate_energy_burn_rate(self, stats: Dict) -> float:
        """에너지 소모율 계산"""
        # 구현 예정
        return 0.0

    async def get_user_segments(self) -> Dict:
        """사용자 세그먼트 분석"""
        # 구현 예정
        return {}

    async def get_user_activity_patterns(self) -> Dict:
        """사용자 활동 패턴 분석"""
        # 구현 예정
        return {}

    def calculate_retention_rate(self, stats) -> float:
        """사용자 유지율 계산"""
        # 구현 예정
        return 0.0

    def calculate_churn_risk(self, patterns: Dict) -> float:
        """이탈 위험도 계산"""
        # 구현 예정
        return 0.0

    async def calculate_fee_revenue(self, since: datetime) -> Decimal:
        """수수료 수익 계산"""
        # 구현 예정
        return Decimal("0")

    async def calculate_energy_revenue(self, since: datetime) -> Decimal:
        """에너지 수익 계산"""
        # 구현 예정
        return Decimal("0")

    async def calculate_other_revenue(self, since: datetime) -> Decimal:
        """기타 수익 계산"""
        # 구현 예정
        return Decimal("0")

    async def calculate_revenue_growth(self) -> float:
        """수익 성장률 계산"""
        # 구현 예정
        return 0.0

    async def calculate_arpu(self) -> float:
        """사용자당 평균 수익 계산"""
        # 구현 예정
        return 0.0

    async def calculate_ltv(self) -> float:
        """생애 가치 계산"""
        # 구현 예정
        return 0.0

    async def forecast_revenue(self) -> Dict:
        """수익 예측"""
        # 구현 예정
        return {}

    async def check_low_balance_alerts(self) -> List[Dict]:
        """잔액 부족 알림 확인"""
        # 구현 예정
        return []

    async def check_low_energy_alerts(self) -> List[Dict]:
        """에너지 부족 알림 확인"""
        # 구현 예정
        return []

    async def check_anomaly_alerts(self) -> List[Dict]:
        """이상 거래 알림 확인"""
        # 구현 예정
        return []

    async def check_system_alerts(self) -> List[Dict]:
        """시스템 상태 알림 확인"""
        # 구현 예정
        return []

    async def predict_transaction_volume(self) -> Dict:
        """거래량 예측"""
        # 구현 예정
        return {}

    async def predict_energy_consumption(self) -> Dict:
        """에너지 소비 예측"""
        # 구현 예정
        return {}

    async def predict_revenue(self) -> Dict:
        """수익 예측"""
        # 구현 예정
        return {}

    def calculate_prediction_confidence(self) -> float:
        """예측 신뢰도 계산"""
        # 구현 예정
        return 0.0

    async def get_model_accuracy(self) -> float:
        """모델 정확도 조회"""
        # 구현 예정
        return 0.0

    async def check_database_health(self) -> Dict:
        """데이터베이스 상태 확인"""
        # 구현 예정
        return {"score": 100, "status": "healthy"}

    async def check_wallet_connections(self) -> Dict:
        """지갑 연결 상태 확인"""
        # 구현 예정
        return {"score": 100, "status": "connected"}

    async def check_external_services(self) -> Dict:
        """외부 서비스 상태 확인"""
        # 구현 예정
        return {"score": 100, "status": "operational"}

    async def get_system_uptime(self) -> float:
        """시스템 가동 시간 조회"""
        # 구현 예정
        return 99.9

    async def get_last_maintenance(self) -> datetime:
        """마지막 유지보수 시간 조회"""
        # 구현 예정
        return datetime.utcnow() - timedelta(days=7)

    async def get_performance_metrics(self) -> Dict:
        """성능 지표 조회"""
        # 구현 예정
        return {}


# API 엔드포인트들
@router.get("/overview/{partner_id}")
async def get_dashboard_overview(partner_id: int, db: AsyncSession = Depends(get_db)):
    """파트너사 대시보드 개요 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_dashboard_data()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Dashboard overview error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wallet-overview/{partner_id}")
async def get_wallet_overview(partner_id: int, db: AsyncSession = Depends(get_db)):
    """지갑 개요 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_wallet_overview()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Wallet overview error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transaction-flow/{partner_id}")
async def get_transaction_flow(partner_id: int, db: AsyncSession = Depends(get_db)):
    """거래 흐름 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_transaction_flow()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Transaction flow error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/energy-status/{partner_id}")
async def get_energy_status(partner_id: int, db: AsyncSession = Depends(get_db)):
    """에너지 상태 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_energy_status()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Energy status error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health/{partner_id}")
async def get_system_health(partner_id: int, db: AsyncSession = Depends(get_db)):
    """시스템 건강도 분석 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_system_health()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"System health error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-analytics/{partner_id}")
async def get_user_analytics(partner_id: int, db: AsyncSession = Depends(get_db)):
    """사용자 분석 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_user_analytics()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"User analytics error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue-metrics/{partner_id}")
async def get_revenue_metrics(partner_id: int, db: AsyncSession = Depends(get_db)):
    """수익 지표 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_revenue_metrics()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Revenue metrics error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-alerts/{partner_id}")
async def get_risk_alerts(partner_id: int, db: AsyncSession = Depends(get_db)):
    """위험 알림 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_risk_alerts()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Risk alerts error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/{partner_id}")
async def get_predictions(partner_id: int, db: AsyncSession = Depends(get_db)):
    """예측 데이터 조회"""
    try:
        dashboard = IntegratedDashboard(db, partner_id)
        data = await dashboard.get_predictions()
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"Predictions error for partner {partner_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_dashboard():
    """대시보드 연결 테스트"""
    return {
        "success": True,
        "message": "Integrated Dashboard API is working",
        "timestamp": datetime.utcnow().isoformat(),
    }
