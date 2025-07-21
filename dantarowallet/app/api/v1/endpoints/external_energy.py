"""
외부 에너지 공급자 API 엔드포인트
요구사항 문서 기반 신규 구현
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Path
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import logging

from app.core.database import get_db
from app.api.deps import (
    get_current_user, 
    get_current_super_admin,
    get_current_partner_admin, 
    get_current_end_user,
    require_super_admin_or_partner_admin
)
from app.models.user import User
from app.models.partner import Partner
from app.schemas.external_energy import (
    ProvidersListResponse,
    ProviderDetailResponse,
    MarketSummaryResponse,
    CreateOrderRequest,
    CreateOrderResponse,
    OrderListResponse,
    ErrorResponse,
    EnergyProviderResponse,
    ProviderFees,
    MarketSummary,
    ProviderStatus,
    EnergyPriceResponse,
    EnergyPurchaseRequest,
    EnergyPurchaseResponse,
    EnergyBalanceResponse,
    ProviderHealthCheck
)
from app.schemas.external_energy import OrderStatus as SchemaOrderStatus
from app.models.energy_order import OrderStatus as ModelOrderStatus
from app.services.external_energy.external_energy_service import ExternalEnergyService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/providers", response_model=ProvidersListResponse)
async def get_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    모든 활성 에너지 공급자 목록 조회
    
    - **반환**: 활성화된 모든 에너지 공급자 정보
    - **포함 데이터**: 가격, 가용성, 신뢰도, 수수료 등
    """
    try:
        service = ExternalEnergyService(db)
        providers = await service.get_providers()
        
        return ProvidersListResponse(
            success=True,
            data=providers
        )
        
    except Exception as e:
        logger.error(f"공급자 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="공급자 정보를 조회할 수 없습니다"
        )


