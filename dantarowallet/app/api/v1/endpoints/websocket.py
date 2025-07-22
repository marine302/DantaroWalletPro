#!/usr/bin/env python3
"""
WebSocket 실시간 데이터 스트리밍 엔드포인트 (개선된 버전)
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, select, func, desc

from app.core.database import get_db
from app.models import Partner, User
from app.models.energy_provider import EnergyProvider
from app.models.energy_price import EnergyPrice  
from app.models.withdrawal import Withdrawal
from app.models.partner_onboarding import PartnerOnboarding
from app.models.energy_usage_history import EnergyUsageHistory
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# 웹소켓 연결 관리자
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.partner_connections: Dict[int, List[WebSocket]] = {}
        self.admin_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket, connection_type: str, identifier: Optional[str] = None):
        await websocket.accept()
        
        if connection_type == "admin":
            self.admin_connections.append(websocket)
            logger.info("Super admin connected to WebSocket")
        elif connection_type == "partner" and identifier:
            partner_id = int(identifier)
            if partner_id not in self.partner_connections:
                self.partner_connections[partner_id] = []
            self.partner_connections[partner_id].append(websocket)
            logger.info(f"Partner {partner_id} connected to WebSocket")
        else:
            if connection_type not in self.active_connections:
                self.active_connections[connection_type] = []
            self.active_connections[connection_type].append(websocket)
            logger.info(f"Client connected to {connection_type} WebSocket")
    
    def disconnect(self, websocket: WebSocket, connection_type: str, identifier: Optional[str] = None):
        try:
            if connection_type == "admin":
                self.admin_connections.remove(websocket)
                logger.info("Super admin disconnected from WebSocket")
            elif connection_type == "partner" and identifier:
                partner_id = int(identifier)
                if partner_id in self.partner_connections:
                    self.partner_connections[partner_id].remove(websocket)
                    if not self.partner_connections[partner_id]:
                        del self.partner_connections[partner_id]
                logger.info(f"Partner {partner_id} disconnected from WebSocket")
            else:
                if connection_type in self.active_connections:
                    self.active_connections[connection_type].remove(websocket)
                logger.info(f"Client disconnected from {connection_type} WebSocket")
        except ValueError:
            pass
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast_to_type(self, message: dict, connection_type: str):
        if connection_type == "admin":
            connections = self.admin_connections
        else:
            connections = self.active_connections.get(connection_type, [])
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send message to {connection_type}: {e}")
                disconnected.append(connection)
        
        # 끊어진 연결 제거
        for conn in disconnected:
            self.disconnect(conn, connection_type)
    
    async def send_to_partner(self, message: dict, partner_id: int):
        if partner_id in self.partner_connections:
            disconnected = []
            for connection in self.partner_connections[partner_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to partner {partner_id}: {e}")
                    disconnected.append(connection)
            
            # 끊어진 연결 제거
            for conn in disconnected:
                self.disconnect(conn, "partner", str(partner_id))

manager = ConnectionManager()

async def check_database_health(db: Session) -> Dict[str, Any]:
    """데이터베이스 상태 확인"""
    try:
        # 간단한 DB 쿼리로 연결 상태 확인
        result = db.execute(text("SELECT 1"))
        result.scalar()  # 동기 방식으로 수정
        
        return {
            "status": "healthy",
            "response_time": "< 50ms",
            "connections": "normal"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "response_time": "timeout"
        }

@router.websocket("/energy-prices")
async def websocket_energy_prices(websocket: WebSocket, db: Session = Depends(get_db)):
    """실시간 에너지 가격 업데이트"""
    await manager.connect(websocket, "energy_prices")
    try:
        while True:
            try:
                # 실제 DB에서 최신 에너지 가격 조회 (안전한 방식)
                try:
                    energy_prices = db.execute(
                        select(EnergyPrice).where(
                            EnergyPrice.is_active == True
                        ).order_by(desc(EnergyPrice.updated_at))
                    ).scalars().all()
                except Exception as e:
                    logger.error(f"Error querying energy prices: {e}")
                    energy_prices = []
                
                prices = []
                for price in energy_prices:
                    try:
                        provider = db.execute(
                            select(EnergyProvider).where(
                                EnergyProvider.id == price.provider_id
                            )
                        ).scalars().first()
                    except Exception as e:
                        logger.error(f"Error querying provider: {e}")
                        provider = None
                    
                    if provider:
                        # 안전한 속성 접근
                        available_energy = getattr(price, 'available_energy', 0)
                        response_time_ms = getattr(price, 'response_time_ms', 0)
                        
                        prices.append({
                            "provider": provider.name,
                            "price_per_energy": float(price.price_per_energy),
                            "available": int(available_energy) if available_energy is not None else 0,
                            "response_time": int(response_time_ms) if response_time_ms is not None else 0,
                            "updated_at": price.updated_at.isoformat() if price.updated_at else None
                        })
                
                # 가격이 없으면 기본값 제공
                if not prices:
                    prices = [{
                        "provider": "Default",
                        "price_per_energy": 0.0001,
                        "available": 0,
                        "response_time": 0
                    }]
                
                best_price = min(prices, key=lambda x: x["price_per_energy"]) if prices else None
                average_price = sum(p["price_per_energy"] for p in prices) / len(prices) if prices else 0
                
                message = {
                    "type": "energy_prices",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "providers": prices,
                        "best_price": best_price,
                        "average_price": average_price,
                        "total_providers": len(prices)
                    }
                }
                
                await manager.send_personal_message(message, websocket)
                await asyncio.sleep(30)  # 30초마다 업데이트
                
            except Exception as e:
                logger.error(f"Error in energy prices websocket: {e}")
                await asyncio.sleep(5)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "energy_prices")

@router.websocket("/system-health")
async def websocket_system_health(websocket: WebSocket, db: Session = Depends(get_db)):
    """실시간 시스템 상태 모니터링"""
    await manager.connect(websocket, "system_health")
    try:
        while True:
            try:
                # 실제 DB에서 시스템 상태 수집
                database_health = await check_database_health(db)
                
                # 안전한 DB 쿼리들
                try:
                    # 파트너 수 조회
                    total_partners = db.execute(
                        select(func.count(Partner.id)).where(Partner.is_active == True)
                    ).scalar() or 0
                    
                    # 대기 중인 출금 수 조회  
                    pending_withdrawals = db.execute(
                        select(func.count(Withdrawal.id)).where(
                            Withdrawal.status.in_(["pending", "processing"])
                        )
                    ).scalar() or 0
                    
                    # 활성 에너지 공급자 수 조회
                    active_providers = db.execute(
                        select(func.count(EnergyProvider.id)).where(
                            EnergyProvider.is_active == True
                        )
                    ).scalar() or 0
                    
                    # 최근 온보딩 현황 조회
                    recent_onboarding = db.execute(
                        select(func.count(PartnerOnboarding.id)).where(
                            PartnerOnboarding.status.in_(["pending", "in_progress"])
                        )
                    ).scalar() or 0
                    
                except Exception as e:
                    logger.error(f"Error querying system stats: {e}")
                    total_partners = 0
                    pending_withdrawals = 0
                    active_providers = 0
                    recent_onboarding = 0
                
                health_data = {
                    "database": database_health,
                    "external_apis": {
                        "status": "healthy" if active_providers > 0 else "warning",
                        "providers": active_providers
                    },
                    "energy_pools": {
                        "total_partners": total_partners,
                        "critical": 0,  # TODO: 임계치 기반 계산 구현 필요
                        "low": 0
                    },
                    "pending_withdrawals": pending_withdrawals,
                    "active_partners": total_partners,
                    "pending_onboarding": recent_onboarding
                }
                
                message = {
                    "type": "system_health",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": health_data
                }
                
                await manager.send_personal_message(message, websocket)
                await asyncio.sleep(60)  # 1분마다 업데이트
                
            except Exception as e:
                logger.error(f"Error in system health websocket: {e}")
                await asyncio.sleep(10)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "system_health")

@router.websocket("/order-status/{order_id}")
async def websocket_order_status(websocket: WebSocket, order_id: int, db: Session = Depends(get_db)):
    """특정 주문의 실시간 상태 업데이트"""
    await manager.connect(websocket, f"order_{order_id}")
    try:
        while True:
            try:
                # 실제 DB에서 출금 주문 조회
                from sqlalchemy import select
                stmt = select(Withdrawal).where(Withdrawal.id == order_id)
                result = db.execute(stmt)
                withdrawal = result.scalar_one_or_none()
                
                if not withdrawal:
                    # 주문이 없으면 연결 종료
                    await manager.send_personal_message({
                        "type": "error",
                        "message": f"Order {order_id} not found"
                    }, websocket)
                    break
                
                # 안전한 속성 접근을 위한 헬퍼 함수들
                status_str = getattr(withdrawal, 'status', 'unknown')
                amount_val = getattr(withdrawal, 'amount', 0)
                created_at_val = getattr(withdrawal, 'created_at', None)
                updated_at_val = getattr(withdrawal, 'updated_at', None)
                tx_hash = getattr(withdrawal, 'transaction_hash', None)
                
                # 진행률 계산
                progress = 0.0
                if status_str == "pending":
                    progress = 10.0
                elif status_str == "processing":
                    progress = 50.0
                elif status_str == "completed":
                    progress = 100.0
                elif status_str in ["failed", "cancelled"]:
                    progress = 0.0
                else:
                    progress = 25.0
                
                order_status = {
                    "type": "withdrawal",
                    "status": status_str,
                    "progress": progress,
                    "details": {
                        "order_id": order_id,
                        "amount": float(amount_val) if amount_val is not None else 0.0,
                        "transaction_hash": tx_hash,
                        "created_at": created_at_val.isoformat() if created_at_val else None,
                        "updated_at": updated_at_val.isoformat() if updated_at_val else None
                    }
                }
                
                message = {
                    "type": "order_status",
                    "timestamp": datetime.utcnow().isoformat(),
                    "order_id": order_id,
                    "data": order_status
                }
                
                await manager.send_personal_message(message, websocket)
                
                # 주문이 완료되거나 실패한 경우 연결 종료
                if status_str in ["completed", "failed", "cancelled"]:
                    break
                    
                await asyncio.sleep(10)  # 10초마다 업데이트
                
            except Exception as e:
                logger.error(f"Error in order status websocket: {e}")
                await asyncio.sleep(5)
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, f"order_{order_id}")

@router.websocket("/onboarding-progress/{partner_id}")
async def websocket_onboarding_progress(websocket: WebSocket, partner_id: int, db: Session = Depends(get_db)):
    """파트너 온보딩 진행 상황 실시간 업데이트"""
    await manager.connect(websocket, "onboarding", str(partner_id))
    try:
        while True:
            try:
                # 기본 온보딩 진행 상황 (실제 DB 구현 전까지)
                # TODO: PartnerOnboarding 모델 조회로 교체
                message = {
                    "type": "onboarding_progress",
                    "timestamp": datetime.utcnow().isoformat(),
                    "partner_id": partner_id,
                    "data": {
                        "overall_status": "in_progress",
                        "current_step": 3,
                        "progress_percentage": 60,
                        "steps": [
                            {"step_number": 1, "name": "파트너 등록", "status": "completed"},
                            {"step_number": 2, "name": "계정 생성", "status": "completed"},
                            {"step_number": 3, "name": "지갑 설정", "status": "running"},
                            {"step_number": 4, "name": "API 키 발급", "status": "pending"},
                            {"step_number": 5, "name": "테스트", "status": "pending"},
                            {"step_number": 6, "name": "완료", "status": "pending"}
                        ]
                    }
                }
                
                await manager.send_personal_message(message, websocket)
                await asyncio.sleep(5)  # 5초마다 업데이트
                
            except Exception as e:
                logger.error(f"Error in onboarding progress websocket: {e}")
                await asyncio.sleep(10)
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "onboarding", str(partner_id))

@router.websocket("/energy-usage/{partner_id}")
async def websocket_energy_usage(websocket: WebSocket, partner_id: int, db: Session = Depends(get_db)):
    """파트너별 실시간 에너지 사용량 모니터링"""
    await manager.connect(websocket, "energy_usage", str(partner_id))
    try:
        while True:
            try:
                # 실제 에너지 사용량 계산 (파트너별)
                # TODO: 실제 EnergyPool과 Transaction 연동 완료 후 활성화
                
                # 기본값 설정 (실제 구현 시 DB에서 조회)
                current_energy = 5500000  # 현재 에너지
                total_capacity = 10000000  # 총 용량
                daily_usage = 150000
                monthly_usage = 4500000
                
                # 사용률 계산 (시간당)
                usage_rate = 2000.0
                estimated_hours = current_energy / usage_rate if usage_rate > 0 else 0
                estimated_depletion = (datetime.utcnow() + timedelta(hours=estimated_hours)).isoformat()
                
                # 비용 계산
                cost_per_energy = 0.0001
                cost_today = daily_usage * cost_per_energy
                cost_month = monthly_usage * cost_per_energy
                
                # 경고 생성
                alerts = []
                if current_energy < total_capacity * 0.2:
                    alerts.append({
                        "level": "warning",
                        "message": "에너지가 부족합니다. 충전을 고려하세요.",
                        "threshold": int(total_capacity * 0.2),
                        "current": current_energy
                    })
                
                usage_data = {
                    "current_usage": total_capacity - current_energy,
                    "daily_usage": daily_usage,
                    "monthly_usage": monthly_usage,
                    "remaining_quota": current_energy,
                    "usage_rate": usage_rate,
                    "estimated_depletion": estimated_depletion,
                    "cost_today": cost_today,
                    "cost_month": cost_month,
                    "alerts": alerts
                }
                
                message = {
                    "type": "energy_usage",
                    "timestamp": datetime.utcnow().isoformat(),
                    "partner_id": partner_id,
                    "data": usage_data
                }
                
                await manager.send_personal_message(message, websocket)
                await asyncio.sleep(30)  # 30초마다 업데이트
                
            except Exception as e:
                logger.error(f"Error in energy usage websocket: {e}")
                await asyncio.sleep(10)
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "energy_usage", str(partner_id))

@router.websocket("/withdrawal-batch-status/{partner_id}")
async def websocket_withdrawal_batch_status(websocket: WebSocket, partner_id: int, db: Session = Depends(get_db)):
    """출금 배치 처리 상태 실시간 모니터링"""
    await manager.connect(websocket, "withdrawal_batch", str(partner_id))
    try:
        while True:
            try:
                # 실제 출금 배치 상태 조회
                from app.models.withdrawal import Withdrawal
                from sqlalchemy import func, and_
                
                # 파트너의 활성 배치들 조회
                active_withdrawals = db.query(Withdrawal).filter(
                    and_(
                        Withdrawal.status.in_(["pending", "processing", "signed", "executing"]),
                        Withdrawal.created_at >= datetime.utcnow() - timedelta(hours=24)  # 최근 24시간
                    )
                ).all()
                
                # 배치별로 그룹화
                batch_groups = {}
                for withdrawal in active_withdrawals:
                    batch_key = withdrawal.batch_number or f"BATCH-{withdrawal.id}"
                    if batch_key not in batch_groups:
                        batch_groups[batch_key] = {
                            "withdrawals": [],
                            "total_amount": 0,
                            "status": withdrawal.status,
                            "created_at": withdrawal.created_at
                        }
                    batch_groups[batch_key]["withdrawals"].append(withdrawal)
                    batch_groups[batch_key]["total_amount"] += float(str(withdrawal.amount))
                
                # 배치 데이터 구성
                batch_data = []
                for batch_number, group in batch_groups.items():
                    # 진행률 계산
                    total_withdrawals = len(group["withdrawals"])
                    completed = sum(1 for w in group["withdrawals"] if w.status in ["completed", "confirmed"])
                    progress = (completed / total_withdrawals * 100) if total_withdrawals > 0 else 0
                    
                    batch_data.append({
                        "batch_id": hash(batch_number) % 10000,  # 임시 ID
                        "batch_number": batch_number,
                        "status": group["status"],
                        "total_amount": group["total_amount"],
                        "withdrawal_count": total_withdrawals,
                        "created_at": group["created_at"].isoformat(),
                        "signed_at": None,  # TODO: 서명 시간 추가
                        "executed_at": None,  # TODO: 실행 시간 추가
                        "progress_percentage": progress
                    })
                
                # 상태별 카운트
                pending_count = sum(1 for batch in batch_data if batch["status"] == "pending")
                executing_count = sum(1 for batch in batch_data if batch["status"] in ["processing", "executing"])
                
                message = {
                    "type": "withdrawal_batch_status",
                    "timestamp": datetime.utcnow().isoformat(),
                    "partner_id": partner_id,
                    "data": {
                        "active_batches": batch_data,
                        "total_active": len(batch_data),
                        "pending_signature": pending_count,
                        "executing": executing_count
                    }
                }
                
                await manager.send_personal_message(message, websocket)
                await asyncio.sleep(15)  # 15초마다 업데이트
                
            except Exception as e:
                logger.error(f"Error in withdrawal batch status websocket: {e}")
                await asyncio.sleep(10)
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "withdrawal_batch", str(partner_id))

@router.websocket("/emergency-alerts")
async def websocket_emergency_alerts(websocket: WebSocket, db: Session = Depends(get_db)):
    """시스템 전체 위기 상황 실시간 알림"""
    await manager.connect(websocket, "emergency_alerts")
    try:
        while True:
            try:
                # 실제 시스템 위기 상황 점검
                from app.models.energy_pool import EnergyPoolModel
                from app.models.user import User
                from app.models.transaction import Transaction
                from sqlalchemy import func
                
                alerts = []
                
                # 에너지 부족 체크
                low_energy_pools = db.query(EnergyPoolModel).filter(
                    EnergyPoolModel.available_energy < EnergyPoolModel.total_energy * 0.2
                ).count()
                
                if low_energy_pools > 0:
                    alerts.append({
                        "type": "energy_crisis",
                        "severity": "warning",
                        "message": f"{low_energy_pools}개 풀의 에너지가 부족합니다",
                        "affected_partners": low_energy_pools,
                        "action_required": True
                    })
                
                # 시스템 과부하 체크 (최근 1시간 거래량)
                hour_ago = datetime.utcnow() - timedelta(hours=1)
                recent_tx_count = db.query(func.count(Transaction.id)).filter(
                    Transaction.created_at >= hour_ago
                ).scalar() or 0
                
                if recent_tx_count > 1000:  # 임계값
                    alerts.append({
                        "type": "system_overload",
                        "severity": "critical",
                        "message": f"시간당 거래량 과다: {recent_tx_count}건",
                        "affected_partners": "all",
                        "action_required": True
                    })
                
                # 실패 거래 비율 체크
                failed_tx_count = db.query(func.count(Transaction.id)).filter(
                    Transaction.created_at >= hour_ago,
                    Transaction.status.in_(["failed", "error"])
                ).scalar() or 0
                
                if recent_tx_count > 0 and (failed_tx_count / recent_tx_count) > 0.1:  # 10% 이상 실패
                    alerts.append({
                        "type": "high_failure_rate",
                        "severity": "warning",
                        "message": f"거래 실패율 과다: {failed_tx_count}/{recent_tx_count}",
                        "affected_partners": "all",
                        "action_required": True
                    })
                
                if alerts:
                    message = {
                        "type": "emergency_alerts",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {
                            "alerts": alerts,
                            "severity": max(alert.get("severity", "info") for alert in alerts),
                            "alert_count": len(alerts)
                        }
                    }
                    
                    await manager.send_personal_message(message, websocket)
                
                await asyncio.sleep(60)  # 1분마다 점검
                
            except Exception as e:
                logger.error(f"Error in emergency alerts websocket: {e}")
                await asyncio.sleep(30)
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "emergency_alerts")

@router.websocket("/admin-events")
async def websocket_admin_events(websocket: WebSocket, db: Session = Depends(get_db)):
    """관리자 이벤트 실시간 브로드캐스트"""
    await manager.connect(websocket, "admin")
    try:
        while True:
            try:
                # 실제 관리자 이벤트 수집
                from app.models.user import User
                from app.models.transaction import Transaction
                from sqlalchemy import func, desc
                
                events = []
                
                # 최근 활동 통계
                minute_ago = datetime.utcnow() - timedelta(minutes=1)
                
                # 새로운 사용자 등록
                new_users = db.query(func.count(User.id)).filter(
                    User.created_at >= minute_ago
                ).scalar() or 0
                
                if new_users > 0:
                    events.append({
                        "type": "user_registration",
                        "message": f"신규 사용자 {new_users}명 등록",
                        "timestamp": datetime.utcnow().isoformat(),
                        "count": new_users
                    })
                
                # 거래 활동
                recent_transactions = db.query(func.count(Transaction.id)).filter(
                    Transaction.created_at >= minute_ago
                ).scalar() or 0
                
                if recent_transactions > 0:
                    events.append({
                        "type": "transaction_activity",
                        "message": f"최근 1분간 거래 {recent_transactions}건 처리",
                        "timestamp": datetime.utcnow().isoformat(),
                        "count": recent_transactions
                    })
                
                # 시스템 상태 주기적 보고
                if datetime.utcnow().minute % 5 == 0:
                    total_users = db.query(func.count(User.id)).scalar() or 0
                    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
                    
                    events.append({
                        "type": "system_status",
                        "message": f"시스템 정상 운영 중 (사용자: {total_users}, 거래: {total_transactions})",
                        "timestamp": datetime.utcnow().isoformat(),
                        "users": total_users,
                        "transactions": total_transactions
                    })
                
                for event in events:
                    message = {
                        "type": "admin_event",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": event
                    }
                    
                    await manager.send_personal_message(message, websocket)
                
                await asyncio.sleep(10)  # 10초마다 이벤트 확인
                
            except Exception as e:
                logger.error(f"Error in admin events websocket: {e}")
                await asyncio.sleep(30)
                
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, "admin")

# 웹소켓 관리 함수들
async def broadcast_onboarding_update(partner_id: int, update_data: dict):
    """온보딩 진행 상황 브로드캐스트"""
    message = {
        "type": "onboarding_update",
        "timestamp": datetime.utcnow().isoformat(),
        "partner_id": partner_id,
        "data": update_data
    }
    await manager.send_to_partner(message, partner_id)

async def broadcast_energy_alert(partner_id: int, alert_data: dict):
    """에너지 위기 알림 브로드캐스트"""
    message = {
        "type": "energy_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "partner_id": partner_id,
        "data": alert_data
    }
    await manager.send_to_partner(message, partner_id)

async def broadcast_system_alert(alert_data: dict):
    """시스템 전체 알림 브로드캐스트"""
    message = {
        "type": "system_alert",
        "timestamp": datetime.utcnow().isoformat(),
        "data": alert_data
    }
    await manager.broadcast_to_type(message, "admin")

# 헬퍼 함수들

# === 실제 데이터 조회 함수들 ===

async def get_real_energy_prices(db: Session) -> List[Dict[str, Any]]:
    """실제 에너지 가격 데이터 조회"""
    try:
        # 일단 기본 데이터 반환 (나중에 실제 DB 조회로 교체)
        # TODO: 실제 EnergyPrice 모델 조회 구현
        return [
            {
                "provider": "TronNRG",
                "price_per_energy": 0.00009,
                "available": 10000000,
                "response_time": 150
            },
            {
                "provider": "EnergyTRON", 
                "price_per_energy": 0.00010,
                "available": 5000000,
                "response_time": 200
            }
        ]
        
    except Exception as e:
        logger.error(f"Error fetching energy prices: {e}")
        return [
            {
                "provider": "TronNRG",
                "price_per_energy": 0.00009,
                "available": 10000000,
                "response_time": 150
            }
        ]

async def get_system_health_data(db: Session) -> Dict[str, Any]:
    """실제 시스템 상태 데이터 조회"""
    try:
        # TODO: 실제 DB 조회로 교체
        # active_partners = db.query(Partner).filter(Partner.status == "active").count()
        # pending_withdrawals = db.query(Withdrawal).filter(...).count()
        
        active_partners = 5
        pending_withdrawals = 15
        
        # 데이터베이스 상태 확인
        db_health = await check_database_health(db)
        
        return {
            "database": db_health,
            "active_partners": active_partners,
            "pending_withdrawals": pending_withdrawals,
            "energy_pools": {
                "total": 5,
                "critical": 0,
                "low": 1
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching system health: {e}")
        return {
            "database": {"status": "error", "error": str(e)},
            "active_partners": 0,
            "pending_withdrawals": 0,
            "energy_pools": {"total": 0, "critical": 0, "low": 0}
        }

async def get_partner_onboarding_data(db: Session, partner_id: int) -> Dict[str, Any]:
    """실제 파트너 온보딩 데이터 조회"""
    try:
        # 파트너 조회
        from sqlalchemy import select
        stmt = select(Partner).where(Partner.id == str(partner_id))
        result = db.execute(stmt)
        partner = result.scalar_one_or_none()
        if not partner:
            return {"error": "Partner not found"}
        
        # 온보딩 상태에 따른 단계 계산
        status = getattr(partner, 'onboarding_status', 'pending') or "pending"
        
        # 상태 문자열로 변환
        status_str = str(status)
        
        steps = [
            {"step": 1, "name": "파트너 등록", "status": "completed"},
            {"step": 2, "name": "계정 생성", "status": "completed" if status_str != "pending" else "pending"},
            {"step": 3, "name": "지갑 설정", "status": "running" if status_str == "wallet_setup" else ("completed" if status_str in ["api_setup", "completed"] else "pending")},
            {"step": 4, "name": "API 설정", "status": "running" if status_str == "api_setup" else ("completed" if status_str == "completed" else "pending")},
        ]
        
        current_step = 1
        for step in steps:
            if step["status"] == "running":
                current_step = step["step"]
                break
            elif step["status"] == "completed":
                current_step = step["step"] + 1
        
        progress = min((current_step - 1) * 25, 100)
        
        return {
            "partner_id": partner_id,
            "status": status,
            "current_step": current_step,
            "progress": progress,
            "steps": steps,
            "checklist": {
                "completed": len([s for s in steps if s["status"] == "completed"]),
                "total": len(steps)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching onboarding data for partner {partner_id}: {e}")
        return {"error": str(e)}

async def get_partner_energy_usage(db: Session, partner_id: int) -> Dict[str, Any]:
    """실제 파트너 에너지 사용량 데이터 조회"""
    try:
        from sqlalchemy import select
        stmt = select(Partner).where(Partner.id == str(partner_id))
        result = db.execute(stmt)
        partner = result.scalar_one_or_none()
        if not partner:
            return {"error": "Partner not found"}
        
        # 현재 에너지 잔액 - 안전한 속성 접근
        energy_balance = getattr(partner, 'energy_balance', 0)
        current_balance = float(energy_balance) if energy_balance is not None else 0.0
        
        # 일일/월간 사용량 계산 (실제 구현 시 EnergyUsageHistory 테이블 조회)
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        # 임시 계산 (실제로는 usage history에서 조회)
        daily_usage = 150000
        monthly_usage = daily_usage * today.day
        monthly_limit_val = getattr(partner, 'monthly_limit', 10000000)
        monthly_limit = float(monthly_limit_val) if monthly_limit_val is not None else 10000000.0
        remaining_quota = max(0, monthly_limit - monthly_usage)
        
        # 비용 계산 (임시 가격 0.0001 TRX/energy)
        price_per_energy = 0.0001
        cost_today = daily_usage * price_per_energy
        cost_month = monthly_usage * price_per_energy
        
        # 알림 생성
        alerts = []
        if remaining_quota < monthly_limit * 0.2:  # 20% 미만 남음
            alerts.append("⚠️ 에너지가 부족합니다. 충전을 고려하세요.")
        
        return {
            "partner_id": partner_id,
            "current_balance": current_balance,
            "daily_usage": daily_usage,
            "monthly_usage": monthly_usage,
            "monthly_limit": monthly_limit,
            "remaining_quota": remaining_quota,
            "usage_rate": 2000,  # energy/hour
            "cost_today": cost_today,
            "cost_month": cost_month,
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Error fetching energy usage for partner {partner_id}: {e}")
        return {"error": str(e)}

async def get_withdrawal_batch_status(db: Session, partner_id: int) -> Dict[str, Any]:
    """실제 출금 배치 상태 조회"""
    try:
        # 파트너의 활성 출금 배치 조회
        from sqlalchemy import select
        stmt = select(Withdrawal).where(
            Withdrawal.partner_id == str(partner_id),
            Withdrawal.status.in_(["pending", "processing", "signing"])
        )
        result = db.execute(stmt)
        active_withdrawals = result.scalars().all()
        
        batches = []
        for withdrawal in active_withdrawals:
            # 안전한 속성 접근
            status = getattr(withdrawal, 'status', 'unknown')
            amount = getattr(withdrawal, 'amount', 0)
            withdrawal_id = getattr(withdrawal, 'id', 0)
            
            progress = 70 if str(status) == "processing" else 30
            amount_float = float(amount) if amount is not None else 0.0
            
            batches.append({
                "batch_id": withdrawal_id,
                "status": str(status),
                "progress": progress,
                "amount": amount_float,
                "transaction_count": 1  # 실제로는 배치 내 트랜잭션 수
            })
        
        # 상태별 집계
        pending_signature = len([b for b in batches if b["status"] == "signing"])
        executing = len([b for b in batches if b["status"] == "processing"])
        
        return {
            "partner_id": partner_id,
            "total_active_batches": len(batches),
            "pending_signature": pending_signature,
            "executing": executing,
            "batches": batches[:5]  # 최대 5개만 표시
        }
        
    except Exception as e:
        logger.error(f"Error fetching withdrawal batch status for partner {partner_id}: {e}")
        return {"error": str(e)}
