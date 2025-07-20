#!/bin/bash

# DantaroWallet 개발 환경 통합 관리 스크립트
# 모든 개발 환경 설정, 서버 관리, 문제 해결을 한 곳에서 처리
# 
# 🤖 AI 개발자님!
# 새로운 세션이면 먼저 ./dev-manager.sh guide 를 실행해서 가이드를 읽어주세요!
# 기획자님은 기술적 세부사항을 기억하지 않으니 모든 것을 자동화해주세요!

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/dantarowallet"
FRONTEND_SUPER_DIR="$PROJECT_ROOT/frontend/super-admin-dashboard"
FRONTEND_PARTNER_DIR="$PROJECT_ROOT/frontend/partner-admin-template"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_header() { echo -e "${CYAN}========== $1 ==========${NC}"; }

function show_help() {
    echo -e "${CYAN}DantaroWallet 개발 환경 통합 관리 스크립트${NC}"
    echo ""
    echo "🚀 주요 명령어:"
    echo "  auto            완전 자동화 - 환경 설정부터 서버 시작까지 모든 것"
    echo "  setup           개발 환경 초기 설정 (Python, Node.js, 패키지 설치)"
    echo "  start           모든 개발 서버 시작"
    echo "  stop            모든 개발 서버 중지"
    echo "  restart         모든 서버 재시작"
    echo ""
    echo "🔧 유틸리티:"
    echo "  health          환경 건강성 검사"
    echo "  ports           포트 관리 (상태, 정리, 충돌 해결)"
    echo "  clean           불필요한 파일 정리"
    echo "  status          서버 상태 확인"
    echo "  test            API 연결 테스트"
    echo ""
    echo "🎯 개별 제어:"
    echo "  backend         백엔드만 시작 (포트 8000)"
    echo "  backend-only    백엔드 개발 모드 (프론트엔드 건드리지 않음)"
    echo "  super           Super Admin 프론트엔드만 시작 (포트 3020)"
    echo "  partner         Partner Admin 프론트엔드만 시작 (포트 3030)"
    echo ""
    echo "🤖 AI 개발자용:"
    echo "  guide           영구 개발 가이드 보기"
    echo "  memo            중요 사항 메모"
    echo ""
    echo "💡 예시:"
    echo "  $0 auto         # 완전 자동화 (추천)"
    echo "  $0 backend-only # 백엔드만 개발 (간단함)"
    echo "  $0 setup        # 처음 설정"
    echo "  $0 status       # 상태 확인"
    echo "  $0 health       # 환경 검사"
}

# =============================================================================
# 완전 자동화 기능 (메인 기능)
# =============================================================================

function auto_everything() {
    log_header "🚀 DantaroWallet 완전 자동화 시작"
    
    echo "다음을 수행합니다:"
    echo "1. 환경 건강성 검사"
    echo "2. 문제 발견 시 자동 수정"  
    echo "3. 포트 정리"
    echo "4. 모든 서버 시작"
    echo "5. 브라우저 자동 접속"
    echo ""
    
    # 1. 환경 검사
    if ! check_environment_health; then
        log_warning "환경에 문제가 있습니다. 자동 수정을 시도합니다..."
        setup_development_environment
    fi
    
    # 2. 포트 정리
    cleanup_ports
    
    # 3. 서버 시작
    start_all_servers
    
    # 4. 브라우저 접속
    open_browsers
    
    # 5. VS Code 열기
    open_vscode
    
    log_success "🎉 완전 자동화 완료! 개발 환경이 준비되었습니다."
}

# =============================================================================
# 환경 설정 기능
# =============================================================================

function setup_development_environment() {
    log_header "🔧 개발 환경 설정"
    
    # Python 환경 설정
    setup_python_environment
    
    # Node.js 환경 설정  
    setup_nodejs_environment
    
    # 데이터베이스 초기화
    setup_database
    
    # 환경 변수 설정
    setup_environment_files
    
    log_success "개발 환경 설정 완료"
}

