#!/usr/bin/env python3
"""
DantaroWallet Pro - 일일 개발 로그 자동 생성 도구

사용법:
    python scripts/daily_log.py "오늘 완성한 기능 설명"
    python scripts/daily_log.py --template  # 템플릿만 생성
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def get_project_stats():
    """프로젝트 현황 통계 수집"""
    project_root = Path(__file__).parent.parent
    app_path = project_root / "app"

    # Python 파일 수
    py_files = list(app_path.rglob("*.py"))

    # API 엔드포인트 수 (대략적 계산)
    api_files = list((app_path / "api").rglob("*.py"))

    # 테스트 파일 수
    test_files = list((project_root / "tests").rglob("test_*.py"))

    return {
        "python_files": len(py_files),
        "api_files": len(api_files),
        "test_files": len(test_files),
        "total_lines": sum(
            len(f.read_text().splitlines()) for f in py_files if f.is_file()
        ),
    }


def get_git_status():
    """Git 변경사항 확인"""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True
        )
        changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
        return len(changes)
    except:
        return "N/A"


def create_daily_log_entry(description="", is_template=False):
    """일일 로그 엔트리 생성"""
    today = datetime.now().strftime("%Y년 %m월 %d일")
    stats = get_project_stats()
    changes = get_git_status()

    if is_template:
        description = "[오늘 완성한 주요 기능이나 해결한 문제를 작성하세요]"
        problems_solved = "[해결한 기술적 문제들을 작성하세요]"
        test_results = "[테스트 결과를 작성하세요]"
        next_plan = "[다음 작업 계획을 작성하세요]"
    else:
        problems_solved = "[해결한 문제가 있다면 작성하세요]"
        test_results = "[테스트를 실행했다면 결과를 작성하세요]"
        next_plan = "[다음 작업 계획이 있다면 작성하세요]"

    entry = f"""
## 📅 {today}

### 🎯 주요 성과
{description}

### 🔧 해결된 문제들
{problems_solved}

### 📊 프로젝트 현황
- **Python 파일 수**: {stats['python_files']}개
- **API 파일 수**: {stats['api_files']}개
- **테스트 파일 수**: {stats['test_files']}개
- **전체 코드 라인**: 약 {stats['total_lines']:,}줄
- **Git 변경사항**: {changes}개 파일

### 🧪 테스트 결과
{test_results}

### 🎯 다음 계획
{next_plan}

### 🔍 기술적 의사결정
[중요한 기술적 결정이 있었다면 작성하세요]

---
"""

    return entry


def update_development_log(entry):
    """DEVELOPMENT_LOG.md 파일 업데이트"""
    project_root = Path(__file__).parent.parent
    log_file = project_root / "docs" / "DEVELOPMENT_LOG.md"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        # 첫 번째 "---" 다음에 새 엔트리 삽입
        lines = content.split("\n")
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.strip() == "---" and i > 10:  # 헤더 이후의 첫 번째 ---
                insert_pos = i + 1
                break

        lines.insert(insert_pos, entry)
        new_content = "\n".join(lines)
        log_file.write_text(new_content, encoding="utf-8")
    else:
        # 파일이 없으면 새로 생성
        header = """# DantaroWallet Pro - 개발 로그

## 📋 앞으로의 기록 규칙

### 🔄 매일 기록할 항목
1. **완료된 작업** - 구체적인 기능 및 코드 변경사항
2. **해결된 문제** - 문제 상황, 원인, 해결 방법
3. **테스트 결과** - 통과/실패 현황 및 수치
4. **기술적 의사결정** - 왜 이 방법을 선택했는지
5. **다음 계획** - 명확한 다음 단계

---
"""
        log_file.write_text(header + entry, encoding="utf-8")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--template":
            entry = create_daily_log_entry(is_template=True)
            print("📝 일일 로그 템플릿이 생성되었습니다:")
            print(entry)

            # 파일에도 저장
            update_development_log(entry)
            print("✅ DEVELOPMENT_LOG.md 파일에 템플릿이 추가되었습니다.")
            print("📝 템플릿을 편집하여 오늘의 개발 내용을 기록하세요.")

        else:
            description = " ".join(sys.argv[1:])
            entry = create_daily_log_entry(description)
            update_development_log(entry)
            print(f"✅ 일일 로그가 업데이트되었습니다: {description}")
    else:
        print("사용법:")
        print('  python scripts/daily_log.py "오늘 완성한 기능 설명"')
        print("  python scripts/daily_log.py --template")


if __name__ == "__main__":
    main()
