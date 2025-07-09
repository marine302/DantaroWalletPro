# Copilot 문서 #34: 파트너사 종합 대시보드

## 목표
파트너사 운영진을 위한 올인원 관리 시스템을 구축합니다. 멀티 지갑 통합 관리 뷰, 실시간 자산 흐름 시각화, AI 기반 이상 거래 탐지, 예측 분석 및 인사이트, 자동화된 리포트 생성, 24/7 모니터링 알림 센터를 포함한 종합 대시보드를 구현합니다.

## 전제 조건
- Copilot 문서 #24-33이 완료되어 있어야 합니다
- 파트너사 시스템이 완전히 통합되어 있어야 합니다
- 실시간 데이터 처리 인프라가 구축되어 있어야 합니다
- AI/ML 모델링을 위한 데이터가 충분히 축적되어 있어야 합니다

## 상세 지시사항

### 1. 종합 대시보드 백엔드 구조

`app/services/dashboard/integrated_dashboard.py` 파일을 생성하세요:

```python
"""파트너사 종합 대시보드 서비스"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import Partner
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.services.analytics.predictive import PredictiveAnalytics
from app.services.monitoring.realtime import RealtimeMonitor
from app.services.ai.anomaly_detector import AnomalyDetector
from app.core.cache import cache_manager

class IntegratedDashboard:
    """파트너사 종합 대시보드 서비스"""
    
    def __init__(self, db: AsyncSession, partner_id: int):
        self.db = db
        self.partner_id = partner_id
        self.cache_key = f"dashboard:{partner_id}"
        self.predictive = PredictiveAnalytics()
        self.monitor = RealtimeMonitor()
        self.anomaly_detector = AnomalyDetector()
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """종합 대시보드 데이터 조회"""
        # 캐시 확인
        cached_data = await cache_manager.get(self.cache_key)
        if cached_data:
            return cached_data
        
        # 병렬 처리로 성능 최적화
        tasks = [
            self.get_wallet_overview(),
            self.get_transaction_flow(),
            self.get_energy_status(),
            self.get_user_analytics(),
            self.get_revenue_metrics(),
            self.get_risk_alerts(),
            self.get_predictions(),
            self.get_system_health()
        ]
        
        results = await asyncio.gather(*tasks)
        
        dashboard_data = {
            "wallet_overview": results[0],
            "transaction_flow": results[1],
            "energy_status": results[2],
            "user_analytics": results[3],
            "revenue_metrics": results[4],
            "risk_alerts": results[5],
            "predictions": results[6],
            "system_health": results[7],
            "last_updated": datetime.utcnow()
        }
        
        # 캐시 저장 (30초)
        await cache_manager.set(self.cache_key, dashboard_data, ttl=30)
        
        return dashboard_data
    
    async def get_wallet_overview(self) -> Dict[str, Any]:
        """멀티 지갑 통합 현황"""
        wallets = await self.db.query(Wallet).filter(
            Wallet.partner_id == self.partner_id
        ).all()
        
        total_balance = Decimal('0')
        wallet_distribution = {
            'hot': {'balance': Decimal('0'), 'percentage': 0, 'wallets': []},
            'warm': {'balance': Decimal('0'), 'percentage': 0, 'wallets': []},
            'cold': {'balance': Decimal('0'), 'percentage': 0, 'wallets': []}
        }
        
        for wallet in wallets:
            balance = await self.get_wallet_balance(wallet.address)
            total_balance += balance
            
            wallet_type = self.classify_wallet_type(wallet)
            wallet_distribution[wallet_type]['balance'] += balance
            wallet_distribution[wallet_type]['wallets'].append({
                'address': wallet.address,
                'balance': balance,
                'last_activity': wallet.last_activity,
                'transactions_24h': await self.get_wallet_transaction_count(wallet.address)
            })
        
        # 백분율 계산
        for wallet_type in wallet_distribution:
            if total_balance > 0:
                percentage = (wallet_distribution[wallet_type]['balance'] / total_balance) * 100
                wallet_distribution[wallet_type]['percentage'] = round(percentage, 2)
        
        return {
            'total_balance': total_balance,
            'total_balance_usd': await self.convert_to_usd(total_balance),
            'wallet_count': len(wallets),
            'distribution': wallet_distribution,
            'recommendations': await self.generate_wallet_recommendations(wallet_distribution)
        }
```

### 2. 실시간 자산 흐름 시각화

`app/services/dashboard/transaction_flow.py` 파일을 생성하세요:

