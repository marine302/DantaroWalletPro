#!/usr/bin/env python3
"""
리팩토링 모니터링 스크립트
코드 메트릭을 수집하고 리팩토링이 필요한 파일들을 식별합니다.
"""

import ast
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FileMetrics:
    """파일 메트릭 정보"""

    filepath: str
    lines_of_code: int
    num_classes: int
    num_functions: int
    num_methods: int
    complexity_score: int
    max_function_length: int
    max_class_length: int
    last_modified: str
    refactoring_priority: str


class CodeMetricsAnalyzer:
    """코드 메트릭 분석기"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"

    def analyze_file(self, filepath: Path) -> Optional[FileMetrics]:
        """개별 파일의 메트릭을 분석합니다."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            # 기본 메트릭
            lines_of_code = len(
                [
                    line
                    for line in content.split("\n")
                    if line.strip() and not line.strip().startswith("#")
                ]
            )

            # AST 분석
            analyzer = ASTAnalyzer()
            analyzer.visit(tree)

            # 복잡도 계산
            complexity = self._calculate_complexity(analyzer)

            # 수정 시간
            last_modified = datetime.fromtimestamp(
                os.path.getmtime(filepath)
            ).isoformat()

            # 우선순위 결정
            priority = self._determine_priority(lines_of_code, complexity, analyzer)

            return FileMetrics(
                filepath=str(filepath.relative_to(self.project_root)),
                lines_of_code=lines_of_code,
                num_classes=len(analyzer.classes),
                num_functions=len(analyzer.functions),
                num_methods=analyzer.total_methods,
                complexity_score=complexity,
                max_function_length=analyzer.max_function_length,
                max_class_length=analyzer.max_class_length,
                last_modified=last_modified,
                refactoring_priority=priority,
            )

        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")
            return None

    def _calculate_complexity(self, analyzer) -> int:
        """복잡도 점수를 계산합니다."""
        # 가중 복잡도 계산
        base_score = analyzer.lines_of_code * 0.1
        class_penalty = len(analyzer.classes) * 5
        function_penalty = len(analyzer.functions) * 2
        method_penalty = analyzer.total_methods * 1.5
        length_penalty = max(analyzer.max_function_length - 50, 0) * 0.5

        return int(
            base_score
            + class_penalty
            + function_penalty
            + method_penalty
            + length_penalty
        )

    def _determine_priority(self, lines: int, complexity: int, analyzer) -> str:
        """리팩토링 우선순위를 결정합니다."""
        # 긴급: 500줄 이상이고 복잡도 높음
        if lines > 500 and complexity > 100:
            return "긴급"
        # 높음: 300줄 이상이거나 복잡도 높음
        elif lines > 300 or complexity > 80:
            return "높음"
        # 중간: 200줄 이상이거나 메서드 많음
        elif lines > 200 or analyzer.total_methods > 15:
            return "중간"
        # 낮음: 그 외
        else:
            return "낮음"

    def analyze_project(self) -> List[FileMetrics]:
        """프로젝트 전체 파일을 분석합니다."""
        metrics = []

        # Python 파일 찾기
        for py_file in self.app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue

            file_metrics = self.analyze_file(py_file)
            if file_metrics:
                metrics.append(file_metrics)

        # 우선순위별로 정렬
        priority_order = {"긴급": 0, "높음": 1, "중간": 2, "낮음": 3}
        metrics.sort(
            key=lambda x: (priority_order[x.refactoring_priority], -x.lines_of_code)
        )

        return metrics

    def generate_report(self, metrics: List[FileMetrics]) -> str:
        """리팩토링 보고서를 생성합니다."""
        report = []
        report.append("# 📊 코드 메트릭 및 리팩토링 보고서")
        report.append(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 요약 통계
        total_files = len(metrics)
        urgent_files = len([m for m in metrics if m.refactoring_priority == "긴급"])
        high_files = len([m for m in metrics if m.refactoring_priority == "높음"])

        report.append("## 📈 요약 통계")
        report.append(f"- 전체 분석 파일: {total_files}개")
        report.append(f"- 긴급 리팩토링 필요: {urgent_files}개")
        report.append(f"- 높은 우선순위: {high_files}개")
        report.append("")

        # 우선순위별 파일 목록
        for priority in ["긴급", "높음", "중간"]:
            priority_files = [m for m in metrics if m.refactoring_priority == priority]
            if not priority_files:
                continue

            report.append(f"## 🔴 {priority} 우선순위 파일")
            report.append("")

            for metric in priority_files:
                report.append(f"### {metric.filepath}")
                report.append(f"- 코드 라인: {metric.lines_of_code}")
                report.append(f"- 클래스 수: {metric.num_classes}")
                report.append(f"- 함수 수: {metric.num_functions}")
                report.append(f"- 메서드 수: {metric.num_methods}")
                report.append(f"- 복잡도 점수: {metric.complexity_score}")
                report.append(f"- 최대 함수 길이: {metric.max_function_length}")
                report.append("")

        return "\n".join(report)


class ASTAnalyzer(ast.NodeVisitor):
    """AST 노드 방문자"""

    def __init__(self):
        self.classes = []
        self.functions = []
        self.methods = []
        self.total_methods = 0
        self.max_function_length = 0
        self.max_class_length = 0
        self.lines_of_code = 0
        self.current_class = None

    def visit_ClassDef(self, node):
        """클래스 정의 방문"""
        self.classes.append(
            {
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
            }
        )

        class_length = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
        self.max_class_length = max(self.max_class_length, class_length)

        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        """함수 정의 방문"""
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", node.lineno),
            "class": self.current_class,
        }

        if self.current_class:
            self.methods.append(func_info)
            self.total_methods += 1
        else:
            self.functions.append(func_info)

        func_length = getattr(node, "end_lineno", node.lineno) - node.lineno + 1
        self.max_function_length = max(self.max_function_length, func_length)

        self.generic_visit(node)


