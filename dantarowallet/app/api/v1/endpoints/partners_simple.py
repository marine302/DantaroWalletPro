from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter()

# 목 데이터
MOCK_PARTNERS = [
    {
        "id": str(uuid.uuid4()),
        "name": "DantaroExchange",
        "domain": "dantaro.exchange",
        "contact_email": "admin@dantaro.exchange",
        "status": "active",
        "created_at": "2025-01-15T10:30:00Z",
        "last_activity": "2025-07-17T14:22:00Z",
        "total_transactions": 1247,
        "total_volume": "125,847.50",
        "fee_rate": 0.25
    },
    {
        "id": str(uuid.uuid4()),
        "name": "CryptoLink Korea",
        "domain": "cryptolink.kr",
        "contact_email": "support@cryptolink.kr", 
        "status": "active",
        "created_at": "2025-02-20T09:15:00Z",
        "last_activity": "2025-07-17T12:45:00Z",
        "total_transactions": 892,
        "total_volume": "89,234.75",
        "fee_rate": 0.30
    },
    {
        "id": str(uuid.uuid4()),
        "name": "TronWallet Pro",
        "domain": "tronwallet.pro",
        "contact_email": "info@tronwallet.pro",
        "status": "pending",
        "created_at": "2025-07-10T16:20:00Z",
        "last_activity": "2025-07-16T18:30:00Z",
        "total_transactions": 23,
        "total_volume": "2,847.20",
        "fee_rate": 0.20
    },
    {
        "id": str(uuid.uuid4()),
        "name": "BlockChain Solutions",
        "domain": "blockchain-sol.com",
        "contact_email": "contact@blockchain-sol.com",
        "status": "suspended",
        "created_at": "2025-03-05T11:45:00Z",
        "last_activity": "2025-07-10T09:15:00Z",
        "total_transactions": 456,
        "total_volume": "45,672.30",
        "fee_rate": 0.35
    }
]

@router.get("/")
async def get_partners(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
):
    """파트너 목록 조회"""
    try:
        partners = MOCK_PARTNERS.copy()
        
        # 상태 필터링
        if status:
            partners = [p for p in partners if p["status"] == status]
            
        # 페이지네이션
        total = len(partners)
        partners = partners[skip:skip + limit]
        
        return {
            "items": partners,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{partner_id}")
async def get_partner(partner_id: str):
    """특정 파트너 상세 조회"""
    partner = next((p for p in MOCK_PARTNERS if p["id"] == partner_id), None)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner

@router.post("/partners")
async def create_partner(partner_data: dict):
    """새 파트너 생성"""
    new_partner = {
        "id": str(uuid.uuid4()),
        "name": partner_data.get("name"),
        "domain": partner_data.get("domain"),
        "contact_email": partner_data.get("contact_email"),
        "status": "pending",
        "created_at": datetime.now().isoformat() + "Z",
        "last_activity": datetime.now().isoformat() + "Z",
        "total_transactions": 0,
        "total_volume": "0.00",
        "fee_rate": partner_data.get("fee_rate", 0.25)
    }
    
    MOCK_PARTNERS.append(new_partner)
    return new_partner

@router.put("/partners/{partner_id}")
async def update_partner(partner_id: str, partner_data: dict):
    """파트너 정보 업데이트"""
    partner_index = next((i for i, p in enumerate(MOCK_PARTNERS) if p["id"] == partner_id), None)
    if partner_index is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    # 업데이트 가능한 필드들
    updatable_fields = ["name", "domain", "contact_email", "status", "fee_rate"]
    for field in updatable_fields:
        if field in partner_data:
            MOCK_PARTNERS[partner_index][field] = partner_data[field]
    
    return MOCK_PARTNERS[partner_index]

@router.delete("/partners/{partner_id}")
async def delete_partner(partner_id: str):
    """파트너 삭제"""
    partner_index = next((i for i, p in enumerate(MOCK_PARTNERS) if p["id"] == partner_id), None)
    if partner_index is None:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    deleted_partner = MOCK_PARTNERS.pop(partner_index)
    return {"message": "Partner deleted successfully", "partner": deleted_partner}