```python
"""트랜잭션 흐름 분석 서비스"""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal

class TransactionFlowAnalyzer:
    """트랜잭션 흐름 분석기"""
    
    def __init__(self, db, partner_id: int):
        self.db = db
        self.partner_id = partner_id
    
    async def get_realtime_flow(self, timeframe: str = "1h") -> Dict:
        """실시간 트랜잭션 흐름 데이터"""
        # 시간 범위 설정
        time_delta = self.parse_timeframe(timeframe)
        start_time = datetime.utcnow() - time_delta
        
        # 트랜잭션 조회
        transactions = await self.get_recent_transactions(start_time)
        
        flow_data = {
            "inflows": [],
            "outflows": [],
            "internal_transfers": [],
            "volume_by_minute": self.calculate_volume_timeline(transactions),
            "top_addresses": self.get_top_addresses(transactions),
            "flow_pattern": self.detect_flow_pattern(transactions),
            "sankey": self.generate_sankey_data(transactions)
        }
        
        # 흐름 분류
        for tx in transactions:
            if tx.direction == 'inflow':
                flow_data['inflows'].append(self.format_transaction(tx))
            elif tx.direction == 'outflow':
                flow_data['outflows'].append(self.format_transaction(tx))
            else:
                flow_data['internal_transfers'].append(self.format_transaction(tx))
        
        # 통계 추가
        flow_data['statistics'] = {
            'total_inflow': sum(tx.amount for tx in transactions if tx.direction == 'inflow'),
            'total_outflow': sum(tx.amount for tx in transactions if tx.direction == 'outflow'),
            'net_flow': flow_data['statistics']['total_inflow'] - flow_data['statistics']['total_outflow'],
            'transaction_count': len(transactions),
            'average_transaction_size': sum(tx.amount for tx in transactions) / len(transactions) if transactions else 0
        }
        
        return flow_data
    
    def generate_sankey_data(self, transactions: List) -> Dict:
        """Sankey 다이어그램용 데이터 생성"""
        nodes = [
            {"id": 0, "name": "외부 입금"},
            {"id": 1, "name": "사용자 지갑"},
            {"id": 2, "name": "Hot Wallet"},
            {"id": 3, "name": "Warm Wallet"},
            {"id": 4, "name": "Cold Wallet"},
            {"id": 5, "name": "외부 출금"},
            {"id": 6, "name": "수수료"}
        ]
        
        # 흐름 집계
        flows = defaultdict(lambda: Decimal('0'))
        
        for tx in transactions:
            if tx.tx_type == 'deposit':
                flows[(0, 1)] += tx.amount
            elif tx.tx_type == 'sweep':
                flows[(1, 2)] += tx.amount
            elif tx.tx_type == 'cold_storage':
                flows[(2, 4)] += tx.amount
            elif tx.tx_type == 'withdrawal':
                flows[(2, 5)] += tx.amount
            elif tx.tx_type == 'fee':
                flows[(2, 6)] += tx.amount
        
        # 링크 생성
        links = []
        for (source, target), value in flows.items():
            if value > 0:
                links.append({
                    "source": source,
                    "target": target,
                    "value": float(value)
                })
        
        return {
            "nodes": nodes,
            "links": links
        }
    
    def detect_flow_pattern(self, transactions: List) -> str:
        """트랜잭션 흐름 패턴 감지"""
        if not transactions:
            return "no_activity"
        
        # 시간별 분포 분석
        hourly_distribution = defaultdict(int)
        for tx in transactions:
            hour = tx.created_at.hour
            hourly_distribution[hour] += 1
        
        # 패턴 판단
        total_tx = len(transactions)
        max_hour_tx = max(hourly_distribution.values()) if hourly_distribution else 0
        
        if max_hour_tx > total_tx * 0.3:
            return "spike"  # 특정 시간 집중
        elif len(hourly_distribution) < 3:
            return "burst"  # 짧은 기간 집중
        elif self.has_regular_pattern(hourly_distribution):
            return "regular"  # 규칙적 패턴
        else:
            return "normal"  # 정상 분포
```

### 3. AI 기반 이상 거래 탐지

`app/services/ai/anomaly_detector.py` 파일을 생성하세요:

