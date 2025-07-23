// 프론트엔드-백엔드 API 연결 테스트 스크립트
// 브라우저 콘솔이나 Node.js에서 실행 가능

const testBackendAPIs = async () => {
    const baseURL = 'http://localhost:8000';

    console.log('🔄 프론트엔드-백엔드 API 연결 테스트 시작...\n');

    const tests = [
        {
            name: '기본 API 상태',
            url: '/api/v1/test',
            method: 'GET'
        },
        {
            name: '관리자 대시보드 개요',
            url: '/api/v1/admin/dashboard/overview',
            method: 'GET',
            headers: { 'Authorization': 'Bearer test_token' }
        },
        {
            name: '시스템 상태',
            url: '/api/v1/admin/dashboard/system-health',
            method: 'GET',
            headers: { 'Authorization': 'Bearer test_token' }
        },
        {
            name: '사용자 랭킹',
            url: '/api/v1/admin/dashboard/user-rankings',
            method: 'GET',
            headers: { 'Authorization': 'Bearer test_token' }
        }
    ];

    const results = [];

    for (const test of tests) {
        try {
            console.log(`📡 테스트: ${test.name}`);

            const response = await fetch(baseURL + test.url, {
                method: test.method,
                headers: {
                    'Content-Type': 'application/json',
                    ...test.headers
                }
            });

            const status = response.status;
            const data = await response.json();

            if (status === 200 || status === 201) {
                console.log(`✅ 성공 (${status}):`, JSON.stringify(data, null, 2));
                results.push({ test: test.name, status: 'PASS', data });
            } else {
                console.log(`❌ 실패 (${status}):`, data);
                results.push({ test: test.name, status: 'FAIL', error: data });
            }

        } catch (error) {
            console.log(`🚨 에러:`, error.message);
            results.push({ test: test.name, status: 'ERROR', error: error.message });
        }
        console.log('─'.repeat(50));
    }

    // 결과 요약
    console.log('\n📊 테스트 결과 요약:');
    const passed = results.filter(r => r.status === 'PASS').length;
    const failed = results.filter(r => r.status === 'FAIL').length;
    const errors = results.filter(r => r.status === 'ERROR').length;

    console.log(`✅ 성공: ${passed}개`);
    console.log(`❌ 실패: ${failed}개`);
    console.log(`🚨 에러: ${errors}개`);

    if (passed === tests.length) {
        console.log('\n🎉 모든 API 테스트 통과! 프론트엔드 연결 준비 완료');
    } else {
        console.log('\n⚠️  일부 API에 문제가 있습니다. 백엔드 상태를 확인하세요.');
    }

    return results;
};

// Node.js 환경에서 실행하는 경우
if (typeof window === 'undefined') {
    // Node.js에서는 fetch polyfill 필요
    console.log('Node.js 환경에서는 브라우저에서 실행하거나 fetch polyfill을 설치하세요.');
    console.log('예: npm install node-fetch');
} else {
    // 브라우저에서 실행
    testBackendAPIs();
}

// 수동 테스트용 함수들
const testSingleAPI = async (endpoint) => {
    try {
        const response = await fetch(`http://localhost:8000${endpoint}`);
        const data = await response.json();
        console.log('Response:', data);
        return data;
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
};

// 브라우저 콘솔에서 사용 예시:
// testSingleAPI('/api/v1/test')
// testBackendAPIs()
