#!/bin/bash

# 🚀 Dantaro Super Admin Dashboard - 통합 서비스 스크립트

echo "🚀 Dantaro Super Admin Dashboard"
echo "================================="

case "$1" in
    "start"|"dev"|"")
        echo "📦 모든 서비스를 시작합니다..."
        echo ""
        
        # 백그라운드에서 목업 서버들 시작
        echo "🔧 목업 서버들 시작 중..."
        node mock-server.js &
        MOCK_HTTP_PID=$!
        
        node mock-realtime-server.js &
        MOCK_WS_PID=$!
        
        # 잠시 대기 (목업 서버들이 시작되도록)
        sleep 3
        
        echo "🌐 프론트엔드 개발 서버 시작 중..."
        # 프론트엔드 서버 시작
        npm run frontend-only
        
        # 종료 시 목업 서버들도 정리
        echo "🛑 서비스들을 정리합니다..."
        kill $MOCK_HTTP_PID 2>/dev/null
        kill $MOCK_WS_PID 2>/dev/null
        ;;
        
    "stop")
        echo "🛑 모든 서비스를 중지합니다..."
        
        # Mock 서버들 중지
        pkill -f "mock-server.js" 2>/dev/null
        pkill -f "mock-realtime-server.js" 2>/dev/null
        
        # 프론트엔드 서버도 중지
        pkill -f "next dev" 2>/dev/null
        pkill -f "port-manager.js" 2>/dev/null
        
        echo "✅ 모든 서비스가 중지되었습니다."
        ;;
        
    "status")
        echo "📊 서비스 상태를 확인합니다..."
        
        echo ""
        echo "🔧 Mock 서버 상태:"
        if curl -s http://localhost:3001/health > /dev/null 2>&1; then
            echo "   ✅ HTTP Mock Server: http://localhost:3001 (정상)"
        else
            echo "   ❌ HTTP Mock Server: 중지됨"
        fi
        
        if nc -z localhost 3002 2>/dev/null; then
            echo "   ✅ WebSocket Mock Server: ws://localhost:3002 (정상)"
        else
            echo "   ❌ WebSocket Mock Server: 중지됨"
        fi
        
        echo ""
        echo "🌐 프론트엔드 서버 상태:"
        if curl -s http://localhost:3020 > /dev/null 2>&1; then
            echo "   ✅ Frontend: http://localhost:3020 (정상)"
        else
            echo "   ❌ Frontend: 중지됨"
        fi
        ;;
        
    "restart")
        echo "🔄 모든 서비스를 재시작합니다..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    "logs")
        echo "📝 서비스 로그를 확인합니다..."
        if [ -f services.log ]; then
            tail -f services.log
        else
            echo "❌ 로그 파일이 없습니다."
        fi
        ;;
        
    "help"|"-h"|"--help")
        echo "사용법: $0 [command]"
        echo ""
        echo "명령어:"
        echo "  start     모든 서비스 시작 (기본값)"
        echo "  dev       개발 모드로 모든 서비스 시작 (start와 동일)"
        echo "  stop      모든 서비스 중지"
        echo "  restart   모든 서비스 재시작"
        echo "  status    서비스 상태 확인"
        echo "  logs      서비스 로그 확인"
        echo "  help      도움말 표시"
        echo ""
        echo "서비스:"
        echo "  - Frontend Dev Server (Next.js) - http://localhost:3020"
        echo "  - Mock HTTP Server - http://localhost:3001"
        echo "  - Mock WebSocket Server - ws://localhost:3002"
        ;;
        
    *)
        echo "❌ 알 수 없는 명령어: $1"
        echo "사용법: $0 [start|stop|restart|status|logs|help]"
        exit 1
        ;;
esac