```python
"""AI 기반 이상 거래 탐지 서비스"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Tuple
import joblib
from datetime import datetime, timedelta

class AnomalyDetector:
    """AI 기반 이상 거래 탐지"""
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.01,  # 1% 이상치 예상
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_columns = [
            'amount',
            'hour_of_day',
            'day_of_week',
            'days_since_last_tx',
            'recipient_tx_count',
            'sender_balance_ratio',
            'velocity_score',
            'amount_deviation'
        ]
        self.load_or_train_model()
    
    def load_or_train_model(self):
        """모델 로드 또는 학습"""
        try:
            self.model = joblib.load('models/anomaly_detector.pkl')
            self.scaler = joblib.load('models/anomaly_scaler.pkl')
        except:
            # 초기 학습 필요
            pass
    
    async def detect_anomalies(self, transactions: List[Dict]) -> List[Dict]:
        """이상 거래 탐지"""
        if not transactions:
            return []
        
        # 특성 추출
        features = await self.extract_features(transactions)
        
        if len(features) < 10:  # 데이터 부족
            return []
        
        # 정규화
        features_scaled = self.scaler.fit_transform(features)
        
        # 이상치 점수 계산
        anomaly_scores = self.model.decision_function(features_scaled)
        predictions = self.model.predict(features_scaled)
        
        # 위험도 높은 거래 추출
        risky_transactions = []
        
        for i, (tx, score, pred) in enumerate(zip(transactions, anomaly_scores, predictions)):
            if pred == -1:  # 이상치로 판단
                risk_level = self.calculate_risk_level(score)
                risk_factors = await self.analyze_risk_factors(tx, features[i])
                
                risky_transactions.append({
                    "transaction_id": tx.get("id"),
                    "amount": tx.get("amount"),
                    "risk_score": abs(float(score)),
                    "risk_level": risk_level,
                    "risk_factors": risk_factors,
                    "recommended_action": self.recommend_action(risk_level, risk_factors),
                    "confidence": self.calculate_confidence(score, features[i])
                })
        
        return sorted(risky_transactions, key=lambda x: x["risk_score"], reverse=True)
    
    async def extract_features(self, transactions: List[Dict]) -> np.ndarray:
        """트랜잭션에서 특성 추출"""
        features = []
        
        for tx in transactions:
            # 기본 특성
            amount = float(tx.get("amount", 0))
            created_at = tx.get("created_at", datetime.utcnow())
            
            # 시간 특성
            hour_of_day = created_at.hour
            day_of_week = created_at.weekday()
            
            # 사용자 행동 특성
            user_stats = await self.get_user_statistics(tx.get("user_id"))
            days_since_last = (created_at - user_stats["last_transaction"]).days if user_stats["last_transaction"] else 0
            
            # 수신자 특성
            recipient_stats = await self.get_address_statistics(tx.get("to_address"))
            
            # 속도 점수 (최근 거래 빈도)
            velocity_score = await self.calculate_velocity_score(tx.get("user_id"))
            
            # 금액 편차
            amount_deviation = abs(amount - user_stats["avg_amount"]) / user_stats["std_amount"] if user_stats["std_amount"] > 0 else 0
            
            features.append([
                amount,
                hour_of_day,
                day_of_week,
                days_since_last,
                recipient_stats["transaction_count"],
                amount / user_stats["total_balance"] if user_stats["total_balance"] > 0 else 0,
                velocity_score,
                amount_deviation
            ])
        
        return np.array(features)
    
    def calculate_risk_level(self, anomaly_score: float) -> str:
        """위험도 레벨 계산"""
        abs_score = abs(anomaly_score)
        
        if abs_score > 0.8:
            return "critical"
        elif abs_score > 0.6:
            return "high"
        elif abs_score > 0.4:
            return "medium"
        else:
            return "low"
    
    async def analyze_risk_factors(self, transaction: Dict, features: List) -> List[str]:
        """위험 요인 분석"""
        risk_factors = []
        
        # 금액 이상
        if features[0] > features[7] * 3:  # 평균의 3배 이상
            risk_factors.append("abnormal_amount")
        
        # 시간 이상
        if features[1] in [2, 3, 4, 5]:  # 새벽 시간
            risk_factors.append("unusual_time")
        
        # 빈도 이상
        if features[6] > 0.8:  # 높은 속도 점수
            risk_factors.append("high_frequency")
        
        # 새로운 수신자
        if features[4] == 0:
            risk_factors.append("new_recipient")
        
        # 잔액 대비 큰 금액
        if features[5] > 0.5:  # 잔액의 50% 이상
            risk_factors.append("large_portion_of_balance")
        
        return risk_factors
    
    def recommend_action(self, risk_level: str, risk_factors: List[str]) -> str:
        """권장 조치 생성"""
        if risk_level == "critical":
            return "immediate_block_and_review"
        elif risk_level == "high":
            if "new_recipient" in risk_factors and "large_portion_of_balance" in risk_factors:
                return "manual_approval_required"
            else:
                return "additional_verification"
        elif risk_level == "medium":
            return "monitor_closely"
        else:
            return "log_and_continue"
```

