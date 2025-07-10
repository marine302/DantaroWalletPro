"""
컴플라이언스 서비스 - KYC/AML 체크 및 규제 준수
"""
import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.audit import ComplianceCheck, SuspiciousActivity
from app.models.user import User
from app.models.transaction import Transaction
from app.core.logging import get_logger
from app.core.database import get_db_session

logger = get_logger(__name__)

def safe_datetime_assign(obj, attr: str, value: datetime):
    """SQLAlchemy 컬럼에 datetime 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_str_assign(obj, attr: str, value: str):
    """SQLAlchemy 컬럼에 문자열 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_int_assign(obj, attr: str, value: int):
    """SQLAlchemy 컬럼에 정수 값을 안전하게 할당"""
    setattr(obj, attr, value)

def safe_dict_assign(obj, attr: str, value: Dict):
    """SQLAlchemy 컬럼에 딕셔너리 값을 안전하게 할당"""
    setattr(obj, attr, value)

class ComplianceService:
    """컴플라이언스 서비스"""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db or get_db_session()
    
    async def perform_kyc_check(
        self,
        user_id: int,
        check_data: Dict[str, Any]
    ) -> ComplianceCheck:
        """KYC 체크 수행"""
        try:
            # 기존 KYC 체크 조회
            existing_check = self.db.query(ComplianceCheck).filter(
                ComplianceCheck.check_type == "kyc",
                ComplianceCheck.entity_type == "user",
                ComplianceCheck.entity_id == str(user_id),
                ComplianceCheck.status == "passed"
            ).first()
            
            if existing_check:
                logger.info(f"사용자 {user_id}의 KYC 이미 완료됨")
                return existing_check
            
            # 새로운 KYC 체크 생성
            kyc_check = ComplianceCheck(
                check_type="kyc",
                entity_type="user",
                entity_id=str(user_id),
                status="pending",
                check_data=check_data,
                initiated_at=datetime.utcnow()
            )
            
            # KYC 검증 로직 수행
            verification_result = await self._verify_kyc_data(check_data)
            
            safe_str_assign(kyc_check, "status", verification_result["status"])
            safe_str_assign(kyc_check, "risk_level", verification_result["risk_level"])
            safe_int_assign(kyc_check, "score", verification_result["score"])
            safe_dict_assign(kyc_check, "provider_response", verification_result["provider_response"])
            safe_datetime_assign(kyc_check, "completed_at", datetime.utcnow())
            
            self.db.add(kyc_check)
            self.db.commit()
            
            logger.info(f"KYC 체크 완료: 사용자 {user_id}, 상태: {kyc_check.status}")
            return kyc_check
            
        except Exception as e:
            logger.error(f"KYC 체크 실패: {str(e)}")
            self.db.rollback()
            raise
    
    async def perform_aml_check(
        self,
        user_id: int,
        transaction_amount: float,
        transaction_data: Dict[str, Any]
    ) -> ComplianceCheck:
        """AML 체크 수행"""
        try:
            aml_check = ComplianceCheck(
                check_type="aml",
                entity_type="user",
                entity_id=str(user_id),
                status="pending",
                check_data={
                    "transaction_amount": transaction_amount,
                    "transaction_data": transaction_data
                },
                initiated_at=datetime.utcnow()
            )
            
            # AML 검증 로직 수행
            verification_result = await self._verify_aml_data(
                user_id, transaction_amount, transaction_data
            )
            
            safe_str_assign(aml_check, "status", verification_result["status"])
            safe_str_assign(aml_check, "risk_level", verification_result["risk_level"])
            safe_int_assign(aml_check, "score", verification_result["score"])
            safe_dict_assign(aml_check, "provider_response", verification_result["provider_response"])
            safe_datetime_assign(aml_check, "completed_at", datetime.utcnow())
            
            self.db.add(aml_check)
            self.db.commit()
            
            logger.info(f"AML 체크 완료: 사용자 {user_id}, 상태: {aml_check.status}")
            return aml_check
            
        except Exception as e:
            logger.error(f"AML 체크 실패: {str(e)}")
            self.db.rollback()
            raise
    
    async def check_sanctions_list(
        self,
        name: str,
        address: Optional[str] = None,
        nationality: Optional[str] = None
    ) -> ComplianceCheck:
        """제재 목록 체크"""
        try:
            sanctions_check = ComplianceCheck(
                check_type="sanctions",
                entity_type="person",
                entity_id=name,
                status="pending",
                check_data={
                    "name": name,
                    "address": address,
                    "nationality": nationality
                },
                initiated_at=datetime.utcnow()
            )
            
            # 제재 목록 검증 로직
            verification_result = await self._check_sanctions_database(
                name, address, nationality
            )
            
            safe_str_assign(sanctions_check, "status", verification_result["status"])
            safe_str_assign(sanctions_check, "risk_level", verification_result["risk_level"])
            safe_int_assign(sanctions_check, "score", verification_result["score"])
            safe_dict_assign(sanctions_check, "provider_response", verification_result["provider_response"])
            safe_datetime_assign(sanctions_check, "completed_at", datetime.utcnow())
            
            self.db.add(sanctions_check)
            self.db.commit()
            
            logger.info(f"제재 목록 체크 완료: {name}, 상태: {sanctions_check.status}")
            return sanctions_check
            
        except Exception as e:
            logger.error(f"제재 목록 체크 실패: {str(e)}")
            self.db.rollback()
            raise
    
    async def check_pep_status(
        self,
        name: str,
        position: Optional[str] = None,
        country: Optional[str] = None
    ) -> ComplianceCheck:
        """PEP (정치적 노출인물) 체크"""
        try:
            pep_check = ComplianceCheck(
                check_type="pep",
                entity_type="person",
                entity_id=name,
                status="pending",
                check_data={
                    "name": name,
                    "position": position,
                    "country": country
                },
                initiated_at=datetime.utcnow()
            )
            
            # PEP 검증 로직
            verification_result = await self._check_pep_database(
                name, position, country
            )
            
            safe_str_assign(pep_check, "status", verification_result["status"])
            safe_str_assign(pep_check, "risk_level", verification_result["risk_level"])
            safe_int_assign(pep_check, "score", verification_result["score"])
            safe_dict_assign(pep_check, "provider_response", verification_result["provider_response"])
            safe_datetime_assign(pep_check, "completed_at", datetime.utcnow())
            
            self.db.add(pep_check)
            self.db.commit()
            
            logger.info(f"PEP 체크 완료: {name}, 상태: {pep_check.status}")
            return pep_check
            
        except Exception as e:
            logger.error(f"PEP 체크 실패: {str(e)}")
            self.db.rollback()
            raise
    
    async def _verify_kyc_data(self, check_data: Dict[str, Any]) -> Dict[str, Any]:
        """KYC 데이터 검증"""
        # 실제 구현에서는 외부 KYC 서비스와 연동
        await asyncio.sleep(0.1)  # 시뮬레이션
        
        # 기본 검증 로직
        required_fields = ["name", "birth_date", "nationality", "document_type", "document_number"]
        missing_fields = [field for field in required_fields if not check_data.get(field)]
        
        if missing_fields:
            return {
                "status": "failed",
                "risk_level": "high",
                "score": 0,
                "provider_response": {
                    "error": f"필수 필드 누락: {', '.join(missing_fields)}"
                }
            }
        
        # 문서 유효성 검증 시뮬레이션
        document_valid = len(check_data.get("document_number", "")) >= 8
        
        if document_valid:
            return {
                "status": "passed",
                "risk_level": "low",
                "score": 85,
                "provider_response": {
                    "document_verified": True,
                    "identity_confirmed": True
                }
            }
        else:
            return {
                "status": "manual_review",
                "risk_level": "medium",
                "score": 60,
                "provider_response": {
                    "document_verified": False,
                    "reason": "문서 번호 형식 오류"
                }
            }
    
    async def _verify_aml_data(
        self,
        user_id: int,
        amount: float,
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AML 데이터 검증"""
        await asyncio.sleep(0.1)  # 시뮬레이션
        
        risk_score = 0
        risk_factors = []
        
        # 고액 거래 체크
        if amount > 10000:
            risk_score += 30
            risk_factors.append("고액 거래")
        
        # 빈번한 거래 체크
        recent_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        if recent_transactions > 10:
            risk_score += 20
            risk_factors.append("빈번한 거래")
        
        # 위험 레벨 결정
        if risk_score >= 50:
            risk_level = "high"
            status = "manual_review"
        elif risk_score >= 30:
            risk_level = "medium"
            status = "passed"
        else:
            risk_level = "low"
            status = "passed"
        
        return {
            "status": status,
            "risk_level": risk_level,
            "score": max(0, 100 - risk_score),
            "provider_response": {
                "risk_factors": risk_factors,
                "risk_score": risk_score
            }
        }
    
    async def _check_sanctions_database(
        self,
        name: str,
        address: Optional[str],
        nationality: Optional[str]
    ) -> Dict[str, Any]:
        """제재 데이터베이스 체크"""
        await asyncio.sleep(0.1)  # 시뮬레이션
        
        # 실제 구현에서는 OFAC, UN 등의 제재 목록과 대조
        # 시뮬레이션: 특정 이름들을 제재 목록에 있다고 가정
        sanctioned_names = ["John Doe", "Jane Smith", "테스트 제재자"]
        
        if name in sanctioned_names:
            return {
                "status": "failed",
                "risk_level": "critical",
                "score": 0,
                "provider_response": {
                    "match_found": True,
                    "list_source": "OFAC",
                    "match_details": f"{name}이 제재 목록에 있습니다"
                }
            }
        
        return {
            "status": "passed",
            "risk_level": "low",
            "score": 100,
            "provider_response": {
                "match_found": False,
                "lists_checked": ["OFAC", "UN", "EU"]
            }
        }
    
    async def _check_pep_database(
        self,
        name: str,
        position: Optional[str],
        country: Optional[str]
    ) -> Dict[str, Any]:
        """PEP 데이터베이스 체크"""
        await asyncio.sleep(0.1)  # 시뮬레이션
        
        # 실제 구현에서는 PEP 데이터베이스와 대조
        # 시뮬레이션: 특정 직책을 가진 사람들을 PEP로 가정
        pep_positions = ["대통령", "총리", "장관", "대사", "판사"]
        
        if position and any(pos in position for pos in pep_positions):
            return {
                "status": "manual_review",
                "risk_level": "high",
                "score": 40,
                "provider_response": {
                    "pep_found": True,
                    "position": position,
                    "country": country,
                    "risk_category": "정치적 노출인물"
                }
            }
        
        return {
            "status": "passed",
            "risk_level": "low",
            "score": 100,
            "provider_response": {
                "pep_found": False,
                "databases_checked": ["World Check", "PEP Database"]
            }
        }
    
    async def get_compliance_history(
        self,
        entity_type: str,
        entity_id: str,
        check_type: Optional[str] = None,
        limit: int = 50
    ) -> List[ComplianceCheck]:
        """컴플라이언스 체크 이력 조회"""
        query = self.db.query(ComplianceCheck).filter(
            ComplianceCheck.entity_type == entity_type,
            ComplianceCheck.entity_id == entity_id
        )
        
        if check_type:
            query = query.filter(ComplianceCheck.check_type == check_type)
        
        return query.order_by(desc(ComplianceCheck.initiated_at)).limit(limit).all()
    
    async def get_pending_reviews(self) -> List[ComplianceCheck]:
        """수동 검토 대기 중인 체크 목록"""
        return self.db.query(ComplianceCheck).filter(
            ComplianceCheck.status == "manual_review"
        ).order_by(ComplianceCheck.initiated_at).all()
    
    def close(self):
        """세션 종료"""
        if self.db:
            self.db.close()
