/**
 * 개발용 테스트 스크립트 - Mock 로그인 테스트
 */

import { mockAuthService } from '../lib/services/mock.service';

async function testMockLogin() {
  console.log('🧪 Mock 로그인 테스트 시작...');
  
  const testEmail = 'partner@dantarowallet.com';
  const testPassword = 'DantaroPartner2024!';
  
  try {
    const result = await mockAuthService.login(testEmail, testPassword);
    
    if (result.success) {
      console.log('✅ 로그인 성공!');
      console.log('사용자 정보:', result.data.user);
      console.log('토큰:', result.data.access_token);
    } else {
      console.log('❌ 로그인 실패:', result.message);
    }
  } catch (error) {
    console.error('❌ 로그인 에러:', error);
  }
}

async function testWrongCredentials() {
  console.log('🧪 잘못된 계정 정보 테스트...');
  
  try {
    const result = await mockAuthService.login('wrong@email.com', 'wrongpassword');
    
    if (!result.success) {
      console.log('✅ 올바르게 로그인 거부됨:', result.message);
    } else {
      console.log('❌ 예상치 못한 로그인 성공');
    }
  } catch (error) {
    console.error('❌ 테스트 에러:', error);
  }
}

// Node.js 환경에서만 실행
if (typeof window === 'undefined') {
  testMockLogin();
  testWrongCredentials();
}

export { testMockLogin, testWrongCredentials };
