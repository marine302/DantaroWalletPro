// 다크 테마 전용 스타일 시스템
export const darkTheme = {
  // 텍스트 색상
  text: {
    primary: 'text-white',           // 메인 제목
    secondary: 'text-gray-200',      // 서브 제목  
    muted: 'text-gray-300',         // 일반 텍스트
    accent: 'text-blue-400',        // 강조 텍스트
    success: 'text-green-400',      // 성공
    warning: 'text-yellow-400',     // 경고
    error: 'text-red-400',          // 에러
  },
  
  // 배경 색상
  background: {
    primary: 'bg-gray-900',         // 메인 배경
    secondary: 'bg-gray-800',       // 카드 배경
    tertiary: 'bg-gray-700',        // 선택된 상태
    input: 'bg-white',              // 입력 필드 (가독성 위해 흰색 유지)
  },
  
  // 보더 색상  
  border: {
    primary: 'border-gray-600',     // 기본 보더
    secondary: 'border-gray-500',   // 강조 보더
    focus: 'border-blue-500',       // 포커스 상태
  },
  
  // 버튼 스타일
  button: {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
    outline: 'border border-gray-500 text-gray-200 hover:bg-gray-700',
  },
  
  // 카드 스타일
  card: {
    background: 'bg-gray-800 border border-gray-600',
    shadow: 'shadow-xl shadow-black/30',
  }
}

// 공통 클래스 조합 함수
export const createDarkClasses = {
  pageTitle: () => `${darkTheme.text.primary} text-3xl font-bold mb-4`,
  sectionTitle: () => `${darkTheme.text.primary} text-lg font-semibold mb-4`,
  label: () => `${darkTheme.text.secondary} text-sm font-medium`,
  description: () => `${darkTheme.text.muted} text-sm`,
  input: () => `px-3 py-2 ${darkTheme.border.primary} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${darkTheme.background.input} text-gray-900`,
  button: {
    primary: () => `px-4 py-2 ${darkTheme.button.primary} rounded-md transition-colors`,
    secondary: () => `px-4 py-2 ${darkTheme.button.secondary} rounded-md transition-colors`,
  },
  card: () => `${darkTheme.card.background} ${darkTheme.card.shadow} rounded-lg p-6`,
  statCard: () => `${darkTheme.card.background} ${darkTheme.card.shadow} rounded-lg p-4`,
}

// 반응형 그리드 레이아웃
export const gridLayouts = {
  statsGrid: 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8',
  contentGrid: 'grid grid-cols-1 lg:grid-cols-2 gap-8',
  fullGrid: 'grid grid-cols-1 gap-6',
}
