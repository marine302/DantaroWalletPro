"""
정기적인 리팩토링 작업 스케줄러
코드 품질 모니터링과 자동화된 리팩토링 제안을 관리합니다.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import schedule

from app.core.database import get_async_session
from scripts.pre_commit_check import generate_quality_report
from scripts.refactoring_monitor import CodeMetricsAnalyzer, RefactoringPlanner

logger = logging.getLogger(__name__)


class RefactoringScheduler:
    """리팩토링 작업 스케줄러"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.docs_dir = self.project_root / "docs"
        self.metrics_analyzer = CodeMetricsAnalyzer(str(project_root))
        self.last_metrics = {}
        self.refactoring_tasks = []

    def start_scheduler(self):
        """스케줄러 시작"""
        logger.info("🚀 리팩토링 스케줄러 시작")

        # 스케줄 설정
        self._setup_schedules()

        # 스케줄러 실행
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
            except KeyboardInterrupt:
                logger.info("리팩토링 스케줄러 중지")
                break
            except Exception as e:
                logger.error(f"스케줄러 실행 중 오류: {str(e)}")
                time.sleep(300)  # 오류 시 5분 대기

    def _setup_schedules(self):
        """스케줄 설정"""
        # 매일 오전 9시 - 메트릭 수집
        schedule.every().day.at("09:00").do(self._daily_metrics_collection)

        # 매주 월요일 오전 10시 - 주간 리팩토링 보고서
        schedule.every().monday.at("10:00").do(self._weekly_refactoring_report)

        # 매월 1일 오전 11시 - 월간 아키텍처 리뷰
        schedule.every().month.do(self._monthly_architecture_review)

        # 매 시간 - 코드 품질 체크 (개발 환경에서만)
        if self._is_development_environment():
            schedule.every().hour.do(self._hourly_quality_check)

        # 파일 변경 감지 시 - 실시간 메트릭 업데이트 (백그라운드)
        schedule.every(30).minutes.do(self._update_metrics_if_changed)

    def _is_development_environment(self) -> bool:
        """개발 환경인지 확인"""
        import os

        return os.getenv("ENVIRONMENT", "development").lower() == "development"

    def _daily_metrics_collection(self):
        """일일 메트릭 수집"""
        try:
            logger.info("📊 일일 메트릭 수집 시작")

            # 메트릭 분석
            metrics = self.metrics_analyzer.analyze_project()

            # 보고서 생성
            report = self.metrics_analyzer.generate_report(metrics)

            # 액션 플랜 생성
            planner = RefactoringPlanner(metrics)
            action_plan = planner.generate_action_plan()

            # 결과 저장
            self._save_daily_metrics(metrics, report, action_plan)

            # 임계값 체크 및 알림
            self._check_metrics_thresholds(metrics)

            logger.info("✅ 일일 메트릭 수집 완료")

        except Exception as e:
            logger.error(f"일일 메트릭 수집 중 오류: {str(e)}")

    def _weekly_refactoring_report(self):
        """주간 리팩토링 보고서 생성"""
        try:
            logger.info("📋 주간 리팩토링 보고서 생성 시작")

            # 이번 주 메트릭 데이터 수집
            weekly_data = self._collect_weekly_data()

            # 리팩토링 진행상황 분석
            progress_analysis = self._analyze_refactoring_progress(weekly_data)

            # 다음 주 우선순위 결정
            next_week_priorities = self._determine_next_week_priorities(weekly_data)

            # 보고서 생성
            report = self._generate_weekly_report(
                progress_analysis, next_week_priorities
            )

            # 보고서 저장
            self._save_weekly_report(report)

            # 팀 알림 (Slack, 이메일 등)
            self._send_weekly_notification(report)

            logger.info("✅ 주간 리팩토링 보고서 생성 완료")

        except Exception as e:
            logger.error(f"주간 리팩토링 보고서 생성 중 오류: {str(e)}")

    def _monthly_architecture_review(self):
        """월간 아키텍처 리뷰"""
        try:
            logger.info("🏗️ 월간 아키텍처 리뷰 시작")

            # 아키텍처 메트릭 수집
            architecture_metrics = self._collect_architecture_metrics()

            # 의존성 분석
            dependency_analysis = self._analyze_dependencies()

            # 아키텍처 개선 제안
            improvement_suggestions = self._generate_architecture_improvements(
                architecture_metrics, dependency_analysis
            )

            # 월간 리뷰 보고서 생성
            review_report = self._generate_monthly_review(
                architecture_metrics, dependency_analysis, improvement_suggestions
            )

            # 보고서 저장
            self._save_monthly_review(review_report)

            logger.info("✅ 월간 아키텍처 리뷰 완료")

        except Exception as e:
            logger.error(f"월간 아키텍처 리뷰 중 오류: {str(e)}")

    def _hourly_quality_check(self):
        """시간별 품질 체크"""
        try:
            logger.info("🔍 시간별 품질 체크 시작")

            # 코드 품질 보고서 생성
            quality_report = generate_quality_report()

            # 품질 저하 감지
            if quality_report["status"] == "FAIL":
                self._handle_quality_degradation(quality_report)

            # 품질 메트릭 저장
            self._save_quality_metrics(quality_report)

            logger.info("✅ 시간별 품질 체크 완료")

        except Exception as e:
            logger.error(f"시간별 품질 체크 중 오류: {str(e)}")

    def _update_metrics_if_changed(self):
        """파일 변경 시 메트릭 업데이트"""
        try:
            # 파일 변경 감지
            if self._detect_file_changes():
                logger.info("📁 파일 변경 감지, 메트릭 업데이트")

                # 변경된 파일들에 대해서만 메트릭 재계산
                changed_files = self._get_changed_files()
                updated_metrics = self._update_changed_file_metrics(changed_files)

                # 메트릭 저장
                self._save_incremental_metrics(updated_metrics)

        except Exception as e:
            logger.error(f"메트릭 업데이트 중 오류: {str(e)}")

    def _save_daily_metrics(self, metrics: List, report: str, action_plan: Dict):
        """일일 메트릭 저장"""
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 메트릭 JSON 저장
        metrics_file = self.docs_dir / f"daily_metrics_{date_str}.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(
                [metric.__dict__ for metric in metrics], f, indent=2, ensure_ascii=False
            )

        # 보고서 저장
        report_file = self.docs_dir / f"daily_report_{date_str}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

        # 액션 플랜 저장
        plan_file = self.docs_dir / f"action_plan_{date_str}.json"
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(action_plan, f, indent=2, ensure_ascii=False)

    def _check_metrics_thresholds(self, metrics: List):
        """메트릭 임계값 체크 및 알림"""
        urgent_files = [m for m in metrics if m.refactoring_priority == "긴급"]

        if urgent_files:
            logger.warning(f"⚠️ 긴급 리팩토링 필요 파일 {len(urgent_files)}개 발견")

            # 알림 생성 (실제 구현에서는 Slack, 이메일 등)
            self._send_urgent_alert(urgent_files)

    def _send_urgent_alert(self, urgent_files: List):
        """긴급 알림 발송"""
        message = f"🚨 긴급 리팩토링 필요!\n\n"
        message += f"대상 파일 수: {len(urgent_files)}\n"

        for file_metric in urgent_files[:5]:  # 상위 5개만 표시
            message += f"- {file_metric.filepath}: {file_metric.lines_of_code}줄\n"

        logger.error(message)

        # 실제 구현에서는 Slack webhook, 이메일 발송 등
        # self._send_slack_notification(message)
        # self._send_email_notification(message)

    def _collect_weekly_data(self) -> Dict[str, Any]:
        """주간 데이터 수집"""
        weekly_data = {
            "period": {
                "start": (datetime.now() - timedelta(days=7)).isoformat(),
                "end": datetime.now().isoformat(),
            },
            "metrics_history": [],
            "refactoring_activities": [],
            "quality_trends": [],
        }

        # 지난 7일의 메트릭 파일들 수집
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")

            metrics_file = self.docs_dir / f"daily_metrics_{date_str}.json"
            if metrics_file.exists():
                with open(metrics_file, "r", encoding="utf-8") as f:
                    daily_metrics = json.load(f)
                    weekly_data["metrics_history"].append(
                        {"date": date_str, "metrics": daily_metrics}
                    )

        return weekly_data

    def _analyze_refactoring_progress(self, weekly_data: Dict) -> Dict[str, Any]:
        """리팩토링 진행상황 분석"""
        if not weekly_data["metrics_history"]:
            return {"status": "no_data"}

        # 첫날과 마지막날 비교
        first_day = weekly_data["metrics_history"][-1]["metrics"]
        last_day = weekly_data["metrics_history"][0]["metrics"]

        # 긴급 파일 수 변화
        first_urgent = len(
            [m for m in first_day if m.get("refactoring_priority") == "긴급"]
        )
        last_urgent = len(
            [m for m in last_day if m.get("refactoring_priority") == "긴급"]
        )

        progress = {
            "urgent_files_change": last_urgent - first_urgent,
            "total_files_analyzed": len(last_day),
            "improvement_trend": (
                "improving"
                if last_urgent < first_urgent
                else "stable" if last_urgent == first_urgent else "degrading"
            ),
        }

        return progress

    def _determine_next_week_priorities(
        self, weekly_data: Dict
    ) -> List[Dict[str, Any]]:
        """다음 주 우선순위 결정"""
        if not weekly_data["metrics_history"]:
            return []

        latest_metrics = weekly_data["metrics_history"][0]["metrics"]
        urgent_files = [
            m for m in latest_metrics if m.get("refactoring_priority") == "긴급"
        ]

        priorities = []
        for file_metric in urgent_files[:3]:  # 상위 3개
            priorities.append(
                {
                    "file": file_metric.get("filepath"),
                    "priority": "높음",
                    "estimated_effort": "3-5일",
                    "reason": f"복잡도 {file_metric.get('complexity_score')}, {file_metric.get('lines_of_code')}줄",
                }
            )

        return priorities

    def _generate_weekly_report(self, progress: Dict, priorities: List) -> str:
        """주간 보고서 생성"""
        report = []
        report.append("# 📊 주간 리팩토링 보고서")
        report.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        report.append("## 📈 이번 주 진행상황")
        if progress.get("status") == "no_data":
            report.append("- 데이터 부족으로 분석 불가")
        else:
            report.append(f"- 긴급 파일 변화: {progress['urgent_files_change']}")
            report.append(f"- 전체 분석 파일: {progress['total_files_analyzed']}")
            report.append(f"- 개선 추세: {progress['improvement_trend']}")

        report.append("")
        report.append("## 🎯 다음 주 우선순위")
        for i, priority in enumerate(priorities, 1):
            report.append(f"{i}. **{priority['file']}**")
            report.append(f"   - 우선순위: {priority['priority']}")
            report.append(f"   - 예상 소요: {priority['estimated_effort']}")
            report.append(f"   - 사유: {priority['reason']}")

        return "\n".join(report)

    def _save_weekly_report(self, report: str):
        """주간 보고서 저장"""
        week_str = datetime.now().strftime("%Y-W%U")
        report_file = self.docs_dir / f"weekly_refactoring_report_{week_str}.md"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)

    def _send_weekly_notification(self, report: str):
        """주간 알림 발송"""
        # 실제 구현에서는 Slack, Teams, 이메일 등
        logger.info("📮 주간 보고서 알림 발송")
        # self._send_slack_notification(report[:500] + "...")

    def _collect_architecture_metrics(self) -> Dict[str, Any]:
        """아키텍처 메트릭 수집"""
        return {
            "module_count": len(list(self.project_root.rglob("*.py"))),
            "dependency_depth": 5,  # 실제로는 의존성 분석 필요
            "coupling_score": 3.2,  # 실제로는 커플링 분석 필요
            "cohesion_score": 7.8,  # 실제로는 응집도 분석 필요
        }

    def _analyze_dependencies(self) -> Dict[str, Any]:
        """의존성 분석"""
        return {
            "circular_dependencies": [],
            "high_coupling_modules": [],
            "unused_imports": [],
        }

    def _generate_architecture_improvements(
        self, metrics: Dict, dependencies: Dict
    ) -> List[str]:
        """아키텍처 개선 제안"""
        improvements = []

        if metrics["coupling_score"] > 5:
            improvements.append("모듈 간 결합도 감소 필요")

        if metrics["cohesion_score"] < 7:
            improvements.append("모듈 내 응집도 개선 필요")

        if dependencies["circular_dependencies"]:
            improvements.append("순환 의존성 제거 필요")

        return improvements

    def _generate_monthly_review(
        self, metrics: Dict, dependencies: Dict, improvements: List
    ) -> str:
        """월간 리뷰 보고서 생성"""
        review = []
        review.append("# 🏗️ 월간 아키텍처 리뷰")
        review.append(f"리뷰 기간: {datetime.now().strftime('%Y년 %m월')}")
        review.append("")

        review.append("## 📊 아키텍처 메트릭")
        for key, value in metrics.items():
            review.append(f"- {key}: {value}")

        review.append("")
        review.append("## 🔍 의존성 분석")
        for key, value in dependencies.items():
            review.append(f"- {key}: {len(value)}개")

        review.append("")
        review.append("## 💡 개선 제안")
        for improvement in improvements:
            review.append(f"- {improvement}")

        return "\n".join(review)

    def _save_monthly_review(self, review: str):
        """월간 리뷰 저장"""
        month_str = datetime.now().strftime("%Y-%m")
        review_file = self.docs_dir / f"monthly_architecture_review_{month_str}.md"

        with open(review_file, "w", encoding="utf-8") as f:
            f.write(review)

    def _detect_file_changes(self) -> bool:
        """파일 변경 감지"""
        # 실제 구현에서는 watchdog 라이브러리 사용 권장
        return False

    def _get_changed_files(self) -> List[str]:
        """변경된 파일 목록"""
        return []

    def _update_changed_file_metrics(self, files: List[str]) -> Dict:
        """변경된 파일의 메트릭 업데이트"""
        return {}

    def _save_incremental_metrics(self, metrics: Dict):
        """증분 메트릭 저장"""
        pass

    def _handle_quality_degradation(self, quality_report: Dict):
        """품질 저하 처리"""
        logger.warning("⚠️ 코드 품질 저하 감지")
        # 실제로는 알림 발송, 자동 수정 등

    def _save_quality_metrics(self, quality_report: Dict):
        """품질 메트릭 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        quality_file = self.docs_dir / f"quality_metrics_{timestamp}.json"

        with open(quality_file, "w", encoding="utf-8") as f:
            json.dump(quality_report, f, indent=2, ensure_ascii=False)


def main():
    """메인 실행 함수"""
    import sys

    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "/Users/danielkwon/DantaroWalletPro/DantaroWalletPro"

    scheduler = RefactoringScheduler(project_root)
    scheduler.start_scheduler()


if __name__ == "__main__":
    main()