### 4. 예측 분석 서비스

`app/services/analytics/predictive_analytics.py` 파일을 생성하세요:

```python
"""예측 분석 서비스"""
from prophet import Prophet
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime, timedelta
import numpy as np

class PredictiveAnalytics:
    """예측 분석 서비스"""
    
    def __init__(self):
        self.models = {
            'transaction_volume': None,
            'energy_usage': None,
            'user_growth': None,
            'revenue': None
        }
    
    async def get_predictions(self, partner_id: int) -> Dict[str, Any]:
        """종합 예측 분석"""
        predictions = {}
        
        # 거래량 예측
        predictions['transaction_volume'] = await self.predict_transaction_volume(
            partner_id, 
            days_ahead=7
        )
        
        # 에너지 사용량 예측
        predictions['energy_usage'] = await self.predict_energy_usage(
            partner_id,
            days_ahead=3
        )
        
        # 사용자 성장 예측
        predictions['user_growth'] = await self.predict_user_growth(
            partner_id,
            days_ahead=30
        )
        
        # 수익 예측
        predictions['revenue'] = await self.predict_revenue(
            partner_id,
            days_ahead=30
        )
        
        # 종합 인사이트
        predictions['insights'] = self.generate_insights(predictions)
        
        return predictions
    
    async def predict_transaction_volume(self, partner_id: int, days_ahead: int = 7) -> Dict:
        """거래량 예측"""
        # 과거 데이터 로드
        historical_data = await self.load_transaction_history(partner_id)
        
        # Prophet 모델 준비
        df = pd.DataFrame(historical_data)
        df['ds'] = pd.to_datetime(df['date'])
        df['y'] = df['transaction_count']
        
        # 모델 학습
        model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode='multiplicative',
            daily_seasonality=True,
            weekly_seasonality=True
        )
        
        # 사용자 정의 계절성 추가
        model.add_seasonality(
            name='hourly',
            period=1,
            fourier_order=8
        )
        
        model.fit(df)
        
        # 예측
        future = model.make_future_dataframe(periods=days_ahead * 24, freq='H')
        forecast = model.predict(future)
        
        # 결과 포맷팅
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days_ahead * 24)
        
        return {
            'forecast': forecast_data.to_dict('records'),
            'trend': self.analyze_trend(forecast),
            'seasonality': self.extract_seasonality(model),
            'anomaly_points': self.detect_forecast_anomalies(forecast),
            'confidence_interval': self.calculate_confidence_interval(forecast)
        }
    
    async def predict_energy_usage(self, partner_id: int, days_ahead: int = 3) -> Dict:
        """에너지 사용량 예측"""
        # 과거 에너지 사용 데이터
        energy_history = await self.load_energy_history(partner_id)
        
        # 거래량과의 상관관계 분석
        correlation = await self.analyze_energy_transaction_correlation(partner_id)
        
        # 예측 모델
        predicted_transactions = await self.predict_transaction_volume(partner_id, days_ahead)
        
        # 에너지 사용량 계산
        energy_predictions = []
        for tx_forecast in predicted_transactions['forecast']:
            energy_needed = tx_forecast['yhat'] * correlation['energy_per_transaction']
            
            energy_predictions.append({
                'timestamp': tx_forecast['ds'],
                'energy_required': energy_needed,
                'energy_buffer': energy_needed * 1.2,  # 20% 버퍼
                'trx_required': energy_needed / 1500  # 1 TRX = 1500 에너지
            })
        
        # 임계값 예측
        critical_points = [
            ep for ep in energy_predictions 
            if ep['energy_required'] > correlation['current_capacity'] * 0.8
        ]
        
        return {
            'predictions': energy_predictions,
            'critical_points': critical_points,
            'recommended_action': self.recommend_energy_action(energy_predictions),
            'optimization_opportunities': self.identify_energy_optimizations(energy_predictions)
        }
    
    def generate_insights(self, predictions: Dict) -> List[Dict]:
        """예측 기반 인사이트 생성"""
        insights = []
        
        # 거래량 인사이트
        if predictions['transaction_volume']['trend'] == 'increasing':
            insights.append({
                'type': 'growth',
                'severity': 'info',
                'message': '향후 7일간 거래량이 증가할 것으로 예상됩니다.',
                'recommendation': '에너지 풀을 사전에 확충하시기 바랍니다.'
            })
        
        # 에너지 부족 경고
        if predictions['energy_usage']['critical_points']:
            insights.append({
                'type': 'warning',
                'severity': 'high',
                'message': f"{len(predictions['energy_usage']['critical_points'])}개 시점에서 에너지 부족이 예상됩니다.",
                'recommendation': 'TRX 추가 스테이킹 또는 에너지 구매를 고려하세요.'
            })
        
        # 수익 최적화 기회
        revenue_trend = predictions['revenue'].get('trend')
        if revenue_trend and revenue_trend['growth_rate'] < 0.05:
            insights.append({
                'type': 'optimization',
                'severity': 'medium',
                'message': '수익 성장률이 둔화되고 있습니다.',
                'recommendation': '수수료 구조 최적화 또는 신규 서비스 도입을 검토하세요.'
            })
        
        return insights
```

