"""
에너지 풀 관리 스키마
"""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from app.models.energy_pool import EnergySourceType


class EnergyPoolBase(BaseModel):
    source_type: EnergySourceType
    wallet_address: str = Field(..., max_length=64)
    total_energy: Decimal = Field(default=0, ge=0)
    available_energy: Decimal = Field(default=0, ge=0)
    is_active: bool = True
    memo: Optional[str] = Field(None, max_length=255)


class EnergyPoolCreate(EnergyPoolBase):
    pass


class EnergyPoolUpdate(BaseModel):
    total_energy: Optional[Decimal] = Field(None, ge=0)
    available_energy: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    memo: Optional[str] = Field(None, max_length=255)


class EnergyPoolResponse(EnergyPoolBase):
    id: int
    created_at: str
    updated_at: str
    last_updated: str

    class Config:
        from_attributes = True


class EnergyAllocationRequest(BaseModel):
    source_id: int
    amount: Decimal = Field(..., gt=0)
    partner_wallet: str = Field(..., max_length=64)


class EnergyAllocationResponse(BaseModel):
    success: bool
    message: str


class EnergyCostCalculation(BaseModel):
    energy_amount: Decimal
    source_type: str
    base_cost: Decimal
    saas_fee: Decimal
    total_cost: Decimal
    margin_rate: Decimal
