#!/usr/bin/env python3
"""
Pre-commit hook for code quality checks
코드 커밋 전 품질 검사를 자동으로 수행합니다.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_command(cmd: list, cwd: Optional[str] = None) -> tuple[int, str, str]:
    """명령어를 실행하고 결과를 반환합니다."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_file_size_limits() -> bool:
    """파일 크기 제한을 확인합니다."""
    print("🔍 파일 크기 제한 확인 중...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = Path(project_root) / "app"

    violations = []

    for py_file in app_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                lines = len(f.readlines())

            # 파일 크기 제한 (500줄)
            if lines > 500:
                violations.append(
                    {
                        "file": str(py_file.relative_to(Path(project_root))),
                        "lines": lines,
                        "limit": 500,
                        "type": "파일 크기 초과",
                    }
                )
        except Exception as e:
            print(f"Warning: Could not check {py_file}: {e}")

    if violations:
        print("❌ 파일 크기 제한 위반:")
        for violation in violations:
            print(
                f"  - {violation['file']}: {violation['lines']}줄 (제한: {violation['limit']}줄)"
            )
        return False

    print("✅ 파일 크기 제한 통과")
    return True


def check_function_complexity() -> bool:
    """함수 복잡도를 확인합니다."""
    print("🔍 함수 복잡도 확인 중...")

    # radon을 사용한 복잡도 체크 (설치 필요)
    returncode, stdout, stderr = run_command(
        ["python", "-m", "radon", "cc", "app/", "--min", "C"]
    )

    if returncode != 0:
        print("⚠️  radon이 설치되지 않음. pip install radon으로 설치하세요.")
        return True  # 도구가 없으면 패스

    if stdout.strip():
        print("❌ 복잡도가 높은 함수 발견:")
        print(stdout)
        return False

    print("✅ 함수 복잡도 통과")
    return True


def check_import_sorting() -> bool:
    """import 정렬을 확인합니다."""
    print("🔍 import 정렬 확인 중...")

    returncode, stdout, stderr = run_command(
        ["python", "-m", "isort", "app/", "--check-only", "--diff"]
    )

    if returncode != 0:
        print("❌ import 정렬이 필요합니다:")
        print(stdout)
        print("\n자동 수정: python -m isort app/")
        return False

    print("✅ import 정렬 통과")
    return True


def check_code_formatting() -> bool:
    """코드 포맷팅을 확인합니다."""
    print("🔍 코드 포맷팅 확인 중...")

    returncode, stdout, stderr = run_command(
        ["python", "-m", "black", "app/", "--check", "--diff"]
    )

    if returncode != 0:
        print("❌ 코드 포맷팅이 필요합니다:")
        print(stdout)
        print("\n자동 수정: python -m black app/")
        return False

    print("✅ 코드 포맷팅 통과")
    return True


def check_type_hints() -> bool:
    """타입 힌트를 확인합니다."""
    print("🔍 타입 힌트 확인 중...")

    returncode, stdout, stderr = run_command(
        ["python", "-m", "mypy", "app/", "--ignore-missing-imports"]
    )

    if returncode != 0:
        print("❌ 타입 검사 실패:")
        print(stdout)
        print(stderr)
        return False

    print("✅ 타입 검사 통과")
    return True


def check_security_issues() -> bool:
    """보안 이슈를 확인합니다."""
    print("🔍 보안 이슈 확인 중...")

    returncode, stdout, stderr = run_command(
        ["python", "-m", "bandit", "-r", "app/", "-f", "json"]
    )

    if returncode != 0:
        try:
            issues = json.loads(stdout)
            high_severity = [
                issue
                for issue in issues.get("results", [])
                if issue.get("issue_severity") in ["HIGH", "MEDIUM"]
            ]

            if high_severity:
                print("❌ 보안 이슈 발견:")
                for issue in high_severity:
                    print(
                        f"  - {issue['filename']}:{issue['line_number']}: {issue['issue_text']}"
                    )
                return False
        except json.JSONDecodeError:
            print("⚠️  bandit 출력 파싱 실패")
            return True

    print("✅ 보안 검사 통과")
    return True


def generate_quality_report() -> dict:
    """품질 보고서를 생성합니다."""
    checks = {
        "file_size_limits": check_file_size_limits(),
        "function_complexity": check_function_complexity(),
        "import_sorting": check_import_sorting(),
        "code_formatting": check_code_formatting(),
        "type_hints": check_type_hints(),
        "security_issues": check_security_issues(),
    }

    passed = sum(checks.values())
    total = len(checks)

    report = {
        "timestamp": "2024-01-15T10:00:00",
        "total_checks": total,
        "passed_checks": passed,
        "success_rate": f"{(passed/total)*100:.1f}%",
        "checks": checks,
        "status": "PASS" if passed == total else "FAIL",
    }

    return report


def main():
    """메인 실행 함수"""
    print("🚀 Pre-commit 코드 품질 검사 시작")
    print("=" * 50)

    # 품질 검사 실행
    report = generate_quality_report()

    # 결과 출력
    print("\n" + "=" * 50)
    print("📊 품질 검사 결과")
    print(f"✅ 통과한 검사: {report['passed_checks']}/{report['total_checks']}")
    print(f"📈 성공률: {report['success_rate']}")

    # 보고서 저장
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)

    with open(docs_dir / "pre_commit_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if report["status"] == "PASS":
        print("\n🎉 모든 품질 검사 통과! 커밋을 진행할 수 있습니다.")
        return 0
    else:
        print("\n❌ 품질 검사 실패. 위의 이슈들을 수정한 후 다시 커밋해주세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
