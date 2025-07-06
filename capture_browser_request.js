// 브라우저 콘솔에서 실행할 스크립트
// 실제 로그인 요청을 캡처하여 분석

console.log("=== 브라우저 로그인 요청 캡처 스크립트 ===");

// 원본 fetch 함수를 백업
const originalFetch = window.fetch;

// fetch 함수를 오버라이드하여 모든 요청을 로깅
window.fetch = function(...args) {
    const [url, options] = args;
    
    if (url.includes('/auth/super-admin/login')) {
        console.log("=== SUPER ADMIN LOGIN REQUEST CAPTURED ===");
        console.log("URL:", url);
        console.log("Method:", options?.method);
        console.log("Headers:", options?.headers);
        console.log("Body:", options?.body);
        
        if (options?.body) {
            try {
                const parsedBody = JSON.parse(options.body);
                console.log("Parsed Body:", parsedBody);
                console.log("Email:", parsedBody.email);
                console.log("Password length:", parsedBody.password?.length);
                console.log("Password repr:", JSON.stringify(parsedBody.password));
            } catch (e) {
                console.log("Body parsing error:", e);
            }
        }
    }
    
    return originalFetch.apply(this, args).then(response => {
        if (url.includes('/auth/super-admin/login')) {
            console.log("=== RESPONSE ===");
            console.log("Status:", response.status);
            console.log("StatusText:", response.statusText);
            
            // 응답 복제하여 내용 확인
            response.clone().text().then(text => {
                console.log("Response body:", text);
            });
        }
        return response;
    });
};

console.log("요청 캡처가 활성화되었습니다. 이제 로그인을 시도하세요.");