### 5. 자동화된 리포트 생성

`app/services/reporting/automated_reports.py` 파일을 생성하세요:

```python
"""자동화된 리포트 생성 서비스"""
from datetime import datetime, timedelta
import jinja2
from weasyprint import HTML
import plotly.graph_objects as go
import plotly.io as pio
from typing import Dict, Any
import asyncio

class AutomatedReportGenerator:
    """자동 리포트 생성기"""
    
    def __init__(self):
        self.template_loader = jinja2.FileSystemLoader('templates/reports')
        self.template_env = jinja2.Environment(loader=self.template_loader)
        self.report_types = ['daily', 'weekly', 'monthly', 'custom']
    
    async def generate_report(self, partner_id: int, report_type: str = 'daily') -> bytes:
        """종합 리포트 생성"""
        # 리포트 데이터 수집
        report_data = await self.collect_report_data(partner_id, report_type)
        
        # 차트 생성
        charts = await self.generate_charts(report_data)
        
        # 템플릿 렌더링
        template = self.template_env.get_template(f'{report_type}_report.html')
        html_content = template.render(
            partner_id=partner_id,
            report_date=datetime.now().strftime("%Y-%m-%d"),
            data=report_data,
            charts=charts,
            insights=await self.generate_report_insights(report_data)
        )
        
        # PDF 변환
        pdf = HTML(string=html_content).write_pdf()
        
        # 저장 및 발송
        await self.save_report(partner_id, report_type, pdf)
        await self.send_report(partner_id, report_type, pdf)
        
        return pdf
    
    async def collect_report_data(self, partner_id: int, report_type: str) -> Dict[str, Any]:
        """리포트 데이터 수집"""
        # 기간 설정
        if report_type == 'daily':
            start_date = datetime.now() - timedelta(days=1)
        elif report_type == 'weekly':
            start_date = datetime.now() - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(days=1)
        
        # 데이터 수집 태스크
        tasks = [
            self.get_transaction_summary(partner_id, start_date),
            self.get_wallet_summary(partner_id),
            self.get_energy_summary(partner_id, start_date),
            self.get_revenue_summary(partner_id, start_date),
            self.get_user_summary(partner_id, start_date),
            self.get_security_summary(partner_id, start_date)
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            'transactions': results[0],
            'wallets': results[1],
            'energy': results[2],
            'revenue': results[3],
            'users': results[4],
            'security': results[5]
        }
    
    async def generate_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """차트 생성"""
        charts = {}
        
        # 거래량 차트
        charts['transaction_volume'] = self.create_line_chart(
            data['transactions']['hourly_volume'],
            '시간별 거래량',
            'datetime',
            'volume'
        )
        
        # 지갑 잔액 분포
        charts['wallet_distribution'] = self.create_pie_chart(
            data['wallets']['distribution'],
            '지갑 유형별 자산 분포'
        )
        
        # 수익 추이
        charts['revenue_trend'] = self.create_bar_chart(
            data['revenue']['daily_revenue'],
            '일별 수익',
            'date',
            'revenue'
        )
        
        # 에너지 사용률
        charts['energy_usage'] = self.create_gauge_chart(
            data['energy']['usage_percentage'],
            '에너지 사용률'
        )
        
        return charts
    
    def create_line_chart(self, data, title, x_label, y_label) -> str:
        """라인 차트 생성"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=[d[x_label] for d in data],
            y=[d[y_label] for d in data],
            mode='lines+markers',
            name=title,
            line=dict(color='#3B82F6', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            template='plotly_white',
            height=400
        )
        
        return pio.to_html(fig, include_plotlyjs='cdn')
    
    async def generate_report_insights(self, data: Dict[str, Any]) -> List[Dict]:
        """리포트 인사이트 생성"""
        insights = []
        
        # 거래량 분석
        tx_growth = data['transactions']['growth_rate']
        if tx_growth > 0.2:
            insights.append({
                'type': 'positive',
                'title': '거래량 급증',
                'description': f'거래량이 전일 대비 {tx_growth*100:.1f}% 증가했습니다.',
                'recommendation': '시스템 용량 확대를 고려하세요.'
            })
        
        # 수익 분석
        revenue_vs_cost = data['revenue']['profit_margin']
        if revenue_vs_cost < 0.2:
            insights.append({
                'type': 'warning',
                'title': '수익성 저하',
                'description': f'순이익률이 {revenue_vs_cost*100:.1f}%로 낮습니다.',
                'recommendation': '비용 구조 최적화가 필요합니다.'
            })
        
        # 보안 이벤트
        security_events = data['security']['critical_events']
        if security_events:
            insights.append({
                'type': 'alert',
                'title': '보안 주의 필요',
                'description': f'{len(security_events)}건의 중요 보안 이벤트가 발생했습니다.',
                'recommendation': '보안 정책 검토 및 강화가 필요합니다.'
            })
        
        return insights
```

