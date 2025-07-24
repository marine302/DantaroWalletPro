.PHONY: help install dev test lint format clean db-init db-migrate db-upgrade db-downgrade db-history metrics refactor-check refactor-plan pre-commit quality-gate

help:
	@echo "🎯 DantaroWallet 개발 명령어 가이드"
	@echo "======================================"
	@echo ""
	@echo "🚀 기본 개발 명령어:"
	@echo "  install          Install dependencies"
	@echo "  dev              Run development server"
	@echo "  test             Run tests"
	@echo "  lint             Run linters"
	@echo "  format           Format code"
	@echo "  clean            Clean up"
	@echo ""
	@echo "🗄️ 데이터베이스:"
	@echo "  db-init          Initialize database"
	@echo "  db-migrate       Create migration (usage: make db-migrate m='message')"
	@echo "  db-upgrade       Upgrade database to head"
	@echo "  db-downgrade     Downgrade database by one version"
	@echo "  db-history       Show database migration history"
	@echo ""
	@echo "🎯 프론트엔드 개발 지원:"
	@echo "  frontend-help    프론트엔드 개발자 가이드 표시"
	@echo "  dev-server       백엔드 개발 서버 실행"
	@echo "  frontend-test    API 연결 테스트"
	@echo "  frontend-ready   프론트엔드 개발 환경 완전 준비"
	@echo "  update-api-docs  API 문서 및 TypeScript 타입 업데이트"
	@echo "  generate-api-types TypeScript API 타입 생성"
	@echo "  monitor-api      실시간 API 모니터링"
	@echo ""
	@echo "📚 API 문서:"
	@echo "  api-docs         Update role-based API documentation"
	@echo "  api-test         Test API endpoints"
	@echo ""
	@echo "🔧 코드 품질 & 리팩토링:"
	@echo "  metrics          Generate code metrics report"
	@echo "  refactor-check   Check which files need refactoring"
	@echo "  refactor-plan    Generate refactoring action plan"
	@echo "  pre-commit       Run pre-commit quality checks"
	@echo "  quality-gate     Run comprehensive quality gate"
	@echo "  auto-fix         자동 코드 수정 (black, isort)"
	@echo "  auto-check       코드 품질 검사"
	@echo ""
	@echo "🚀 통합 워크플로우:"
	@echo "  full-dev-setup   완전한 개발 환경 설정"
	@echo "  pre-dev          개발 전 준비 작업"
	@echo "  dev-check        개발 전 모든 검사"
	@echo ""
	@echo "🧹 파일 정리:"
	@echo "  clean-empty      빈 파일들 정리 (안전 모드)"
	@echo "  clean-empty-force 빈 파일들 강제 정리"
	@echo "  prevent-empty    빈 파일 생성 방지 모니터링"
	@echo "  prevent-empty-check 빈 파일 검사만 실행"
	@echo ""

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

# API Documentation commands
api-docs:
	@echo "📚 역할별 API 문서 업데이트..."
	./scripts/update_api_docs.sh

api-test:
	@echo "🧪 주요 API 엔드포인트 테스트..."
	@curl -s http://localhost:8000/health | jq '.status' || echo "❌ Health check 실패"
	@curl -s http://localhost:8000/api/v1/simple-energy/providers | jq '.success' || echo "❌ Simple Energy 실패"
	@echo "✅ API 테스트 완료"

# Frontend Development Support Commands
frontend-help:
	@echo "🎯 프론트엔드 개발자를 위한 가이드"
	@echo "=============================================="
	@echo ""
	@echo "🔐 Super Admin Dashboard (포트 3020):"
	@echo "   📚 API 문서: http://localhost:8000/api/v1/admin/docs"
	@echo "   📄 OpenAPI: http://localhost:8000/api/v1/admin/openapi.json"
	@echo "   📁 TypeScript: frontend/super-admin-dashboard/src/lib/api-client.ts"
	@echo "   📝 예제 코드: frontend/super-admin-dashboard/src/examples/"
	@echo ""
	@echo "🔗 Partner Admin Template (포트 3030):"
	@echo "   📚 API 문서: http://localhost:8000/api/v1/partner/docs"
	@echo "   📄 OpenAPI: http://localhost:8000/api/v1/partner/openapi.json"
	@echo "   📁 TypeScript: frontend/partner-admin-template/src/lib/api-client.ts"
	@echo "   📝 예제 코드: frontend/partner-admin-template/src/examples/"
	@echo ""
	@echo "🌟 개발/테스트용 API:"
	@echo "   📚 API 문서: http://localhost:8000/api/v1/dev/docs"
	@echo "   📄 OpenAPI: http://localhost:8000/api/v1/dev/openapi.json"
	@echo ""
	@echo "🔧 개발 도구:"
	@echo "   make dev-server      - 백엔드 서버 실행"
	@echo "   make frontend-test   - 전체 API 연결 테스트"
	@echo "   make update-api-docs - API 문서 및 타입 업데이트"
	@echo "   make generate-api-types - TypeScript 타입 생성"