function setup_python_environment() {
    log_info "Python 환경 설정 중..."
    cd "$BACKEND_DIR"
    
    # 기존 가상환경 제거 후 재생성
    if [[ -d ".venv" ]]; then
        log_info "기존 가상환경 제거 중..."
        rm -rf .venv
    fi
    
    # 새 가상환경 생성
    python3 -m venv .venv
    source .venv/bin/activate
    
    # pip 업그레이드 및 패키지 설치
    python -m pip install --upgrade pip
    
    if [[ -f "pyproject.toml" ]]; then
        pip install -e .
    else
        pip install fastapi uvicorn sqlalchemy alembic python-multipart python-jose[cryptography] passlib[bcrypt] python-dotenv aiosqlite
    fi
    
    # 개발 도구 설치
    pip install pytest httpx black isort flake8
    
    log_success "Python 환경 설정 완료"
}

function setup_nodejs_environment() {
    log_info "Node.js 환경 설정 중..."
    
    # Super Admin Dashboard
    if [[ -d "$FRONTEND_SUPER_DIR" ]]; then
        log_info "Super Admin Dashboard 설정 중..."
        cd "$FRONTEND_SUPER_DIR"
        [[ -d "node_modules" ]] && rm -rf node_modules
        [[ -f "package-lock.json" ]] && rm -f package-lock.json
        npm install
        
        # .env.local 생성
        if [[ ! -f ".env.local" ]]; then
            cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Super Admin Dashboard
PORT=3020
EOF
        fi
    fi
    
    # Partner Admin Template
    if [[ -d "$FRONTEND_PARTNER_DIR" ]]; then
        log_info "Partner Admin Template 설정 중..."
        cd "$FRONTEND_PARTNER_DIR"
        [[ -d "node_modules" ]] && rm -rf node_modules
        [[ -f "package-lock.json" ]] && rm -f package-lock.json
        npm install
        
        # .env.local 생성
        if [[ ! -f ".env.local" ]]; then
            cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Partner Admin Template
PORT=3030
EOF
        fi
    fi
    
    log_success "Node.js 환경 설정 완료"
}

function setup_database() {
    log_info "데이터베이스 설정 중..."
    cd "$BACKEND_DIR"
    
    # 기존 DB 제거
    [[ -f "dev.db" ]] && rm -f dev.db
    
    # 가상환경에서 마이그레이션 실행
    source .venv/bin/activate
    alembic upgrade 7a5993b11637  # 기본 마이그레이션만
    
    log_success "데이터베이스 설정 완료"
}

function setup_environment_files() {
    log_info "환경 변수 파일 설정 중..."
    cd "$BACKEND_DIR"
    
    if [[ ! -f ".env" && -f ".env.example" ]]; then
        cp .env.example .env
        log_success ".env 파일 생성됨"
    fi
    
    # VS Code 워크스페이스 생성
    if [[ ! -f "$PROJECT_ROOT/DantaroWalletPro.code-workspace" ]]; then
        cat > "$PROJECT_ROOT/DantaroWalletPro.code-workspace" << 'EOF'
{
    "folders": [
        { "name": "Backend", "path": "./dantarowallet" },
        { "name": "Super Admin", "path": "./frontend/super-admin-dashboard" },
        { "name": "Partner Admin", "path": "./frontend/partner-admin-template" },
        { "name": "Root", "path": "." }
    ],
    "settings": {
        "python.defaultInterpreterPath": "./dantarowallet/.venv/bin/python"
    }
}
EOF
        log_success "VS Code 워크스페이스 생성됨"
    fi
}

# =============================================================================
# 서버 관리 기능
# =============================================================================

function start_all_servers() {
    log_header "🚀 모든 서버 시작"
    
    # 백엔드 시작
    start_backend_server
    sleep 3
    
    # 프론트엔드들 시작
    start_super_admin_server
    sleep 2
    start_partner_admin_server
    
    log_success "모든 서버가 시작되었습니다"
    show_server_urls
}