### 6. 24/7 모니터링 알림 센터

`app/services/monitoring/alert_center.py` 파일을 생성하세요:

```python
"""24/7 모니터링 알림 센터"""
from typing import List, Dict, Any
import asyncio
from datetime import datetime
from enum import Enum
import uuid

from app.core.events import event_manager
from app.services.notification import NotificationService
from app.core.logger import logger

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertCenter:
    """24/7 모니터링 알림 센터"""
    
    def __init__(self, partner_id: int):
        self.partner_id = partner_id
        self.notification_service = NotificationService()
        self.alert_rules = self.load_alert_rules()
        self.alert_history = []
        self.monitoring_tasks = []
    
    async def start_monitoring(self):
        """24/7 모니터링 시작"""
        logger.info(f"Starting 24/7 monitoring for partner {self.partner_id}")
        
        # 모니터링 태스크 생성
        self.monitoring_tasks = [
            asyncio.create_task(self.monitor_wallet_balance()),
            asyncio.create_task(self.monitor_energy_level()),
            asyncio.create_task(self.monitor_transaction_patterns()),
            asyncio.create_task(self.monitor_system_health()),
            asyncio.create_task(self.monitor_security_events()),
            asyncio.create_task(self.monitor_api_usage())
        ]
        
        # 모든 태스크 실행
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
    
    async def monitor_wallet_balance(self):
        """지갑 잔액 모니터링"""
        while True:
            try:
                wallets = await self.get_partner_wallets()
                
                for wallet in wallets:
                    balance = await self.get_wallet_balance(wallet.address)
                    
                    # Hot Wallet 잔액 체크
                    if wallet.wallet_type == 'hot':
                        daily_average = await self.get_daily_average_withdrawal()
                        
                        if balance < daily_average * 0.5:
                            await self.create_alert(
                                title="Hot Wallet 잔액 부족",
                                message=f"Hot Wallet 잔액이 일일 평균 출금액의 50% 미만입니다. 현재: {balance} USDT",
                                severity=AlertSeverity.CRITICAL,
                                data={
                                    'wallet_address': wallet.address,
                                    'current_balance': balance,
                                    'daily_average': daily_average,
                                    'recommended_action': 'warm_to_hot_transfer'
                                }
                            )
                    
                    # Cold Wallet 비율 체크
                    elif wallet.wallet_type == 'cold':
                        total_balance = await self.get_total_balance()
                        cold_ratio = balance / total_balance if total_balance > 0 else 0
                        
                        if cold_ratio < 0.7:
                            await self.create_alert(
                                title="Cold Storage 비율 부족",
                                message=f"Cold Storage 비율이 70% 미만입니다. 현재: {cold_ratio*100:.1f}%",
                                severity=AlertSeverity.WARNING,
                                data={
                                    'cold_balance': balance,
                                    'total_balance': total_balance,
                                    'current_ratio': cold_ratio,
                                    'recommended_action': 'hot_to_cold_transfer'
                                }
                            )
                
                await asyncio.sleep(300)  # 5분마다 확인
                
            except Exception as e:
                logger.error(f"Wallet balance monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_energy_level(self):
        """에너지 레벨 모니터링"""
        while True:
            try:
                energy_status = await self.get_energy_status()
                
                # 현재 에너지 비율
                energy_ratio = energy_status['current'] / energy_status['max']
                
                # 예상 소진 시간 계산
                depletion_time = await self.calculate_energy_depletion_time(
                    energy_status['current'],
                    energy_status['usage_rate']
                )
                
                # 임계값 체크
                if energy_ratio < 0.1:
                    await self.create_alert(
                        title="에너지 긴급 부족",
                        message=f"에너지가 10% 미만입니다. 예상 소진 시간: {depletion_time}",
                        severity=AlertSeverity.EMERGENCY,
                        data={
                            'current_energy': energy_status['current'],
                            'max_energy': energy_status['max'],
                            'depletion_time': depletion_time,
                            'recommended_action': 'emergency_energy_purchase'
                        }
                    )
                elif energy_ratio < 0.2:
                    await self.create_alert(
                        title="에너지 부족 경고",
                        message=f"에너지가 20% 미만입니다. 조치가 필요합니다.",
                        severity=AlertSeverity.WARNING,
                        data={
                            'current_energy': energy_status['current'],
                            'recommended_action': 'prepare_energy_purchase'
                        }
                    )
                
                await asyncio.sleep(180)  # 3분마다 확인
                
            except Exception as e:
                logger.error(f"Energy monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_transaction_patterns(self):
        """거래 패턴 모니터링"""
        while True:
            try:
                # 최근 거래 분석
                recent_transactions = await self.get_recent_transactions(minutes=10)
                
                # 이상 패턴 감지
                anomalies = await self.detect_transaction_anomalies(recent_transactions)
                
                for anomaly in anomalies:
                    if anomaly['severity'] == 'high':
                        await self.create_alert(
                            title="이상 거래 패턴 감지",
                            message=anomaly['description'],
                            severity=AlertSeverity.CRITICAL,
                            data=anomaly
                        )
                
                # 대량 거래 감지
                large_transactions = [
                    tx for tx in recent_transactions 
                    if tx.amount > 10000  # 10,000 USDT 이상
                ]
                
                if large_transactions:
                    await self.create_alert(
                        title="대량 거래 감지",
                        message=f"{len(large_transactions)}건의 대량 거래가 감지되었습니다.",
                        severity=AlertSeverity.WARNING,
                        data={'transactions': large_transactions}
                    )
                
                await asyncio.sleep(60)  # 1분마다 확인
                
            except Exception as e:
                logger.error(f"Transaction monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_system_health(self):
        """시스템 상태 모니터링"""
        while True:
            try:
                health_status = await self.check_system_health()
                
                # API 응답 시간 체크
                if health_status['api_response_time'] > 1000:  # 1초 이상
                    await self.create_alert(
                        title="API 응답 지연",
                        message=f"API 평균 응답 시간이 {health_status['api_response_time']}ms입니다.",
                        severity=AlertSeverity.WARNING,
                        data=health_status
                    )
                
                # 에러율 체크
                if health_status['error_rate'] > 0.05:  # 5% 이상
                    await self.create_alert(
                        title="높은 에러율",
                        message=f"시스템 에러율이 {health_status['error_rate']*100:.1f}%입니다.",
                        severity=AlertSeverity.CRITICAL,
                        data=health_status
                    )
                
                # 데이터베이스 연결 체크
                if not health_status['database_healthy']:
                    await self.create_alert(
                        title="데이터베이스 연결 문제",
                        message="데이터베이스 연결에 문제가 있습니다.",
                        severity=AlertSeverity.EMERGENCY,
                        data=health_status
                    )
                
                await asyncio.sleep(30)  # 30초마다 확인
                
            except Exception as e:
                logger.error(f"System health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        data: Dict = None
    ):
        """알림 생성 및 발송"""
        alert = {
            "id": str(uuid.uuid4()),
            "partner_id": self.partner_id,
            "timestamp": datetime.utcnow(),
            "title": title,
            "message": message,
            "severity": severity.value,
            "data": data or {},
            "acknowledged": False,
            "resolved": False
        }
        
        # 알림 저장
        await self.save_alert(alert)
        self.alert_history.append(alert)
        
        # 심각도에 따른 알림 발송
        if severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            # 즉시 알림 (SMS, 전화)
            await self.send_immediate_notification(alert)
            
            # 에스컬레이션
            if severity == AlertSeverity.EMERGENCY:
                await self.escalate_alert(alert)
        
        elif severity == AlertSeverity.WARNING:
            # 일반 알림 (이메일, 슬랙)
            await self.send_standard_notification(alert)
        
        else:
            # 정보성 알림 (대시보드만)
            await self.update_dashboard_notification(alert)
        
        # 이벤트 발행
        await event_manager.publish(
            f"alert.{severity.value}",
            alert
        )
    
    async def send_immediate_notification(self, alert: Dict):
        """즉시 알림 발송"""
        # SMS 발송
        await self.notification_service.send_sms(
            recipient=await self.get_emergency_contacts(),
            message=f"[긴급] {alert['title']}\n{alert['message']}"
        )
        
        # 전화 알림 (TTS)
        await self.notification_service.make_call(
            recipient=await self.get_primary_contact(),
            message=alert['message']
        )
        
        # 푸시 알림
        await self.notification_service.send_push(
            title=alert['title'],
            body=alert['message'],
            priority='high'
        )
    
    def load_alert_rules(self) -> Dict:
        """알림 규칙 로드"""
        return {
            'wallet_balance': {
                'hot_wallet_minimum': 0.5,  # 일일 평균의 50%
                'cold_wallet_ratio': 0.7,    # 전체의 70%
                'check_interval': 300        # 5분
            },
            'energy': {
                'critical_threshold': 0.1,   # 10%
                'warning_threshold': 0.2,    # 20%
                'check_interval': 180        # 3분
            },
            'transactions': {
                'large_amount': 10000,       # 10,000 USDT
                'frequency_limit': 10,       # 10분당 10회
                'check_interval': 60         # 1분
            },
            'system': {
                'max_response_time': 1000,   # 1초
                'max_error_rate': 0.05,      # 5%
                'check_interval': 30         # 30초
            }
        }
```