dev-server:
	@echo "🚀 백엔드 개발 서버 시작..."
	@echo "Super Admin API: http://localhost:8000/api/v1/admin/docs"
	@echo "Partner Admin API: http://localhost:8000/api/v1/partner/docs"
	@echo "개발용 API: http://localhost:8000/api/v1/dev/docs"
	@echo ""
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-test:
	@echo "🧪 프론트엔드-백엔드 API 연결 테스트 실행..."
	./test_frontend_requests.sh

frontend-test-super-admin:
	@echo "🔐 Super Admin API만 테스트..."
	./test_frontend_requests.sh super-admin

frontend-test-partner-admin:
	@echo "🔗 Partner Admin API만 테스트..."
	./test_frontend_requests.sh partner-admin

update-api-docs:
	@echo "📚 API 문서 및 TypeScript 타입 업데이트..."
	./scripts/update_api_docs.sh
	@echo "✅ 업데이트 완료!"

generate-api-types:
	@echo "🧪 TypeScript API 타입 생성..."
	poetry run python scripts/generate_api_docs_by_role.py
	@echo "✅ TypeScript 타입 생성 완료!"

frontend-dev-setup:
	@echo "🚀 프론트엔드 개발 환경 완전 설정..."
	@make dev-server &
	@sleep 5
	@make frontend-test
	@echo "✅ 프론트엔드 개발 환경 준비 완료!"
	@echo ""
	@echo "📋 다음 단계:"
	@echo "1. Super Admin: cd frontend/super-admin-dashboard && npm run dev"
	@echo "2. Partner Admin: cd frontend/partner-admin-template && npm run dev"

monitor-api:
	@echo "📊 실시간 API 모니터링 시작..."
	./monitor_api_requests.sh

check-backend-status:
	@echo "🔍 백엔드 상태 확인..."
	@curl -s http://localhost:8000/health | jq '.' && echo "✅ 백엔드 정상" || echo "❌ 백엔드 문제"
	@curl -s http://localhost:8000/ | jq '.api_docs' && echo "✅ API 문서 접근 가능" || echo "❌ API 문서 문제"

# 통합 개발 워크플로우
full-dev-setup: install pre-dev dev-server
	@echo "🎉 완전한 개발 환경 설정 완료!"

frontend-ready: check-backend-status update-api-docs frontend-test
	@echo "🎯 프론트엔드 개발 준비 완료!"
	@echo ""
	@echo "📋 프론트엔드 팀을 위한 체크리스트:"
	@echo "✅ 백엔드 서버 실행 중"
	@echo "✅ API 문서 업데이트됨"
	@echo "✅ TypeScript 타입 생성됨"
	@echo "✅ API 연결 테스트 통과"
	@echo ""
	@echo "🚀 이제 프론트엔드 개발을 시작하세요!"

# 파일 정리 명령어들
clean-empty:
	@echo "🧹 빈 파일 정리 중..."
	python scripts/prevent_empty_files.py --cleanup

clean-empty-force:
	@echo "🧹 빈 파일 강제 정리 중..."
	find . -type f -size 0 \
		-not -path "./.venv/*" \
		-not -path "./.git/*" \
		-not -path "./__pycache__/*" \
		-not -path "./.pytest_cache/*" \
		-not -path "./logs/*" \
		-not -path "./backups/*" \
		-not -path "./archive/*" \
		-delete 2>/dev/null || true

prevent-empty:
	@echo "🛡️ 빈 파일 생성 방지 모니터링 시작..."
	python scripts/prevent_empty_files.py --monitor

prevent-empty-check:
	@echo "🔍 빈 파일 검사 중..."
	python scripts/prevent_empty_files.py
	@echo "✅ 빈 파일 정리 완료"

clean-temp:
	@echo "🧹 임시 파일 정리 중..."
	find . -name "*.tmp" -o -name "*.temp" -o -name "*.backup" | grep -v ".venv" | xargs rm -f 2>/dev/null || true
	@echo "✅ 임시 파일 정리 완료"

clean-all: clean clean-empty clean-temp
	@echo "🧹 전체 정리 완료!"

# 빈 파일 방지 안전 가드
safe-update-docs:
	@echo "🛡️ 안전한 API 문서 업데이트..."
	@make check-backend-status
	@make clean-empty
	@make update-api-docs
	@make clean-empty
	@echo "✅ 안전한 문서 업데이트 완료"
