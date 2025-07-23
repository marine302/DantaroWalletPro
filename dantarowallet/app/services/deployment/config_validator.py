"""
설정 검증자 모듈
파트너 환경 설정 및 검증
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.partner import Partner

from .utils import safe_dict, safe_str


class ConfigValidator:
    """설정 검증자"""

    def __init__(self, db: Session):
        self.db = db

    async def configure_partner_environment(
        self, partner_id: str, config_data: Dict[str, Any]
    ) -> bool:
        """파트너 환경 설정"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                raise HTTPException(status_code=404, detail="Partner not found")

            # 환경 변수 설정
            env_config = self._create_environment_config(partner)

            # 브랜딩 설정
            branding_config = safe_dict(partner.settings).get("branding", {})

            # 기능 설정
            feature_config = self._create_feature_config(partner)

            # 설정 업데이트
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config.update(
                {
                    "environment_variables": env_config,
                    "branding_config": branding_config,
                    "feature_config": feature_config,
                    "configured_at": datetime.utcnow().isoformat(),
                }
            )

            # 데이터베이스 업데이트
            self._update_partner_config(partner_id, deployment_config)

            return True

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to configure partner environment: {str(e)}",
            )

    def _create_environment_config(self, partner: Partner) -> Dict[str, str]:
        """환경 변수 설정 생성"""
        return {
            "PARTNER_ID": safe_str(partner.id),
            "PARTNER_NAME": safe_str(partner.name),
            "API_KEY": safe_str(partner.api_key),
            "DATABASE_URL": f"postgresql://user:pass@db:5432/dantaro_{safe_str(partner.id).replace('-', '_')}",
            "REDIS_URL": "redis://redis:6379/0",
            "TRON_NETWORK": "mainnet",
            "ENERGY_POOL_ADDRESS": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
            "WEBHOOK_SECRET": f"whsec_{uuid.uuid4().hex}",
            "DOMAIN": safe_str(partner.domain)
            or f"{safe_str(partner.name).lower().replace(' ', '-')}.dantarowallet.com",
        }

    def _create_feature_config(self, partner: Partner) -> Dict[str, Any]:
        """기능 설정 생성"""
        return safe_dict(partner.settings).get(
            "features",
            {
                "multi_signature": True,
                "cold_wallet": True,
                "auto_sweep": False,
                "api_access": True,
                "webhook_notifications": True,
                "2fa_required": False,
            },
        )

    def _update_partner_config(
        self, partner_id: str, deployment_config: Dict[str, Any]
    ) -> None:
        """파트너 설정 업데이트"""
        update_query = (
            update(Partner)
            .where(Partner.id == partner_id)
            .values(deployment_config=deployment_config)
        )
        self.db.execute(update_query)
        self.db.commit()

    def validate_configuration(self, config_data: Dict[str, Any]) -> List[str]:
        """설정 유효성 검증"""
        errors = []

        # 필수 필드 검증
        required_fields = ["partner_id", "domain", "api_key"]
        for field in required_fields:
            if not config_data.get(field):
                errors.append(f"Missing required field: {field}")

        # 도메인 형식 검증
        domain = config_data.get("domain", "")
        if domain and not self._is_valid_domain(domain):
            errors.append("Invalid domain format")

        # API 키 형식 검증
        api_key = config_data.get("api_key", "")
        if api_key and len(api_key) < 32:
            errors.append("API key must be at least 32 characters")

        # 기능 설정 검증
        features = config_data.get("features", {})
        if features:
            feature_errors = self._validate_features(features)
            errors.extend(feature_errors)

        return errors

    def _is_valid_domain(self, domain: str) -> bool:
        """도메인 형식 유효성 검사"""
        import re

        domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
        return bool(re.match(domain_pattern, domain))

    def _validate_features(self, features: Dict[str, Any]) -> List[str]:
        """기능 설정 유효성 검증"""
        errors = []
        valid_features = {
            "multi_signature",
            "cold_wallet",
            "auto_sweep",
            "api_access",
            "webhook_notifications",
            "2fa_required",
        }

        for feature in features:
            if feature not in valid_features:
                errors.append(f"Unknown feature: {feature}")

        return errors

    async def setup_partner_database(self, partner_id: str) -> bool:
        """파트너 데이터베이스 설정"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                return False

            # 데이터베이스 생성 시뮬레이션
            database_config = {
                "database_name": f"dantaro_{safe_str(partner.id).replace('-', '_')}",
                "created_at": datetime.utcnow().isoformat(),
                "status": "created",
            }

            # 설정 업데이트
            deployment_config = safe_dict(partner.deployment_config)
            deployment_config["database_config"] = database_config

            self._update_partner_config(partner_id, deployment_config)

            return True

        except Exception:
            return False

    def get_configuration_status(self, partner_id: str) -> Dict[str, Any]:
        """설정 상태 조회"""
        try:
            partner = self.db.query(Partner).filter(Partner.id == partner_id).first()
            if not partner:
                return {"status": "not_found"}

            deployment_config = safe_dict(partner.deployment_config)

            status = {
                "environment_configured": "environment_variables" in deployment_config,
                "database_configured": "database_config" in deployment_config,
                "features_configured": "feature_config" in deployment_config,
                "branding_configured": "branding_config" in deployment_config,
                "overall_status": "pending",
            }

            # 전체 상태 계산
            configured_count = sum(
                [
                    status["environment_configured"],
                    status["database_configured"],
                    status["features_configured"],
                    status["branding_configured"],
                ]
            )

            if configured_count == 4:
                status["overall_status"] = "completed"
            elif configured_count > 0:
                status["overall_status"] = "in_progress"

            return status

        except Exception:
            return {"status": "error"}