### 7. 대시보드 프론트엔드 컴포넌트

`frontend/components/dashboard/IntegratedDashboard.tsx` 파일을 생성하세요:

```typescript
// 종합 대시보드 React 컴포넌트
import React, { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import { WalletOverview } from './WalletOverview';
import { TransactionFlow } from './TransactionFlow';
import { EnergyMonitor } from './EnergyMonitor';
import { RevenueMetrics } from './RevenueMetrics';
import { RiskAlerts } from './RiskAlerts';
import { PredictiveInsights } from './PredictiveInsights';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useDashboardData } from '../../hooks/useDashboardData';

export const IntegratedDashboard: React.FC = () => {
  const { data, loading, error, refetch } = useDashboardData();
  const ws = useWebSocket();
  
  // 실시간 업데이트
  useEffect(() => {
    const handleRealtimeUpdate = (event: any) => {
      if (event.type === 'dashboard_update') {
        refetch();
      }
    };
    
    ws.on('message', handleRealtimeUpdate);
    
    return () => {
      ws.off('message', handleRealtimeUpdate);
    };
  }, [ws, refetch]);
  
  if (loading) return <LoadingScreen />;
  if (error) return <ErrorScreen error={error} />;
  
  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        파트너사 종합 대시보드
      </Typography>
      
      <Grid container spacing={3}>
        {/* 지갑 현황 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <WalletOverview data={data.wallet_overview} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* 거래 흐름 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <TransactionFlow data={data.transaction_flow} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* 에너지 상태 */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <EnergyMonitor data={data.energy_status} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* 수익 지표 */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <RevenueMetrics data={data.revenue_metrics} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* 위험 알림 */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <RiskAlerts alerts={data.risk_alerts} />
            </CardContent>
          </Card>
        </Grid>
        
        {/* 예측 인사이트 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <PredictiveInsights predictions={data.predictions} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
```

