"""
Reports 모듈 초기화 및 통합 관리
"""

def get_trend_report_service():
    """트렌드 보고서 서비스 반환"""
    from .trend_reports import TrendReportService
    return TrendReportService()

def get_user_report_service():
    """사용자 보고서 서비스 반환"""
    from .user_reports import UserReportService
    return UserReportService()

__all__ = [
    "get_trend_report_service",
    "get_user_report_service",
]
