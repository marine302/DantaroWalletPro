/* 메인 JavaScript 파일 */

// 전역 변수
let isLoading = false;
let currentUser = null;
let balance = { trx: 0, usdt: 0 };

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadUserBalance();
    setupEventListeners();
});

// 앱 초기화
function initializeApp() {
    // 토큰 확인
    const token = localStorage.getItem('token');
    if (token) {
        // 토큰 유효성 검사
        validateToken(token);
    }

    // 토스트 컨테이너 생성
    createToastContainer();

    // 자동 새로고침 설정 (5분마다)
    setInterval(autoRefresh, 300000);
}

// 이벤트 리스너 설정
function setupEventListeners() {
    // 복사 버튼
    document.querySelectorAll('[data-copy]').forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-copy');
            copyToClipboard(target);
        });
    });

    // 새로고침 버튼
    document.querySelectorAll('[data-refresh]').forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-refresh');
            refreshData(target);
        });
    });

    // 폼 제출 방지 (Enter 키)
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
            }
        });
    });
}

// 토큰 유효성 검사
async function validateToken(token) {
    try {
        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            currentUser = await response.json();
            updateUserDisplay();
        } else {
            // 토큰 만료 또는 유효하지 않음
            localStorage.removeItem('token');
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
    } catch (error) {
        console.error('토큰 검증 실패:', error);
        localStorage.removeItem('token');
    }
}

// 사용자 잔고 로드
async function loadUserBalance() {
    if (isLoading) return;

    const token = localStorage.getItem('token');
    if (!token) return;

    try {
        setLoading(true);
        const response = await fetch('/api/v1/balance', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            balance = data;
            updateBalanceDisplay();
        } else {
            showToast('잔고 로드 실패', 'error');
        }
    } catch (error) {
        console.error('잔고 로드 오류:', error);
        showToast('잔고 로드 중 오류가 발생했습니다', 'error');
    } finally {
        setLoading(false);
    }
}

// 잔고 표시 업데이트
function updateBalanceDisplay() {
    // TRX 잔고
    const trxElements = document.querySelectorAll('[data-balance="trx"]');
    trxElements.forEach(element => {
        element.textContent = formatNumber(balance.trx_balance || 0);
    });

    // USDT 잔고
    const usdtElements = document.querySelectorAll('[data-balance="usdt"]');
    usdtElements.forEach(element => {
        element.textContent = formatNumber(balance.usdt_balance || 0);
    });

    // 총 USD 가치
    const totalElements = document.querySelectorAll('[data-balance="total"]');
    totalElements.forEach(element => {
        const total = (balance.trx_balance || 0) * 0.1 + (balance.usdt_balance || 0); // TRX 가격 가정
        element.textContent = formatCurrency(total);
    });
}

// 사용자 정보 표시 업데이트
function updateUserDisplay() {
    if (!currentUser) return;

    const userElements = document.querySelectorAll('[data-user]');
    userElements.forEach(element => {
        const field = element.getAttribute('data-user');
        if (currentUser[field]) {
            element.textContent = currentUser[field];
        }
    });
}

// 클립보드 복사
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // 현대적인 방법
        navigator.clipboard.writeText(text).then(() => {
            showToast('클립보드에 복사되었습니다', 'success');
        }).catch(err => {
            console.error('복사 실패:', err);
            showToast('복사에 실패했습니다', 'error');
        });
    } else {
        // 대체 방법
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showToast('클립보드에 복사되었습니다', 'success');
        } catch (err) {
            console.error('복사 실패:', err);
            showToast('복사에 실패했습니다', 'error');
        }

        document.body.removeChild(textArea);
    }
}

// 데이터 새로고침
function refreshData(type = 'all') {
    switch (type) {
        case 'balance':
            loadUserBalance();
            break;
        case 'transactions':
            loadTransactions();
            break;
        case 'all':
        default:
            loadUserBalance();
            loadTransactions();
            break;
    }
}

// 자동 새로고침
function autoRefresh() {
    if (document.visibilityState === 'visible') {
        refreshData('balance');
    }
}

// 로딩 상태 설정
function setLoading(loading) {
    isLoading = loading;
    const loadingElements = document.querySelectorAll('.loading-spinner');
    const refreshButtons = document.querySelectorAll('[data-refresh]');

    if (loading) {
        loadingElements.forEach(element => element.style.display = 'inline-block');
        refreshButtons.forEach(button => button.disabled = true);
    } else {
        loadingElements.forEach(element => element.style.display = 'none');
        refreshButtons.forEach(button => button.disabled = false);
    }
}

// 토스트 알림 표시
function showToast(message, type = 'info', duration = 3000) {
    const toast = createToast(message, type);
    const container = document.getElementById('toast-container');
    container.appendChild(toast);

    // 애니메이션
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);

    // 자동 제거
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// 토스트 요소 생성
function createToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${getToastColor(type)} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas ${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    return toast;
}

// 토스트 컨테이너 생성
function createToastContainer() {
    if (document.getElementById('toast-container')) return;

    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
}

// 토스트 색상 반환
function getToastColor(type) {
    switch (type) {
        case 'success': return 'success';
        case 'error': return 'danger';
        case 'warning': return 'warning';
        case 'info': return 'info';
        default: return 'primary';
    }
}

// 토스트 아이콘 반환
function getToastIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        case 'info': return 'fa-info-circle';
        default: return 'fa-bell';
    }
}

// 숫자 포맷팅
function formatNumber(value, decimals = 6) {
    return parseFloat(value).toFixed(decimals);
}

// 통화 포맷팅
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// 날짜 포맷팅
function formatDate(date) {
    return new Date(date).toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// API 호출 헬퍼
async function apiCall(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };

    try {
        const response = await fetch(endpoint, mergedOptions);

        if (!response.ok) {
            if (response.status === 401) {
                // 토큰 만료
                localStorage.removeItem('token');
                window.location.href = '/login';
                return null;
            }

            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || '요청 실패');
        }

        return await response.json();
    } catch (error) {
        console.error('API 호출 오류:', error);
        throw error;
    }
}

// 전역 함수로 노출
window.app = {
    copyToClipboard,
    refreshData,
    showToast,
    formatNumber,
    formatCurrency,
    formatDate,
    apiCall
};
