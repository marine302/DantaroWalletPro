"""
컴플라이언스 체크 서비스 - Doc #30
AML/KYC 통합 및 컴플라이언스 체크 서비스
"""
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, desc, func

from app.models.audit import (
    ComplianceCheck, ComplianceCheckType, ComplianceStatus, 
    RiskLevel, SuspiciousActivity, AuditEventType
)
from app.models.user import User
from app.models.partner import Partner
from app.models.transaction import Transaction
from app.services.audit.audit_service import AuditService
from app.core.logger import get_logger

logger = get_logger(__name__)


def safe_int(value: Any, default: int = 0) -> int:
    """안전한 int 변환"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """안전한 str 변환"""
    if value is None:
        return default
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """안전한 bool 변환"""
    if value is None:
        return default
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default


def safe_enum_value(enum_value) -> str:
    """Enum 값을 안전하게 문자열로 변환"""
    if hasattr(enum_value, 'value'):
        return enum_value.value
    return str(enum_value)


def safe_datetime(value: Any, default: Optional[datetime] = None) -> Optional[datetime]:
    """안전한 datetime 변환"""
    if value is None:
        return default
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (ValueError, TypeError):
        return default


class ComplianceService:
    """컴플라이언스 체크 서비스"""
    
    def __init__(self, db: AsyncSession, audit_service: AuditService):
        self.db = db
        self.audit_service = audit_service
    
    async def create_compliance_check(
        self,
        check_type: ComplianceCheckType,
        entity_type: str,
        entity_id: str,
        check_data: Dict[str, Any],
        provider_response: Optional[Dict[str, Any]] = None
    ) -> Optional[ComplianceCheck]:
        """컴플라이언스 체크 생성"""
        try:
            # 초기 위험도 평가
            risk_level, score = self._calculate_initial_risk(check_type, check_data)
            
            # 컴플라이언스 체크 생성
            compliance_check = ComplianceCheck(
                check_type=check_type,
                entity_type=entity_type,
                entity_id=entity_id,
                status=ComplianceStatus.PENDING,
                risk_level=risk_level,
                score=score,
                check_data=check_data,
                provider_response=provider_response or {},
                initiated_at=datetime.utcnow()
            )
            
            self.db.add(compliance_check)
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(compliance_check)
            
            # 감사 로그 생성
            await self.audit_service.log_event(
                event_type=AuditEventType.COMPLIANCE_CHECK,
                entity_type=entity_type,
                entity_id=entity_id,
                event_data={
                    "check_type": check_type.value,
                    "risk_level": risk_level.value,
                    "score": score,
                    "status": ComplianceStatus.PENDING.value
                },
                event_category="compliance",
                risk_score=self._risk_level_to_score(risk_level)
            )
            
            logger.info(f"컴플라이언스 체크 생성: {check_type.value} - {entity_type}:{entity_id}")
            return compliance_check
            
        except Exception as e:
            logger.error(f"컴플라이언스 체크 생성 오류: {e}")
            await self.db.rollback()
            return None
    
    def _calculate_initial_risk(
        self, 
        check_type: ComplianceCheckType, 
        check_data: Dict[str, Any]
    ) -> tuple[RiskLevel, int]:
        """초기 위험도 계산"""
        try:
            # 기본 위험도
            base_scores = {
                ComplianceCheckType.KYC: 20,
                ComplianceCheckType.AML: 30,
                ComplianceCheckType.SANCTIONS: 50,
                ComplianceCheckType.PEP: 40,
                ComplianceCheckType.TRANSACTION_LIMIT: 25,
                ComplianceCheckType.SUSPICIOUS_PATTERN: 60
            }
            
            base_score = base_scores.get(check_type, 30)
            
            # 추가 위험 요소 평가
            additional_risk = 0
            
            # 거래 금액 기반 위험도
            if "amount" in check_data:
                amount = Decimal(str(check_data["amount"]))
                if amount > Decimal("10000"):  # $10,000 이상
                    additional_risk += 20
                elif amount > Decimal("5000"):  # $5,000 이상
                    additional_risk += 10
            
            # 거래 빈도 기반 위험도
            if "frequency" in check_data:
                frequency = check_data["frequency"]
                if frequency > 100:  # 일일 100회 이상
                    additional_risk += 30
                elif frequency > 50:  # 일일 50회 이상
                    additional_risk += 15
            
            # 지역 기반 위험도
            if "country" in check_data:
                high_risk_countries = ["AF", "IR", "KP", "SY"]  # 예시
                if check_data["country"] in high_risk_countries:
                    additional_risk += 40
            
            # 총 점수 계산
            total_score = min(base_score + additional_risk, 100)
            
            # 위험도 레벨 결정
            if total_score >= 80:
                risk_level = RiskLevel.CRITICAL
            elif total_score >= 60:
                risk_level = RiskLevel.HIGH
            elif total_score >= 40:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
            
            return risk_level, total_score
            
        except Exception as e:
            logger.error(f"위험도 계산 오류: {e}")
            return RiskLevel.MEDIUM, 50
    
    def _risk_level_to_score(self, risk_level: RiskLevel) -> int:
        """위험도 레벨을 점수로 변환"""
        scores = {
            RiskLevel.LOW: 25,
            RiskLevel.MEDIUM: 50,
            RiskLevel.HIGH: 75,
            RiskLevel.CRITICAL: 100
        }
        return scores.get(risk_level, 50)
    
    async def perform_kyc_check(
        self,
        user_id: int,
        kyc_data: Dict[str, Any]
    ) -> Optional[ComplianceCheck]:
        """KYC 체크 수행"""
        try:
            # 사용자 정보 조회
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"사용자를 찾을 수 없음: {user_id}")
                return None
            
            # KYC 체크 데이터 준비
            check_data = {
                "user_email": user.email,
                "kyc_level": kyc_data.get("kyc_level", "basic"),
                "documents_provided": kyc_data.get("documents", []),
                "verification_method": kyc_data.get("method", "automated"),
                **kyc_data
            }
            
            # 컴플라이언스 체크 생성
            compliance_check = await self.create_compliance_check(
                check_type=ComplianceCheckType.KYC,
                entity_type="user",
                entity_id=str(user_id),
                check_data=check_data
            )
            
            if compliance_check:
                # 자동 KYC 검증 수행
                await self._perform_automated_kyc_verification(compliance_check)
                # 완료 후 객체 새로고침
                await self.db.refresh(compliance_check)
            
            return compliance_check
            
        except Exception as e:
            logger.error(f"KYC 체크 수행 오류: {e}")
            return None
    
    async def _perform_automated_kyc_verification(self, compliance_check: ComplianceCheck):
        """자동 KYC 검증 수행"""
        try:
            # 기본 검증 로직
            check_data = compliance_check.check_data
            
            # 필수 정보 확인
            required_fields = ["user_email", "kyc_level"]
            missing_fields = [field for field in required_fields if field not in check_data]
            
            if missing_fields:
                # 검증 실패
                setattr(compliance_check, 'status', ComplianceStatus.FAILED)
                setattr(compliance_check, 'manual_review_notes', f"필수 정보 누락: {', '.join(missing_fields)}")
            else:
                # 기본 검증 통과
                setattr(compliance_check, 'status', ComplianceStatus.PASSED)
                current_score = safe_int(compliance_check.score, 0)
                new_score = max(current_score - 10, 0)  # 검증 통과 시 점수 감소
                setattr(compliance_check, 'score', new_score)
            
            setattr(compliance_check, 'completed_at', datetime.utcnow())
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(compliance_check)
            
            # 감사 로그 업데이트
            await self.audit_service.log_event(
                event_type=AuditEventType.COMPLIANCE_CHECK,
                entity_type="user",
                entity_id=safe_str(compliance_check.entity_id),
                event_data={
                    "check_type": safe_enum_value(compliance_check.check_type),
                    "status": safe_enum_value(compliance_check.status),
                    "score": safe_int(compliance_check.score, 0),
                    "automated_verification": True
                },
                event_category="compliance"
            )
            
        except Exception as e:
            logger.error(f"자동 KYC 검증 오류: {e}")
            await self.db.rollback()
    
    async def perform_aml_check(
        self,
        transaction_id: str,
        transaction_data: Dict[str, Any]
    ) -> Optional[ComplianceCheck]:
        """AML 체크 수행"""
        try:
            # AML 체크 데이터 준비
            check_data = {
                "transaction_id": transaction_id,
                "amount": str(transaction_data.get("amount", 0)),
                "currency": transaction_data.get("currency", "USDT"),
                "from_address": transaction_data.get("from_address", ""),
                "to_address": transaction_data.get("to_address", ""),
                "transaction_type": transaction_data.get("transaction_type", ""),
                "user_id": transaction_data.get("user_id"),
                "partner_id": transaction_data.get("partner_id"),
                **transaction_data
            }
            
            # 컴플라이언스 체크 생성
            compliance_check = await self.create_compliance_check(
                check_type=ComplianceCheckType.AML,
                entity_type="transaction",
                entity_id=transaction_id,
                check_data=check_data
            )
            
            if compliance_check:
                # 자동 AML 검증 수행
                await self._perform_automated_aml_verification(compliance_check)
                # 완료 후 객체 새로고침
                await self.db.refresh(compliance_check)
            
            return compliance_check
            
        except Exception as e:
            logger.error(f"AML 체크 수행 오류: {e}")
            return None
    
    async def _perform_automated_aml_verification(self, compliance_check: ComplianceCheck):
        """자동 AML 검증 수행"""
        try:
            check_data = compliance_check.check_data
            
            # 거래 금액 확인
            amount = Decimal(str(check_data.get("amount", 0)))
            
            # 고액 거래 확인
            if amount > Decimal("10000"):  # $10,000 이상
                setattr(compliance_check, 'status', ComplianceStatus.MANUAL_REVIEW)
                setattr(compliance_check, 'manual_review_notes', f"고액 거래 ({amount}) - 수동 검토 필요")
                setattr(compliance_check, 'risk_level', RiskLevel.HIGH)
            else:
                setattr(compliance_check, 'status', ComplianceStatus.PASSED)
                setattr(compliance_check, 'risk_level', RiskLevel.LOW)
            
            setattr(compliance_check, 'completed_at', datetime.utcnow())
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(compliance_check)
            
            # 감사 로그 업데이트 (check_data에서 entity_id 사용)
            entity_id = check_data.get("transaction_id", "unknown")
            await self.audit_service.log_event(
                event_type=AuditEventType.COMPLIANCE_CHECK,
                entity_type="transaction",
                entity_id=entity_id,
                event_data={
                    "check_type": safe_enum_value(compliance_check.check_type),
                    "status": safe_enum_value(compliance_check.status),
                    "risk_level": safe_enum_value(compliance_check.risk_level),
                    "amount": str(amount),
                    "automated_verification": True
                },
                event_category="compliance"
            )
            
        except Exception as e:
            logger.error(f"자동 AML 검증 오류: {e}")
            await self.db.rollback()
    
    async def perform_sanctions_check(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: Dict[str, Any]
    ) -> Optional[ComplianceCheck]:
        """제재 목록 체크 수행"""
        try:
            # 제재 목록 체크 데이터 준비
            check_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "check_timestamp": datetime.utcnow().isoformat(),
                **entity_data
            }
            
            # 컴플라이언스 체크 생성
            compliance_check = await self.create_compliance_check(
                check_type=ComplianceCheckType.SANCTIONS,
                entity_type=entity_type,
                entity_id=entity_id,
                check_data=check_data
            )
            
            if compliance_check:
                # 자동 제재 목록 검증 수행
                await self._perform_automated_sanctions_verification(compliance_check)
                # 완료 후 객체 새로고침
                await self.db.refresh(compliance_check)
            
            return compliance_check
            
        except Exception as e:
            logger.error(f"제재 목록 체크 수행 오류: {e}")
            return None
    
    async def _perform_automated_sanctions_verification(self, compliance_check: ComplianceCheck):
        """자동 제재 목록 검증 수행"""
        try:
            check_data = compliance_check.check_data
            
            # 간단한 제재 목록 체크 (실제 구현에서는 외부 API 사용)
            sanctions_keywords = ["terrorist", "sanctions", "blacklist", "prohibited"]
            
            # 체크 데이터에서 제재 관련 키워드 확인
            is_sanctioned = False
            for key, value in check_data.items():
                if isinstance(value, str):
                    for keyword in sanctions_keywords:
                        if keyword.lower() in value.lower():
                            is_sanctioned = True
                            break
                if is_sanctioned:
                    break
            
            if is_sanctioned:
                setattr(compliance_check, 'status', ComplianceStatus.FAILED)
                setattr(compliance_check, 'risk_level', RiskLevel.CRITICAL)
                setattr(compliance_check, 'manual_review_notes', "제재 목록 일치 - 거래 차단")
            else:
                setattr(compliance_check, 'status', ComplianceStatus.PASSED)
                setattr(compliance_check, 'risk_level', RiskLevel.LOW)
            
            setattr(compliance_check, 'completed_at', datetime.utcnow())
            await self.db.commit()
            
            # 객체를 새로고침하여 lazy loading 문제 방지
            await self.db.refresh(compliance_check)
            
            # 감사 로그 업데이트 (check_data에서 정보 사용)
            entity_type_from_data = check_data.get("entity_type", "unknown")
            entity_id_from_data = check_data.get("entity_id", "unknown")
            await self.audit_service.log_event(
                event_type=AuditEventType.COMPLIANCE_CHECK,
                entity_type=entity_type_from_data,
                entity_id=entity_id_from_data,
                event_data={
                    "check_type": safe_enum_value(compliance_check.check_type),
                    "status": safe_enum_value(compliance_check.status),
                    "risk_level": safe_enum_value(compliance_check.risk_level),
                    "is_sanctioned": is_sanctioned,
                    "automated_verification": True
                },
                event_category="compliance",
                severity="critical" if is_sanctioned else "info"
            )
            
        except Exception as e:
            logger.error(f"자동 제재 목록 검증 오류: {e}")
            await self.db.rollback()
    
    async def get_compliance_checks(
        self,
        limit: int = 100,
        offset: int = 0,
        check_type: Optional[ComplianceCheckType] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        status: Optional[ComplianceStatus] = None,
        risk_level: Optional[RiskLevel] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ComplianceCheck]:
        """컴플라이언스 체크 조회"""
        try:
            query = select(ComplianceCheck)
            
            # 필터 조건 적용
            conditions = []
            
            if check_type:
                conditions.append(ComplianceCheck.check_type == check_type)
            
            if entity_type:
                conditions.append(ComplianceCheck.entity_type == entity_type)
            
            if entity_id:
                conditions.append(ComplianceCheck.entity_id == entity_id)
            
            if status:
                conditions.append(ComplianceCheck.status == status)
            
            if risk_level:
                conditions.append(ComplianceCheck.risk_level == risk_level)
            
            if start_date:
                conditions.append(ComplianceCheck.initiated_at >= start_date)
            
            if end_date:
                conditions.append(ComplianceCheck.initiated_at <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 정렬 및 페이지네이션
            query = query.order_by(desc(ComplianceCheck.initiated_at)).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"컴플라이언스 체크 조회 오류: {e}")
            return []
    
    async def get_compliance_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """컴플라이언스 통계 조회"""
        try:
            # 기본 기간 설정 (최근 30일)
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # 총 체크 수
            total_checks_query = select(func.count(ComplianceCheck.id)).where(
                and_(
                    ComplianceCheck.initiated_at >= start_date,
                    ComplianceCheck.initiated_at <= end_date
                )
            )
            result = await self.db.execute(total_checks_query)
            total_checks = result.scalar_one_or_none() or 0
            
            # 체크 타입별 통계
            check_type_stats = {}
            for check_type in ComplianceCheckType:
                query = select(func.count(ComplianceCheck.id)).where(
                    and_(
                        ComplianceCheck.check_type == check_type,
                        ComplianceCheck.initiated_at >= start_date,
                        ComplianceCheck.initiated_at <= end_date
                    )
                )
                result = await self.db.execute(query)
                count = result.scalar_one_or_none() or 0
                check_type_stats[check_type.value] = count
            
            # 상태별 통계
            status_stats = {}
            for status in ComplianceStatus:
                query = select(func.count(ComplianceCheck.id)).where(
                    and_(
                        ComplianceCheck.status == status,
                        ComplianceCheck.initiated_at >= start_date,
                        ComplianceCheck.initiated_at <= end_date
                    )
                )
                result = await self.db.execute(query)
                count = result.scalar_one_or_none() or 0
                status_stats[status.value] = count
            
            # 위험도별 통계
            risk_stats = {}
            for risk_level in RiskLevel:
                query = select(func.count(ComplianceCheck.id)).where(
                    and_(
                        ComplianceCheck.risk_level == risk_level,
                        ComplianceCheck.initiated_at >= start_date,
                        ComplianceCheck.initiated_at <= end_date
                    )
                )
                result = await self.db.execute(query)
                count = result.scalar_one_or_none() or 0
                risk_stats[risk_level.value] = count
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_checks": total_checks,
                "check_type_stats": check_type_stats,
                "status_stats": status_stats,
                "risk_stats": risk_stats
            }
            
        except Exception as e:
            logger.error(f"컴플라이언스 통계 조회 오류: {e}")
            return {}
