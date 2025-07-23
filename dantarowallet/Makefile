.PHONY: help install dev test lint format clean db-init db-migrate db-upgrade db-downgrade db-history metrics refactor-check refactor-plan pre-commit quality-gate

help:
	@echo "Available commands:"
	@echo "  install          Install dependencies"
	@echo "  dev              Run development server"
	@echo "  test             Run tests"
	@echo "  lint             Run linters"
	@echo "  format           Format code"
	@echo "  clean            Clean up"
	@echo "  db-init          Initialize database"
	@echo "  db-migrate       Create migration (usage: make db-migrate m='message')"
	@echo "  db-upgrade       Upgrade database to head"
	@echo "  db-downgrade     Downgrade database by one version"
	@echo "  db-history       Show database migration history"
	@echo ""
	@echo "Refactoring & Quality:"
	@echo "  metrics          Generate code metrics report"
	@echo "  refactor-check   Check which files need refactoring"
	@echo "  refactor-plan    Generate refactoring action plan"
	@echo "  pre-commit       Run pre-commit quality checks"
	@echo "  quality-gate     Run comprehensive quality gate"

install:
	poetry install

dev:
	docker-compose up -d postgres redis
	poetry run uvicorn app.main:app --reload

test:
	poetry run pytest -v --cov=app

lint:
	poetry run flake8 app tests
	poetry run mypy app

format:
	poetry run black app tests

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v

db-init:
	poetry run python scripts/init_db.py

db-migrate:
	poetry run alembic revision --autogenerate -m "$(m)"

db-upgrade:
	poetry run alembic upgrade head

db-downgrade:
	poetry run alembic downgrade -1

db-history:
	poetry run alembic history

# Refactoring & Quality Commands
metrics:
	@echo "📊 Generating code metrics report..."
	poetry run python scripts/refactoring_monitor.py

refactor-check:
	@echo "🔍 Checking files that need refactoring..."
	poetry run python scripts/refactoring_monitor.py
	@echo "📋 Check docs/CODE_METRICS_REPORT.md for detailed analysis"

refactor-plan:
	@echo "📋 Generating refactoring action plan..."
	poetry run python scripts/refactoring_monitor.py
	@echo "📝 Action plan generated in docs/refactoring_action_plan.json"

pre-commit:
	@echo "🚀 Running pre-commit quality checks..."
	poetry run python scripts/pre_commit_check.py

quality-gate:
	@echo "🏗️ Running comprehensive quality gate..."
	@make lint
	@make test
	@make metrics
	@make pre-commit
	@echo "✅ Quality gate completed"

# Install quality tools
install-quality-tools:
	poetry add --group dev radon bandit isort black mypy flake8
	@echo "✅ Quality tools installed"

# 개발 시 자동 품질 검사 명령어들
auto-fix:
	@echo "🔧 자동 코드 수정 시작..."
	poetry run black app tests scripts
	poetry run isort app tests scripts
	@echo "✅ 자동 수정 완료!"

auto-check:
	@echo "🔍 코드 품질 검사 시작..."
	poetry run black --check app tests scripts
	poetry run isort --check-only app tests scripts
	poetry run flake8 app tests scripts
	poetry run mypy app
	poetry run bandit -r app/
	@echo "✅ 품질 검사 완료!"

dev-check: auto-fix auto-check test
	@echo "🚀 개발 전 모든 검사 완료! 개발 시작하세요."

build-test:
	@echo "🏗️ 빌드 테스트 시작..."
	poetry check
	poetry run python -m app.main --help > /dev/null 2>&1 || echo "❌ 앱 로드 실패"
	poetry run pytest tests/test_app.py::test_app_startup -v
	@echo "✅ 빌드 테스트 완료!"

pre-dev: install auto-fix auto-check build-test
	@echo "🎯 개발 환경 준비 완료!"
	@echo "   ✅ 의존성 설치"
	@echo "   ✅ 코드 자동 수정"
	@echo "   ✅ 품질 검사"
	@echo "   ✅ 빌드 테스트"
	@echo "🚀 이제 'make dev'로 서버를 시작하세요!"

watch-dev:
	@echo "👀 개발 모드: 파일 변경 시 자동 검사"
	poetry run watchdog --recursive --ignore-directories=__pycache__ --ignore-directories=.git --patterns="*.py" --command="make auto-fix && make auto-check" app/