@router.get("/providers/{provider_id}", response_model=ProviderDetailResponse)
async def get_provider_detail(
    provider_id: str = Path(..., description="공급자 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """특정 공급자의 상세 정보 조회"""
    try:
        service = ExternalEnergyService(db)
        provider = await service.get_provider_detail(provider_id)
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="공급자를 찾을 수 없습니다"
            )
        
        return ProviderDetailResponse(
            success=True,
            data=provider
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"공급자 상세 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="공급자 상세 정보를 조회할 수 없습니다"
        )


@router.post("/providers/{provider_id}/refresh")
async def refresh_provider(
    provider_id: str = Path(..., description="공급자 ID"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """공급자 정보 새로고침"""
    try:
        service = ExternalEnergyService(db)
        
        # 백그라운드에서 공급자 정보 업데이트
        background_tasks.add_task(service.update_provider_data, provider_id)
        
        return {"success": True, "message": "공급자 정보 업데이트가 요청되었습니다"}
        
    except Exception as e:
        logger.error(f"공급자 새로고침 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="공급자 정보를 새로고침할 수 없습니다"
        )


@router.get("/market/summary", response_model=MarketSummaryResponse)
async def get_market_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """시장 요약 정보 조회"""
    try:
        service = ExternalEnergyService(db)
        summary = await service.get_market_summary()
        
        return MarketSummaryResponse(
            success=True,
            data=summary
        )
        
    except Exception as e:
        logger.error(f"시장 요약 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="시장 정보를 조회할 수 없습니다"
        )


@router.get("/market/prices/realtime")
async def get_realtime_prices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """실시간 가격 정보 조회"""
    try:
        service = ExternalEnergyService(db)
        prices = await service.get_realtime_prices()
        
        return {
            "success": True,
            "data": prices,
            "lastUpdated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"실시간 가격 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="실시간 가격 정보를 조회할 수 없습니다"
        )


@router.post("/orders", response_model=CreateOrderResponse)
async def create_order(
    order_request: CreateOrderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """새로운 에너지 주문 생성"""
    try:
        service = ExternalEnergyService(db)
        order = await service.create_order(order_request, str(current_user.id))
        
        return CreateOrderResponse(
            success=True,
            data=order
        )
        
    except Exception as e:
        logger.error(f"주문 생성 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문을 생성할 수 없습니다"
        )


@router.get("/orders/{order_id}")
async def get_order_detail(
    order_id: str = Path(..., description="주문 ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """주문 상세 정보 조회"""
    try:
        service = ExternalEnergyService(db)
        order = await service.get_order_detail(order_id, str(current_user.id))
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="주문을 찾을 수 없습니다"
            )
        
        return {
            "success": True,
            "data": order
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"주문 상세 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 정보를 조회할 수 없습니다"
        )


@router.get("/orders", response_model=OrderListResponse)
async def get_orders(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 개수"),
    status_filter: Optional[SchemaOrderStatus] = Query(None, description="상태 필터"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자 주문 목록 조회"""
    try:
        # 스키마 OrderStatus를 모델 OrderStatus로 변환
        model_status_filter = None
        if status_filter:
            model_status_filter = ModelOrderStatus(status_filter.value)
        
        service = ExternalEnergyService(db)
        orders = await service.get_user_orders(
            user_id=str(current_user.id),
            page=page,
            limit=limit,
            status_filter=model_status_filter
        )
        
        return OrderListResponse(
            success=True,
            data=orders,
            pagination={
                "page": page,
                "limit": limit,
                "total": len(orders)  # TODO: 실제 총 개수 계산
            }
        )
        
    except Exception as e:
        logger.error(f"주문 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 목록을 조회할 수 없습니다"
        )


@router.get("/test")
async def test_endpoint():
    """외부 에너지 API 테스트 엔드포인트 (인증 불필요)"""
    return {
        "message": "External Energy API is working",
        "providers": ["tronnrg", "energytron"],
        "status": "success",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/providers/list")
async def get_providers_list():
    """공급업체 목록 간단 조회 (인증 불필요)"""
    try:
        # 간단한 SQLite 연결로 공급업체 목록 조회
        import sqlite3
        conn = sqlite3.connect("dev.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id, 
                name, 
                status, 
                reliability_score, 
                min_order_size, 
                max_order_size,
                trading_fee,
                withdrawal_fee
            FROM energy_providers 
            WHERE status = 'ONLINE'
            ORDER BY reliability_score DESC
        """)
        providers = cursor.fetchall()
        
        # 각 공급업체의 최신 가격 정보도 조회
        provider_data = []
        for provider in providers:
            cursor.execute("""
                SELECT price, available_energy 
                FROM energy_prices 
                WHERE provider_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (provider[0],))
            price_info = cursor.fetchone()
            
            provider_info = {
                "id": provider[0],
                "name": provider[1], 
                "status": provider[2],
                "reliability": provider[3],
                "min_order": provider[4],
                "max_order": provider[5],
                "trading_fee": provider[6],
                "withdrawal_fee": provider[7]
            }
            
            if price_info:
                provider_info.update({
                    "current_price": price_info[0],
                    "available_energy": price_info[1]
                })
            
            provider_data.append(provider_info)
        
        conn.close()
        
        return {
            "success": True,
            "count": len(provider_data),
            "data": provider_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# === 다중 공급업체 관련 새로운 엔드포인트들 ===

@router.get("/providers/prices", response_model=dict)
async def get_all_provider_prices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    모든 공급업체의 현재 가격 정보 조회
    
    - **반환**: 각 공급업체별 가격 정보
    - **용도**: 가격 비교 및 최적 공급업체 선택
    """
    try:
        service = ExternalEnergyService(db)
        prices = await service.get_all_provider_prices()
        
        return {
            "success": True,
            "data": prices,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all provider prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider prices: {str(e)}"
        )


@router.get("/providers/best-price")
async def find_best_price(
    energy_amount: int = Query(..., gt=0, description="필요한 에너지 양"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    지정된 에너지 양에 대한 최적 가격 공급업체 찾기
    
    - **energy_amount**: 필요한 에너지 양
    - **반환**: 최적 가격 제공 공급업체 정보
    """
    try:
        service = ExternalEnergyService(db)
        best_option = await service.find_best_price(energy_amount)
        
        if not best_option:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No providers available for the requested amount"
            )
        
        return {
            "success": True,
            "data": best_option,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding best price: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find best price: {str(e)}"
        )


@router.post("/purchase/multi-provider")
async def purchase_energy_multi_provider(
    energy_amount: int = Query(..., gt=0, description="구매할 에너지 양"),
    target_address: str = Query(..., description="에너지를 받을 트론 주소"),
    preferred_provider: Optional[str] = Query(None, description="선호하는 공급업체 (선택사항)"),
    auto_distribute: bool = Query(False, description="파트너에게 자동 분배 여부"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    다중 공급업체를 고려한 스마트 에너지 구매
    
    - **energy_amount**: 구매할 에너지 양
    - **target_address**: 에너지를 받을 주소
    - **preferred_provider**: 선호 공급업체 (미지정시 최적 가격 자동 선택)
    - **auto_distribute**: 파트너 자동 분배 여부
    """
    try:
        service = ExternalEnergyService(db)
        
        result = await service.purchase_energy_multi_provider(
            energy_amount=energy_amount,
            target_address=target_address,
            preferred_provider=preferred_provider,
            auto_distribute=auto_distribute
        )
        
        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in multi-provider purchase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Purchase failed: {str(e)}"
        )


@router.get("/providers/health")
async def check_all_providers_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    모든 공급업체의 상태 확인
    
    - **반환**: 각 공급업체별 상태 정보 (응답시간, 가용성 등)
    - **용도**: 시스템 모니터링 및 장애 감지
    """
    try:
        service = ExternalEnergyService(db)
        health_status = await service.check_all_provider_health()
        
        return {
            "success": True,
            "data": health_status,
            "overall_status": "healthy" if all(
                status["is_healthy"] for status in health_status.values()
            ) else "degraded",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking providers health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/providers/{provider_name}/prices")
async def get_provider_specific_prices(
    provider_name: str = Path(..., description="공급업체 이름 (tronnrg, energytron 등)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 공급업체의 가격 정보 조회
    
    - **provider_name**: 공급업체 이름
    - **반환**: 해당 공급업체의 상세 가격 정보
    """
    try:
        service = ExternalEnergyService(db)
        
        # 특정 공급업체 서비스 가져오기
        provider_service = service._get_provider_service(provider_name)
        prices = await provider_service.get_current_prices()
        
        return {
            "success": True,
            "data": prices.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting {provider_name} prices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get {provider_name} prices: {str(e)}"
        )


@router.get("/providers/{provider_name}/balance")
async def get_provider_balance(
    provider_name: str = Path(..., description="공급업체 이름"),
    address: str = Query(..., description="조회할 트론 주소"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 공급업체에서 주소별 에너지 잔액 조회
    
    - **provider_name**: 공급업체 이름
    - **address**: 조회할 트론 주소
    - **반환**: 해당 주소의 에너지 잔액 정보
    """
    try:
        service = ExternalEnergyService(db)
        
        # 특정 공급업체 서비스 가져오기
        provider_service = service._get_provider_service(provider_name)
        balance = await provider_service.check_balance(address)
        
        return {
            "success": True,
            "data": balance.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting {provider_name} balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get {provider_name} balance: {str(e)}"
        )


# === 사용자 유형별 인증을 사용하는 예시 엔드포인트들 ===

@router.get("/admin/providers", response_model=ProvidersListResponse)
async def get_providers_admin(
    current_user: User = Depends(get_current_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    관리자 전용 공급업체 관리
    슈퍼어드민만 접근 가능
    """
    try:
        service = ExternalEnergyService(db)
        providers = await service.get_providers()
        
        return ProvidersListResponse(
            success=True,
            data=providers
        )
        
    except Exception as e:
        logger.error(f"Admin providers fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch providers: {str(e)}"
        )


@router.post("/partner/purchase")
async def purchase_energy_partner(
    energy_amount: int = Query(..., gt=0, description="구매할 에너지 양"),
    target_address: str = Query(..., description="에너지를 받을 트론 주소"),
    user_partner: tuple[User, Partner] = Depends(get_current_partner_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    파트너어드민 전용 에너지 구매
    파트너사 관리자만 접근 가능
    """
    user, partner = user_partner
    
    try:
        service = ExternalEnergyService(db)
        
        result = await service.purchase_energy_multi_provider(
            energy_amount=energy_amount,
            target_address=target_address,
            auto_distribute=True,
            partner_allocation={str(partner.id): energy_amount}
        )
        
        return {
            "success": True,
            "data": result,
            "partner_info": {
                "id": partner.id,
                "name": partner.name,
                "user": user.email
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Partner energy purchase error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Purchase failed: {str(e)}"
        )


@router.get("/user/balance")
async def get_user_energy_balance(
    address: str = Query(..., description="조회할 트론 주소"),
    current_user: User = Depends(get_current_end_user),
    db: AsyncSession = Depends(get_db)
):
    """
    일반 사용자 전용 에너지 잔액 조회
    최종 고객만 접근 가능
    """
    try:
        service = ExternalEnergyService(db)
        
        # 여러 공급업체에서 잔액 조회
        balances = {}
        for provider_name in ["tronnrg", "energytron"]:
            try:
                provider_service = service._get_provider_service(provider_name)
                balance = await provider_service.check_balance(address)
                balances[provider_name] = balance.dict()
            except Exception as e:
                logger.warning(f"Failed to get balance from {provider_name}: {e}")
                balances[provider_name] = None
        
        return {
            "success": True,
            "data": {
                "address": address,
                "user_email": current_user.email,
                "balances": balances
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"User balance check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Balance check failed: {str(e)}"
        )


@router.get("/management/system-status")
async def get_system_status(
    user_partner: tuple[User, Optional[Partner]] = Depends(require_super_admin_or_partner_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    시스템 상태 관리
    슈퍼어드민 또는 파트너어드민만 접근 가능
    """
    user, partner = user_partner
    
    try:
        service = ExternalEnergyService(db)
        health_status = await service.check_all_provider_health()
        
        response_data = {
            "success": True,
            "data": health_status,
            "admin_info": {
                "user_email": user.email,
                "is_super_admin": bool(user.is_admin),
                "partner_name": partner.name if partner else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return response_data
        
    except Exception as e:
        logger.error(f"System status check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System status check failed: {str(e)}"
        )