class RefactoringPlanner:
    """리팩토링 계획 생성기"""

    def __init__(self, metrics: List[FileMetrics]):
        self.metrics = metrics

    def generate_action_plan(self) -> Dict[str, Any]:
        """리팩토링 액션 플랜을 생성합니다."""
        plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_goals": [],
            "automation_recommendations": [],
        }

        # 긴급 액션
        urgent_files = [m for m in self.metrics if m.refactoring_priority == "긴급"]
        for file_metric in urgent_files:
            plan["immediate_actions"].append(
                {
                    "file": file_metric.filepath,
                    "action": "모듈 분해",
                    "reason": f"코드 라인 {file_metric.lines_of_code}, 복잡도 {file_metric.complexity_score}",
                    "estimated_effort": "높음",
                }
            )

        # 단기 목표
        high_files = [m for m in self.metrics if m.refactoring_priority == "높음"]
        for file_metric in high_files:
            plan["short_term_goals"].append(
                {
                    "file": file_metric.filepath,
                    "action": "함수 분리 및 클래스 리팩토링",
                    "reason": f"코드 라인 {file_metric.lines_of_code}",
                    "estimated_effort": "중간",
                }
            )

        # 장기 목표
        plan["long_term_goals"].extend(
            ["도메인 주도 설계 패턴 적용", "인터페이스 분리 및 의존성 주입", "아키텍처 계층 분리"]
        )

        # 자동화 권고사항
        plan["automation_recommendations"].extend(
            [
                "pre-commit hook 설정으로 코드 품질 자동 검사",
                "CI/CD 파이프라인에 메트릭 체크 추가",
                "정기적인 리팩토링 보고서 생성 자동화",
            ]
        )

        return plan


def main():
    """메인 실행 함수"""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    analyzer = CodeMetricsAnalyzer(project_root)
    metrics = analyzer.analyze_project()

    # 보고서 생성
    report = analyzer.generate_report(metrics)

    # 액션 플랜 생성
    planner = RefactoringPlanner(metrics)
    action_plan = planner.generate_action_plan()

    # 결과 저장
    docs_dir = Path(project_root) / "docs"
    docs_dir.mkdir(exist_ok=True)

    # 보고서 파일
    with open(docs_dir / "CODE_METRICS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)

    # 메트릭 JSON
    with open(docs_dir / "code_metrics.json", "w", encoding="utf-8") as f:
        json.dump([asdict(m) for m in metrics], f, indent=2, ensure_ascii=False)

    # 액션 플랜 JSON
    with open(docs_dir / "refactoring_action_plan.json", "w", encoding="utf-8") as f:
        json.dump(action_plan, f, indent=2, ensure_ascii=False)

    print(f"✅ 리팩토링 보고서가 생성되었습니다:")
    print(f"📊 메트릭 보고서: {docs_dir / 'CODE_METRICS_REPORT.md'}")
    print(f"📈 메트릭 데이터: {docs_dir / 'code_metrics.json'}")
    print(f"📋 액션 플랜: {docs_dir / 'refactoring_action_plan.json'}")


if __name__ == "__main__":
    main()