function start_backend_server() {
    # 먼저 백엔드 서버가 이미 실행 중인지 확인
    if curl -s --max-time 3 http://localhost:8000/health > /dev/null 2>&1; then
        log_success "백엔드 서버가 이미 실행 중입니다 (포트 8000)"
        echo "   🔧 API 문서: http://localhost:8000/docs"
        echo "   ❤️ Health 체크: http://localhost:8000/health"
        return 0
    fi
    
    # 포트는 사용 중이지만 응답하지 않는 경우 정리
    if lsof -ti:8000 > /dev/null 2>&1; then
        log_warning "포트 8000이 사용 중이지만 응답하지 않습니다. 정리 중..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    log_info "백엔드 서버 시작 중... (포트 8000)"
    cd "$BACKEND_DIR"
    
    # 가상환경 확인
    if [[ ! -d ".venv" ]]; then
        log_error "Python 가상환경이 없습니다. setup을 먼저 실행하세요."
        return 1
    fi
    
    # 가상환경 활성화 및 필수 패키지 설치 확인
    source .venv/bin/activate
    
    # mnemonic과 hdwallet 패키지가 설치되어 있는지 확인
    if ! python -c "import mnemonic, hdwallet" > /dev/null 2>&1; then
        log_info "필수 패키지 설치 중..."
        pip install mnemonic hdwallet > /dev/null 2>&1
    fi
    
    # 새 터미널에서 서버 시작
    osascript -e "tell application \"Terminal\" to do script \"cd '$BACKEND_DIR' && source .venv/bin/activate && echo '🐍 백엔드 서버 시작 중...' && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000\""
    
    # 서버가 시작될 때까지 잠시 대기
    log_info "서버 시작 대기 중..."
    for i in {1..10}; do
        sleep 2
        if curl -s --max-time 2 http://localhost:8000/health > /dev/null 2>&1; then
            log_success "백엔드 서버가 성공적으로 시작되었습니다!"
            echo "   🔧 API 문서: http://localhost:8000/docs"
            echo "   ❤️ Health 체크: http://localhost:8000/health"
            return 0
        fi
        echo "   대기 중... ($i/10)"
    done
    
    log_warning "서버가 시작되었지만 응답 확인에 시간이 걸립니다. 터미널을 확인해주세요."
}

function start_super_admin_server() {
    if [[ -d "$FRONTEND_SUPER_DIR" ]]; then
        log_info "Super Admin Dashboard 시작 중... (포트 3020)"
        osascript -e "tell application \"Terminal\" to do script \"cd '$FRONTEND_SUPER_DIR' && echo '⚛️ Super Admin 시작 중...' && npm run dev\""
    fi
}

function start_partner_admin_server() {
    if [[ -d "$FRONTEND_PARTNER_DIR" ]]; then
        log_info "Partner Admin Template 시작 중... (포트 3030)"
        osascript -e "tell application \"Terminal\" to do script \"cd '$FRONTEND_PARTNER_DIR' && echo '⚛️ Partner Admin 시작 중...' && npm run dev\""
    fi
}

function stop_all_servers() {
    log_header "🛑 모든 서버 중지"
    
    # 포트별로 프로세스 종료
    for port in 8000 3020 3030; do
        if lsof -ti:$port > /dev/null 2>&1; then
            log_info "포트 $port 프로세스 종료 중..."
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    # Node.js 개발 서버들 종료
    pkill -f "next-server" 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    
    log_success "모든 서버가 중지되었습니다"
}

function restart_all_servers() {
    log_header "🔄 모든 서버 재시작"
    stop_all_servers
    sleep 2
    start_all_servers
}

function show_server_urls() {
    echo ""
    echo -e "${GREEN}📍 서비스 접속 주소:${NC}"
    echo -e "   🔧 API 문서: ${CYAN}http://localhost:8000/docs${NC}"
    echo -e "   🔒 Super Admin: ${CYAN}http://localhost:3020${NC}"
    echo -e "   👥 Partner Admin: ${CYAN}http://localhost:3030${NC}"
    echo ""
}

