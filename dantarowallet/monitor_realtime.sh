#!/bin/bash

echo "🔍 백엔드 API 요청 실시간 모니터링"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 사용법: 다른 터미널에서 프론트엔드 요청을 보내면 여기서 실시간으로 확인 가능"
echo "🔄 10초마다 자동으로 테스트 요청도 보냅니다"
echo "⏹️  중지하려면 Ctrl+C"
echo ""

# 카운터
counter=0

while true; do
    counter=$((counter + 1))
    echo "📊 모니터링 #$counter - $(date '+%H:%M:%S')"
    
    # 기본 API 테스트
    echo "   🔸 기본 API 테스트"
    start_time=$(date +%s.%N)
    response=$(curl -s -w "%{http_code}" http://localhost:8000/api/v1/test)
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.001")
    
    http_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        echo "      ✅ 응답: $http_code (${duration}s) - $response_body"
    else
        echo "      ❌ 에러: $http_code - $response_body"
    fi
    
    # 관리자 API 테스트
    echo "   🔸 관리자 API 테스트"
    start_time=$(date +%s.%N)
    admin_response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer test_token" \
        http://localhost:8000/api/v1/admin/dashboard/overview)
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.001")
    
    admin_code="${admin_response: -3}"
    
    if [ "$admin_code" = "200" ]; then
        echo "      ✅ 응답: $admin_code (${duration}s)"
    else
        echo "      ❌ 에러: $admin_code"
    fi
    
    # 활성 백엔드 프로세스 확인
    uvicorn_count=$(ps aux | grep uvicorn | grep -v grep | wc -l | tr -d ' ')
    echo "   🔸 활성 백엔드 프로세스: $uvicorn_count개"
    
    echo "   ⏳ 10초 대기 중... (Ctrl+C로 중지)"
    echo ""
    
    sleep 10
done
