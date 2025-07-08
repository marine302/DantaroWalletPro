"""
슈퍼 어드민용 배포 관리 API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.services.deployment.deployment_service import DeploymentService
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["배포 관리"])


@router.post("/partners/{partner_id}/deploy")
async def deploy_partner_instance(
    partner_id: str,
    template_type: str = "standard",
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 인스턴스 배포"""
    try:
        deployment_service = DeploymentService(db)
        result = await deployment_service.create_partner_instance(partner_id, template_type)
        
        logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 인스턴스 배포")
        return result
        
    except Exception as e:
        logger.error(f"파트너 인스턴스 배포 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="파트너 인스턴스 배포 중 오류가 발생했습니다."
        )


@router.post("/partners/{partner_id}/configure")
async def configure_partner_environment(
    partner_id: str,
    config_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 환경 설정"""
    try:
        deployment_service = DeploymentService(db)
        success = await deployment_service.configure_partner_environment(partner_id, config_data)
        
        if success:
            logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 환경 설정")
            return {"message": "파트너 환경 설정이 완료되었습니다.", "partner_id": partner_id}
        else:
            raise HTTPException(status_code=400, detail="환경 설정 실패")
            
    except Exception as e:
        logger.error(f"파트너 환경 설정 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="파트너 환경 설정 중 오류가 발생했습니다."
        )


@router.post("/partners/{partner_id}/database")
async def setup_partner_database(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 데이터베이스 설정"""
    try:
        deployment_service = DeploymentService(db)
        success = await deployment_service.setup_partner_database(partner_id)
        
        if success:
            logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 데이터베이스 설정")
            return {"message": "파트너 데이터베이스 설정이 완료되었습니다.", "partner_id": partner_id}
        else:
            raise HTTPException(status_code=400, detail="데이터베이스 설정 실패")
            
    except Exception as e:
        logger.error(f"파트너 데이터베이스 설정 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="파트너 데이터베이스 설정 중 오류가 발생했습니다."
        )


@router.post("/partners/{partner_id}/templates")
async def deploy_partner_templates(
    partner_id: str,
    template_list: List[str],
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 템플릿 배포"""
    try:
        deployment_service = DeploymentService(db)
        status_result = await deployment_service.deploy_partner_templates(partner_id)
        
        logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 템플릿 배포")
        return status_result
        
    except Exception as e:
        logger.error(f"파트너 템플릿 배포 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="파트너 템플릿 배포 중 오류가 발생했습니다."
        )


@router.get("/partners/{partner_id}/status")
async def get_deployment_status(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 배포 상태 조회"""
    try:
        deployment_service = DeploymentService(db)
        status = await deployment_service.get_deployment_status(partner_id)
        
        logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 배포 상태 조회")
        return status
        
    except Exception as e:
        logger.error(f"배포 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="배포 상태 조회 중 오류가 발생했습니다."
        )


@router.delete("/partners/{partner_id}/deployment")
async def remove_partner_deployment(
    partner_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """파트너 배포 제거"""
    try:
        deployment_service = DeploymentService(db)
        success = await deployment_service.remove_partner_deployment(partner_id)
        
        if success:
            logger.info(f"관리자 {current_admin.id}가 파트너 {partner_id} 배포 제거")
            return {"message": "파트너 배포가 제거되었습니다.", "partner_id": partner_id}
        else:
            raise HTTPException(status_code=400, detail="배포 제거 실패")
            
    except Exception as e:
        logger.error(f"파트너 배포 제거 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="파트너 배포 제거 중 오류가 발생했습니다."
        )


@router.get("/templates")
async def get_available_templates(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """사용 가능한 템플릿 목록 조회"""
    try:
        deployment_service = DeploymentService(db)
        templates = await deployment_service.get_available_templates()
        
        logger.info(f"관리자 {current_admin.id}가 템플릿 목록 조회")
        return templates
        
    except Exception as e:
        logger.error(f"템플릿 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="템플릿 목록 조회 중 오류가 발생했습니다."
        )


@router.post("/templates")
async def create_template(
    template_data: Dict[str, Any],
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """새 템플릿 생성"""
    try:
        deployment_service = DeploymentService(db)
        template = await deployment_service.create_template(template_data, str(current_admin.id))
        
        logger.info(f"관리자 {current_admin.id}가 새 템플릿 생성: {template['name']}")
        return template
        
    except Exception as e:
        logger.error(f"템플릿 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="템플릿 생성 중 오류가 발생했습니다."
        )


@router.get("/deployments")
async def get_all_deployments(
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """전체 배포 현황 조회"""
    try:
        deployment_service = DeploymentService(db)
        deployments = await deployment_service.get_all_deployments(status_filter, limit)
        
        logger.info(f"관리자 {current_admin.id}가 전체 배포 현황 조회")
        return deployments
        
    except Exception as e:
        logger.error(f"배포 현황 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="배포 현황 조회 중 오류가 발생했습니다."
        )


@router.post("/rollback/{deployment_id}")
async def rollback_deployment(
    deployment_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_sync_db),
):
    """배포 롤백"""
    try:
        deployment_service = DeploymentService(db)
        success = await deployment_service.rollback_deployment(deployment_id, f"Rollback by admin {current_admin.id}")
        
        if success:
            logger.info(f"관리자 {current_admin.id}가 배포 {deployment_id} 롤백")
            return {"message": "배포 롤백이 완료되었습니다.", "deployment_id": deployment_id}
        else:
            raise HTTPException(status_code=400, detail="배포 롤백 실패")
            
    except Exception as e:
        logger.error(f"배포 롤백 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="배포 롤백 중 오류가 발생했습니다."
        )