# =============================================================================
# 포트 관리 기능
# =============================================================================

function cleanup_ports() {
    log_info "포트 정리 중..."
    
    # 개발 서버 포트들 정리
    for port in 8000 3020 3030; do
        if lsof -ti:$port > /dev/null 2>&1; then
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
    
    # 관련 프로세스들 정리
    pkill -f "next-server" 2>/dev/null || true
    pkill -f "uvicorn" 2>/dev/null || true
    
    sleep 1
    log_success "포트 정리 완료"
}

function check_ports() {
    log_header "🔌 포트 사용 현황"
    
    PORTS=(8000 3020 3030)
    NAMES=("백엔드" "Super Admin" "Partner Admin")
    
    for i in "${!PORTS[@]}"; do
        PORT=${PORTS[$i]}
        NAME=${NAMES[$i]}
        
        if lsof -ti:$PORT > /dev/null 2>&1; then
            echo -e "$NAME (포트 $PORT): ${RED}사용 중${NC}"
        else
            echo -e "$NAME (포트 $PORT): ${GREEN}사용 가능${NC}"
        fi
    done
    echo ""
}

# =============================================================================
# 환경 검사 기능
# =============================================================================

function check_environment_health() {
    log_header "🏥 환경 건강성 검사"
    
    local errors=0
    
    # Python 환경 검사
    if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
        log_error "Python 가상환경이 없습니다"
        ((errors++))
    else
        cd "$BACKEND_DIR"
        if ! source .venv/bin/activate 2>/dev/null; then
            log_error "Python 가상환경을 활성화할 수 없습니다"
            ((errors++))
        else
            if ! python -c "import fastapi" 2>/dev/null; then
                log_error "FastAPI가 설치되지 않았습니다"
                ((errors++))
            fi
        fi
    fi
    
    # Node.js 환경 검사
    if ! command -v node &> /dev/null; then
        log_error "Node.js가 설치되지 않았습니다"
        ((errors++))
    fi
    
    # 프론트엔드 패키지 검사
    for dir in "$FRONTEND_SUPER_DIR" "$FRONTEND_PARTNER_DIR"; do
        if [[ -d "$dir" && ! -d "$dir/node_modules" ]]; then
            log_error "$(basename "$dir")의 node_modules가 없습니다"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log_success "환경이 정상입니다"
        return 0
    else
        log_warning "$errors개의 문제가 발견되었습니다"
        return 1
    fi
}

# =============================================================================
# 브라우저 및 도구 실행
# =============================================================================

function open_browsers() {
    log_info "브라우저에서 서비스 열기..."
    sleep 5  # 서버 시작 대기
    
    open "http://localhost:8000/docs" 2>/dev/null || true
    sleep 1
    open "http://localhost:3020" 2>/dev/null || true  
    sleep 1
    open "http://localhost:3030" 2>/dev/null || true
}

function open_vscode() {
    if command -v code &> /dev/null; then
        log_info "VS Code 워크스페이스 열기..."
        code "$PROJECT_ROOT/DantaroWalletPro.code-workspace" 2>/dev/null || true
    fi
}

# =============================================================================
# 상태 확인 및 테스트
# =============================================================================

function check_server_status() {
    log_header "📊 서버 상태 확인"
    
    # 백엔드 상태
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "백엔드: ${GREEN}실행 중${NC} (http://localhost:8000)"
    else
        echo -e "백엔드: ${RED}중지됨${NC}"
    fi
    
    # 프론트엔드 상태들
    for port in 3020 3030; do
        if curl -s http://localhost:$port > /dev/null 2>&1; then
            echo -e "프론트엔드 ($port): ${GREEN}실행 중${NC} (http://localhost:$port)"
        else
            echo -e "프론트엔드 ($port): ${RED}중지됨${NC}"
        fi
    done
    
    echo ""
    check_ports
}