### 8. 대시보드 API 엔드포인트

`app/api/v1/endpoints/partner/dashboard.py` 파일을 생성하세요:

```python
"""파트너사 대시보드 API 엔드포인트"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.deps import get_current_partner
from app.services.dashboard.integrated_dashboard import IntegratedDashboard
from app.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["대시보드"])

@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    timeframe: Optional[str] = Query("24h", description="시간 범위"),
    current_partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """종합 대시보드 데이터 조회"""
    dashboard_service = IntegratedDashboard(db, current_partner.id)
    data = await dashboard_service.get_dashboard_data()
    
    return DashboardResponse(**data)

@router.get("/realtime")
async def get_realtime_data(
    metric: str = Query(..., description="실시간 지표 유형"),
    current_partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """실시간 데이터 스트리밍"""
    # WebSocket으로 구현 권장
    pass

@router.post("/export")
async def export_dashboard(
    format: str = Query("pdf", description="내보내기 형식"),
    current_partner = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db)
):
    """대시보드 데이터 내보내기"""
    dashboard_service = IntegratedDashboard(db, current_partner.id)
    
    if format == "pdf":
        report_generator = AutomatedReportGenerator()
        pdf = await report_generator.generate_report(
            current_partner.id,
            "dashboard_export"
        )
        
        return FileResponse(
            pdf,
            media_type="application/pdf",
            filename=f"dashboard_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
```