function test_api_connection() {
    log_header "🧪 API 연결 테스트"
    
    # Health 체크
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "Health 엔드포인트 정상"
    else
        log_error "Health 엔드포인트 연결 실패"
    fi
    
    # API 문서 확인
    if curl -s http://localhost:8000/docs > /dev/null; then
        log_success "API 문서 접속 가능"
    else
        log_error "API 문서 접속 실패"
    fi
}

# =============================================================================
# 정리 기능
# =============================================================================

function clean_project() {
    log_header "🧹 프로젝트 정리"
    
    cd "$PROJECT_ROOT"
    
    # 임시 파일들 정리
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name ".DS_Store" -delete 2>/dev/null || true
    
    # 로그 파일 정리
    find . -name "*.log" -type f -delete 2>/dev/null || true
    
    # 백엔드 정리
    cd "$BACKEND_DIR"
    [[ -f "dev.db" ]] && rm -f dev.db
    
    log_success "프로젝트 정리 완료"
}

# =============================================================================
# AI 개발자를 위한 영구 가이드 함수
# =============================================================================

function show_ai_guide() {
    log_header "🤖 AI 개발자 영구 가이드"
    echo ""
    echo -e "${YELLOW}⚠️  AI 개발자님, 이것을 반드시 읽어주세요! ⚠️${NC}"
    echo ""
    echo -e "${CYAN}📋 기획자님은 기술적 세부사항을 기억하지 않습니다!${NC}"
    echo -e "${CYAN}🎯 모든 것은 자동화되어야 하고, 원클릭으로 동작해야 합니다!${NC}"
    echo ""
    echo -e "${GREEN}✅ 기획자님이 사용할 명령어:${NC}"
    echo "  ./dev-manager.sh auto      # 완전 자동화 (이것만 알면 됨!)"
    echo "  ./dev-manager.sh status    # 상태 확인"
    echo "  ./dev-manager.sh restart   # 재시작"
    echo ""
    echo -e "${RED}❌ 절대 이렇게 안내하지 마세요:${NC}"
    echo '  - "터미널에서 cd 명령어로..."'
    echo '  - "가상환경을 먼저 활성화하고..."'
    echo '  - "pip install을 실행해서..."'
    echo ""
    echo -e "${GREEN}✅ 항상 이렇게 답변하세요:${NC}"
    echo '  - "dev-manager.sh auto 실행해주세요!"'
    echo '  - "자동으로 해결해드릴게요!"'
    echo ""
    echo -e "${PURPLE}📖 상세 가이드: DEVELOPMENT_GUIDE.md${NC}"
    echo -e "${PURPLE}📝 개발 이력: DEVELOPMENT_LOG.md${NC}"
    echo ""
    echo -e "${YELLOW}🔄 새로운 세션마다 이 가이드를 먼저 확인하세요!${NC}"
}

function show_ai_memo() {
    log_header "📝 AI 개발자 메모"
    echo ""
    echo -e "${CYAN}🎯 프로젝트 목표:${NC}"
    echo "  - 기획자님을 위한 완전 자동화 개발 환경"
    echo "  - 원클릭으로 모든 것이 동작"
    echo "  - 기술적 세부사항 숨기기"
    echo ""
    echo -e "${GREEN}✅ 현재 완료된 기능:${NC}"
    echo "  - 백엔드 자동 실행: ./dev-manager.sh auto"
    echo "  - 스마트 포트 관리 (중복 실행 방지)"
    echo "  - 가상환경 자동 설정"
    echo "  - 의존성 자동 설치"
    echo "  - Health 체크 우선 로직"
    echo ""
    echo -e "${YELLOW}🔨 작업 중인 기능:${NC}"
    echo "  - 프론트엔드 자동 실행 (예정)"
    echo "  - Super Admin (포트 3020)"
    echo "  - Partner Admin (포트 3030)"
    echo ""
    echo -e "${PURPLE}🔗 중요 URL:${NC}"
    echo "  - 백엔드 API: http://localhost:8000/api/v1/docs"
    echo "  - Health 체크: http://localhost:8000/health"
    echo ""
    echo -e "${RED}⚠️  중요 규칙:${NC}"
    echo "  1. 기존 dev-manager.sh 구조 변경 금지"
    echo "  2. 복잡한 명령어 요구 금지"
    echo "  3. 자동화 우선, 수동 설정 금지"
    echo "  4. 에러 시 자동 복구 로직 포함"
}

# =============================================================================
# 백엔드 전용 개발 모드
# =============================================================================

function start_backend_only_mode() {
    log_header "🎯 백엔드 개발 모드"
    
    echo "백엔드 개발을 위해 다음을 수행합니다:"
    echo "1. 백엔드 서버 시작/확인"
    echo "2. 백엔드 개발 환경 안내"
    echo "3. 프론트엔드는 건드리지 않음"
    echo ""
    
    # 백엔드 서버만 시작
    start_backend_server
    
    # 백엔드 개발 환경 안내
    show_backend_only_urls
    
    log_success "백엔드 개발 환경이 준비되었습니다!"
    echo ""
    echo -e "${YELLOW}💡 참고:${NC} 프론트엔드 서버는 별도로 관리됩니다:"
    echo "   ./dev-manager.sh status     # 전체 상태 확인"
    echo "   ./dev-manager.sh super      # Super Admin 시작"
    echo "   ./dev-manager.sh partner    # Partner Admin 시작"
}

function stop_frontend_servers() {
    # 이 함수는 사용하지 않습니다 - 프론트엔드는 수동으로 관리
    log_warning "이 기능은 비활성화되었습니다. 프론트엔드는 개별적으로 관리해주세요."
    echo "   터미널에서 Ctrl+C로 중지하거나"
    echo "   ./dev-manager.sh status로 상태를 확인하세요"
}

function show_backend_only_urls() {
    echo ""
    echo -e "${GREEN}🎯 백엔드 개발 환경${NC}"
    echo -e "   🔧 API 문서: ${CYAN}http://localhost:8000/api/v1/docs${NC}"
    echo -e "   ❤️ Health 체크: ${CYAN}http://localhost:8000/health${NC}"
    echo -e "   📋 OpenAPI JSON: ${CYAN}http://localhost:8000/api/v1/openapi.json${NC}"
    echo -e "   🌐 Root: ${CYAN}http://localhost:8000${NC}"
    echo ""
    echo -e "${GREEN}🚀 개발 팁:${NC}"
    echo -e "   📝 코드 편집: code ."
    echo -e "   🧪 API 테스트: curl http://localhost:8000/health"
    echo -e "   🔍 로그 확인: 백엔드 터미널 창 참조"
    echo -e "   📊 상태 확인: ./dev-manager.sh status"
    echo ""
}

# =============================================================================
# 메인 명령어 처리
# =============================================================================

case "$1" in
    "auto")
        auto_everything
        ;;
    "setup")
        setup_development_environment
        ;;
    "start")
        start_all_servers
        ;;
    "stop")
        stop_all_servers
        ;;
    "restart")
        restart_all_servers
        ;;
    "backend")
        start_backend_server
        ;;
    "backend-only")
        start_backend_only_mode
        ;;
    "super")
        start_super_admin_server
        ;;
    "partner")
        start_partner_admin_server
        ;;
    "health")
        check_environment_health
        ;;
    "ports")
        case "$2" in
            "check"|"status"|"")
                check_ports
                ;;
            "clean"|"cleanup")
                cleanup_ports
                ;;
            *)
                echo "포트 명령어: check, cleanup"
                ;;
        esac
        ;;
    "status")
        check_server_status
        ;;
    "test")
        test_api_connection
        ;;
    "clean")
        clean_project
        ;;
    "guide")
        show_ai_guide
        ;;
    "memo")
        show_ai_memo
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}알 수 없는 명령어: $1${NC}"
        show_help
        exit 1
        ;;
esac
