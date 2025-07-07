# Copilot 문서 #20: 사용자 UI 샘플 개발

## 목표
파트너사 참고용 기본 사용자 인터페이스를 개발합니다. React 컴포넌트 라이브러리, 지갑 기능 샘플 페이지, API 연동 예제 코드, 커스터마이징 가이드, 모바일 반응형 템플릿을 제공하여 파트너사가 쉽게 자체 사용자 앱을 구축할 수 있도록 지원합니다.

## 전제 조건
- Copilot 문서 #15-19가 완료되어 있어야 합니다.
- 파트너 관리자 UI 템플릿이 구현되어 있어야 합니다.
- 기본 API 엔드포인트들이 구현되어 있어야 합니다.
- React/TypeScript 개발 환경이 준비되어 있어야 합니다.

## 🎯 사용자 UI 샘플 구조

### 📱 모바일 우선 앱 구조
```
User Mobile App Sample
├── 🔐 인증 시스템
│   ├── 로그인/회원가입
│   ├── 생체 인증 지원
│   ├── PIN 코드 설정
│   └── 보안 설정
├── 💰 지갑 기능
│   ├── 잔액 조회
│   ├── 송금/받기
│   ├── QR 코드 스캔
│   └── 거래 내역
├── 🔄 거래 관리
│   ├── 입금 요청
│   ├── 출금 신청
│   ├── 거래 상태 추적
│   └── 거래 확인서
├── 📊 대시보드
│   ├── 포트폴리오 개요
│   ├── 최근 활동
│   ├── 알림 센터
│   └── 빠른 액션
├── 👤 사용자 프로필
│   ├── 개인정보 관리
│   ├── 보안 설정
│   ├── 알림 설정
│   └── 고객 지원
└── 🛠️ 추가 기능
    ├── 결제 QR 생성
    ├── 주소록 관리
    ├── 거래 분석
    └── 설정 관리
```

## 🛠️ 구현 단계

### Phase 1: 프로젝트 기본 구조 (1일)

#### 1.1 React Native 프로젝트 생성
```bash
# React Native 프로젝트 생성
npx react-native init DantaroWalletUserApp --template react-native-template-typescript

cd DantaroWalletUserApp

# 필요한 패키지 설치
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install @reduxjs/toolkit react-redux redux-persist
npm install react-native-keychain react-native-biometrics
npm install react-native-qrcode-scanner react-native-qrcode-svg
npm install react-native-vector-icons react-native-linear-gradient
npm install axios react-query
npm install react-hook-form @hookform/resolvers yup
npm install react-native-toast-message
npm install react-native-reanimated react-native-gesture-handler

# 웹 버전을 위한 추가 패키지 (선택사항)
npm install react-native-web react-dom
```

#### 1.2 프로젝트 구조 설정
```
src/
├── components/
│   ├── common/              # 공통 컴포넌트
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   ├── Loading.tsx
│   │   └── QRCode.tsx
│   ├── auth/               # 인증 관련
│   │   ├── LoginForm.tsx
│   │   ├── SignupForm.tsx
│   │   ├── BiometricAuth.tsx
│   │   └── PinInput.tsx
│   ├── wallet/             # 지갑 관련
│   │   ├── WalletCard.tsx
│   │   ├── BalanceDisplay.tsx
│   │   ├── TransactionItem.tsx
│   │   └── SendForm.tsx
│   └── layout/             # 레이아웃
│       ├── SafeContainer.tsx
│       ├── Header.tsx
│       └── TabBar.tsx
├── screens/
│   ├── auth/
│   │   ├── LoginScreen.tsx
│   │   ├── SignupScreen.tsx
│   │   └── PinSetupScreen.tsx
│   ├── wallet/
│   │   ├── WalletScreen.tsx
│   │   ├── SendScreen.tsx
│   │   ├── ReceiveScreen.tsx
│   │   └── TransactionDetailScreen.tsx
│   ├── dashboard/
│   │   ├── DashboardScreen.tsx
│   │   └── NotificationScreen.tsx
│   └── profile/
│       ├── ProfileScreen.tsx
│       ├── SettingsScreen.tsx
│       └── SupportScreen.tsx
├── navigation/
│   ├── AppNavigator.tsx
│   ├── AuthNavigator.tsx
│   └── TabNavigator.tsx
├── store/
│   ├── index.ts
│   ├── authSlice.ts
│   ├── walletSlice.ts
│   └── userSlice.ts
├── services/
│   ├── api.ts
│   ├── authService.ts
│   ├── walletService.ts
│   └── biometricService.ts
├── hooks/
│   ├── useAuth.ts
│   ├── useWallet.ts
│   └── useBiometric.ts
├── utils/
│   ├── formatters.ts
│   ├── validators.ts
│   └── constants.ts
└── types/
    ├── auth.ts
    ├── wallet.ts
    └── user.ts
```

#### 1.3 기본 컴포넌트 라이브러리
```typescript
// src/components/common/Button.tsx
import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'small' | 'medium' | 'large';
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  loading = false,
  disabled = false,
  fullWidth = false,
  icon,
  style,
  textStyle,
}) => {
  const getButtonStyle = () => {
    const baseStyle = [styles.button, styles[size]];
    
    if (fullWidth) baseStyle.push(styles.fullWidth);
    if (disabled || loading) baseStyle.push(styles.disabled);
    if (style) baseStyle.push(style);
    
    return baseStyle;
  };

  const getTextStyle = () => {
    const baseStyle = [styles.text, styles[`${variant}Text`], styles[`${size}Text`]];
    if (textStyle) baseStyle.push(textStyle);
    return baseStyle;
  };

  const renderContent = () => (
    <>
      {loading ? (
        <ActivityIndicator size="small" color="#FFFFFF" />
      ) : (
        <>
          {icon}
          <Text style={getTextStyle()}>{title}</Text>
        </>
      )}
    </>
  );

  if (variant === 'primary') {
    return (
      <TouchableOpacity
        style={getButtonStyle()}
        onPress={onPress}
        disabled={disabled || loading}
        activeOpacity={0.8}
      >
        <LinearGradient
          colors={['#3B82F6', '#1D4ED8']}
          style={[styles.gradient, fullWidth && styles.fullWidth]}
        >
          {renderContent()}
        </LinearGradient>
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[getButtonStyle(), styles[variant]]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {renderContent()}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
  },
  gradient: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  primary: {
    backgroundColor: '#3B82F6',
  },
  secondary: {
    backgroundColor: '#6B7280',
  },
  outline: {
    borderWidth: 1,
    borderColor: '#3B82F6',
    backgroundColor: 'transparent',
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  small: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  medium: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  large: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  fullWidth: {
    width: '100%',
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
  primaryText: {
    color: '#FFFFFF',
  },
  secondaryText: {
    color: '#FFFFFF',
  },
  outlineText: {
    color: '#3B82F6',
  },
  ghostText: {
    color: '#3B82F6',
  },
  smallText: {
    fontSize: 14,
  },
  mediumText: {
    fontSize: 16,
  },
  largeText: {
    fontSize: 18,
  },
});

export default Button;
```

### Phase 2: 인증 시스템 구현 (1일)

#### 2.1 로그인 화면
```typescript
// src/screens/auth/LoginScreen.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';

import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import SafeContainer from '../../components/layout/SafeContainer';
import { useAuth } from '../../hooks/useAuth';
import { useBiometric } from '../../hooks/useBiometric';

const schema = yup.object().shape({
  email: yup.string().email('유효한 이메일을 입력하세요').required('이메일은 필수입니다'),
  password: yup.string().min(6, '비밀번호는 최소 6자 이상이어야 합니다').required('비밀번호는 필수입니다'),
});

type FormData = {
  email: string;
  password: string;
};

const LoginScreen: React.FC = () => {
  const navigation = useNavigation();
  const { login, loading } = useAuth();
  const { isAvailable: biometricAvailable, authenticate } = useBiometric();
  const [showBiometric, setShowBiometric] = useState(false);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: yupResolver(schema),
  });

  const onSubmit = async (data: FormData) => {
    try {
      const result = await login(data.email, data.password);
      if (result.success) {
        // 로그인 성공 후 생체 인증 등록 제안
        if (biometricAvailable && !result.user.biometric_enabled) {
          Alert.alert(
            '생체 인증',
            '더 안전하고 편리한 로그인을 위해 생체 인증을 등록하시겠습니까?',
            [
              { text: '나중에', style: 'cancel' },
              { text: '등록', onPress: () => navigation.navigate('BiometricSetup' as never) },
            ]
          );
        }
      }
    } catch (error) {
      Alert.alert('로그인 실패', '이메일 또는 비밀번호를 확인해주세요.');
    }
  };

  const handleBiometricLogin = async () => {
    try {
      const result = await authenticate('로그인을 위해 생체 인증을 진행해주세요');
      if (result.success) {
        // 저장된 크리덴셜로 자동 로그인
        // 실제 구현에서는 저장된 토큰이나 크리덴셜을 사용
      }
    } catch (error) {
      Alert.alert('생체 인증 실패', '다시 시도해주세요.');
    }
  };

  return (
    <SafeContainer>
      <KeyboardAvoidingView 
        style={styles.container}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.header}>
          <Text style={styles.title}>DantaroWallet</Text>
          <Text style={styles.subtitle}>안전한 디지털 지갑</Text>
        </View>

        <View style={styles.form}>
          <Controller
            control={control}
            name="email"
            render={({ field: { onChange, value } }) => (
              <Input
                label="이메일"
                value={value}
                onChangeText={onChange}
                placeholder="이메일을 입력하세요"
                keyboardType="email-address"
                autoCapitalize="none"
                error={errors.email?.message}
              />
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { onChange, value } }) => (
              <Input
                label="비밀번호"
                value={value}
                onChangeText={onChange}
                placeholder="비밀번호를 입력하세요"
                secureTextEntry
                error={errors.password?.message}
              />
            )}
          />

          <Button
            title="로그인"
            onPress={handleSubmit(onSubmit)}
            loading={loading}
            fullWidth
            style={styles.loginButton}
          />

          {biometricAvailable && (
            <Button
              title="생체 인증 로그인"
              onPress={handleBiometricLogin}
              variant="outline"
              fullWidth
              style={styles.biometricButton}
            />
          )}

          <View style={styles.links}>
            <TouchableOpacity onPress={() => navigation.navigate('ForgotPassword' as never)}>
              <Text style={styles.linkText}>비밀번호를 잊으셨나요?</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>계정이 없으신가요?</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Signup' as never)}>
            <Text style={styles.signupLink}>회원가입</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeContainer>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
  },
  form: {
    marginBottom: 32,
  },
  loginButton: {
    marginTop: 24,
  },
  biometricButton: {
    marginTop: 16,
  },
  links: {
    alignItems: 'center',
    marginTop: 24,
  },
  linkText: {
    color: '#3B82F6',
    fontSize: 14,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  footerText: {
    color: '#6B7280',
    fontSize: 14,
  },
  signupLink: {
    color: '#3B82F6',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
});

export default LoginScreen;
```

### Phase 3: 지갑 기능 구현 (2일)

#### 3.1 지갑 메인 화면
```typescript
// src/screens/wallet/WalletScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  QrCodeIcon,
  ClockIcon,
} from 'react-native-heroicons/outline';

import SafeContainer from '../../components/layout/SafeContainer';
import WalletCard from '../../components/wallet/WalletCard';
import TransactionItem from '../../components/wallet/TransactionItem';
import Button from '../../components/common/Button';
import { useWallet } from '../../hooks/useWallet';
import { formatCurrency } from '../../utils/formatters';

const WalletScreen: React.FC = () => {
  const navigation = useNavigation();
  const {
    balance,
    transactions,
    loading,
    refreshing,
    fetchBalance,
    fetchTransactions,
  } = useWallet();

  const [activeTab, setActiveTab] = useState<'all' | 'sent' | 'received'>('all');

  useEffect(() => {
    fetchBalance();
    fetchTransactions();
  }, []);

  const onRefresh = async () => {
    await Promise.all([fetchBalance(), fetchTransactions()]);
  };

  const filteredTransactions = transactions.filter(tx => {
    if (activeTab === 'all') return true;
    if (activeTab === 'sent') return tx.type === 'withdraw';
    if (activeTab === 'received') return tx.type === 'deposit';
    return true;
  });

  const quickActions = [
    {
      title: '송금',
      icon: <ArrowUpIcon size={24} color="#FFFFFF" />,
      onPress: () => navigation.navigate('Send' as never),
      gradient: ['#EF4444', '#DC2626'],
    },
    {
      title: '받기',
      icon: <ArrowDownIcon size={24} color="#FFFFFF" />,
      onPress: () => navigation.navigate('Receive' as never),
      gradient: ['#10B981', '#059669'],
    },
    {
      title: 'QR 스캔',
      icon: <QrCodeIcon size={24} color="#FFFFFF" />,
      onPress: () => navigation.navigate('QRScanner' as never),
      gradient: ['#8B5CF6', '#7C3AED'],
    },
    {
      title: '내역',
      icon: <ClockIcon size={24} color="#FFFFFF" />,
      onPress: () => navigation.navigate('TransactionHistory' as never),
      gradient: ['#F59E0B', '#D97706'],
    },
  ];

  return (
    <SafeContainer>
      <ScrollView
        style={styles.container}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* 잔액 카드 */}
        <View style={styles.balanceSection}>
          <LinearGradient
            colors={['#3B82F6', '#1D4ED8']}
            style={styles.balanceCard}
          >
            <Text style={styles.balanceLabel}>총 잔액</Text>
            <Text style={styles.balanceAmount}>
              {formatCurrency(balance.total)}
            </Text>
            <View style={styles.balanceDetails}>
              <View style={styles.balanceItem}>
                <Text style={styles.balanceItemLabel}>사용 가능</Text>
                <Text style={styles.balanceItemValue}>
                  {formatCurrency(balance.available)}
                </Text>
              </View>
              <View style={styles.balanceItem}>
                <Text style={styles.balanceItemLabel}>보류 중</Text>
                <Text style={styles.balanceItemValue}>
                  {formatCurrency(balance.pending)}
                </Text>
              </View>
            </View>
          </LinearGradient>
        </View>

        {/* 빠른 액션 */}
        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>빠른 액션</Text>
          <View style={styles.actionsGrid}>
            {quickActions.map((action, index) => (
              <TouchableOpacity
                key={index}
                style={styles.actionButton}
                onPress={action.onPress}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={action.gradient}
                  style={styles.actionGradient}
                >
                  {action.icon}
                </LinearGradient>
                <Text style={styles.actionTitle}>{action.title}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* 최근 거래 */}
        <View style={styles.transactionsSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>최근 거래</Text>
            <TouchableOpacity onPress={() => navigation.navigate('TransactionHistory' as never)}>
              <Text style={styles.seeAllText}>전체 보기</Text>
            </TouchableOpacity>
          </View>

          {/* 거래 탭 */}
          <View style={styles.transactionTabs}>
            {[
              { key: 'all', label: '전체' },
              { key: 'sent', label: '송금' },
              { key: 'received', label: '입금' },
            ].map((tab) => (
              <TouchableOpacity
                key={tab.key}
                style={[
                  styles.tab,
                  activeTab === tab.key && styles.activeTab,
                ]}
                onPress={() => setActiveTab(tab.key as any)}
              >
                <Text
                  style={[
                    styles.tabText,
                    activeTab === tab.key && styles.activeTabText,
                  ]}
                >
                  {tab.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* 거래 목록 */}
          <View style={styles.transactionList}>
            {filteredTransactions.length > 0 ? (
              filteredTransactions.slice(0, 5).map((transaction) => (
                <TransactionItem
                  key={transaction.id}
                  transaction={transaction}
                  onPress={() =>
                    navigation.navigate('TransactionDetail' as never, {
                      transactionId: transaction.id,
                    } as never)
                  }
                />
              ))
            ) : (
              <View style={styles.emptyState}>
                <Text style={styles.emptyStateText}>거래 내역이 없습니다</Text>
              </View>
            )}
          </View>
        </View>
      </ScrollView>
    </SafeContainer>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  balanceSection: {
    padding: 16,
  },
  balanceCard: {
    borderRadius: 16,
    padding: 24,
    marginBottom: 8,
  },
  balanceLabel: {
    color: '#E5E7EB',
    fontSize: 14,
    marginBottom: 8,
  },
  balanceAmount: {
    color: '#FFFFFF',
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  balanceDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  balanceItem: {
    flex: 1,
  },
  balanceItemLabel: {
    color: '#E5E7EB',
    fontSize: 12,
    marginBottom: 4,
  },
  balanceItemValue: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  quickActions: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 16,
  },
  actionsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 4,
  },
  actionGradient: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionTitle: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  transactionsSection: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  seeAllText: {
    color: '#3B82F6',
    fontSize: 14,
    fontWeight: '600',
  },
  transactionTabs: {
    flexDirection: 'row',
    backgroundColor: '#E5E7EB',
    borderRadius: 8,
    padding: 4,
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: '#FFFFFF',
  },
  tabText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#1F2937',
    fontWeight: '600',
  },
  transactionList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    overflow: 'hidden',
  },
  emptyState: {
    padding: 32,
    alignItems: 'center',
  },
  emptyStateText: {
    color: '#6B7280',
    fontSize: 14,
  },
});

export default WalletScreen;
```

### Phase 4: API 연동 서비스 (1일)

#### 4.1 API 서비스 기본 구조
```typescript
// src/services/api.ts
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_BASE_URL } from '../utils/constants';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 요청 인터셉터 - 토큰 추가
    this.api.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('accessToken');
        const partnerId = await AsyncStorage.getItem('partnerId');
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        if (partnerId) {
          config.headers['X-Partner-ID'] = partnerId;
        }
        
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터 - 토큰 갱신 처리
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = await AsyncStorage.getItem('refreshToken');
            if (refreshToken) {
              const response = await this.api.post('/auth/refresh', {
                refresh_token: refreshToken,
              });

              const { access_token } = response.data;
              await AsyncStorage.setItem('accessToken', access_token);

              // 원래 요청 재시도
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.api(originalRequest);
            }
          } catch (refreshError) {
            // 리프레시 실패 시 로그아웃
            await AsyncStorage.multiRemove(['accessToken', 'refreshToken']);
            // 로그인 화면으로 리다이렉트
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.delete(url, config);
    return response.data;
  }
}

export const apiService = new ApiService();
```

#### 4.2 지갑 서비스
```typescript
// src/services/walletService.ts
import { apiService } from './api';
import { 
  WalletBalance, 
  Transaction, 
  SendTransactionRequest,
  TransactionResponse 
} from '../types/wallet';

class WalletService {
  async getBalance(): Promise<WalletBalance> {
    return apiService.get<WalletBalance>('/wallet/balance');
  }

  async getTransactions(params?: {
    page?: number;
    limit?: number;
    type?: 'deposit' | 'withdraw' | 'all';
    status?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{ data: Transaction[]; total: number; page: number; limit: number }> {
    const queryString = new URLSearchParams(params as any).toString();
    return apiService.get<any>(`/wallet/transactions?${queryString}`);
  }

  async getTransactionDetail(id: string): Promise<Transaction> {
    return apiService.get<Transaction>(`/wallet/transactions/${id}`);
  }

  async sendTransaction(data: SendTransactionRequest): Promise<TransactionResponse> {
    return apiService.post<TransactionResponse>('/wallet/send', data);
  }

  async generateReceiveAddress(): Promise<{ address: string; qr_code: string }> {
    return apiService.post<any>('/wallet/receive-address');
  }

  async validateAddress(address: string): Promise<{ valid: boolean; network: string }> {
    return apiService.post<any>('/wallet/validate-address', { address });
  }

  async estimateFee(toAddress: string, amount: number): Promise<{ fee: number; energy_cost: number }> {
    return apiService.post<any>('/wallet/estimate-fee', {
      to_address: toAddress,
      amount,
    });
  }

  async getTransactionStatus(txHash: string): Promise<{ status: string; confirmations: number }> {
    return apiService.get<any>(`/wallet/transaction-status/${txHash}`);
  }
}

export const walletService = new WalletService();
```

### Phase 5: 모바일 최적화 및 반응형 디자인 (1일)

#### 5.1 반응형 유틸리티
```typescript
// src/utils/responsive.ts
import { Dimensions, PixelRatio } from 'react-native';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// 기준 크기 (iPhone 12 기준)
const BASE_WIDTH = 375;
const BASE_HEIGHT = 812;

export const responsive = {
  // 화면 크기 정보
  screenWidth: SCREEN_WIDTH,
  screenHeight: SCREEN_HEIGHT,
  
  // 디바이스 타입 판별
  isTablet: SCREEN_WIDTH >= 768,
  isSmallScreen: SCREEN_WIDTH < 350,
  
  // 반응형 크기 계산
  width: (size: number): number => (SCREEN_WIDTH / BASE_WIDTH) * size,
  height: (size: number): number => (SCREEN_HEIGHT / BASE_HEIGHT) * size,
  
  // 폰트 크기 계산
  fontSize: (size: number): number => {
    const scale = Math.min(SCREEN_WIDTH / BASE_WIDTH, SCREEN_HEIGHT / BASE_HEIGHT);
    return Math.round(PixelRatio.roundToNearestPixel(size * scale));
  },
  
  // Safe Area 계산 (노치 대응)
  getSafeAreaPadding: () => {
    const isIPhoneX = SCREEN_HEIGHT >= 812;
    return {
      top: isIPhoneX ? 44 : 20,
      bottom: isIPhoneX ? 34 : 0,
    };
  },
  
  // 그리드 시스템
  getGridItemWidth: (columns: number, spacing: number = 16): number => {
    const totalSpacing = spacing * (columns - 1);
    const availableWidth = SCREEN_WIDTH - (spacing * 2); // 좌우 여백
    return (availableWidth - totalSpacing) / columns;
  },
};

// 미디어 쿼리 스타일 헬퍼
export const createResponsiveStyles = (styles: any) => {
  const { isTablet, isSmallScreen } = responsive;
  
  return {
    ...styles.default,
    ...(isSmallScreen && styles.small),
    ...(isTablet && styles.tablet),
  };
};
```

#### 5.2 적응형 레이아웃 컴포넌트
```typescript
// src/components/layout/AdaptiveLayout.tsx
import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';
import { responsive } from '../../utils/responsive';

interface AdaptiveLayoutProps {
  children: React.ReactNode;
  variant?: 'mobile' | 'tablet' | 'auto';
  padding?: number;
  style?: ViewStyle;
}

const AdaptiveLayout: React.FC<AdaptiveLayoutProps> = ({
  children,
  variant = 'auto',
  padding = 16,
  style,
}) => {
  const getLayoutStyle = () => {
    if (variant === 'auto') {
      return responsive.isTablet ? styles.tabletLayout : styles.mobileLayout;
    }
    return variant === 'tablet' ? styles.tabletLayout : styles.mobileLayout;
  };

  return (
    <View style={[
      getLayoutStyle(),
      { padding: responsive.width(padding) },
      style
    ]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  mobileLayout: {
    flex: 1,
    width: '100%',
  },
  tabletLayout: {
    flex: 1,
    width: '100%',
    maxWidth: 768, // 최대 폭 제한
    alignSelf: 'center',
  },
});

export default AdaptiveLayout;
```

## 📚 커스터마이징 가이드

### 브랜딩 가이드
```typescript
// src/config/theme.ts
export interface Theme {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    border: string;
    error: string;
    success: string;
    warning: string;
  };
  fonts: {
    regular: string;
    medium: string;
    bold: string;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
}

export const defaultTheme: Theme = {
  colors: {
    primary: '#3B82F6',
    secondary: '#6B7280',
    accent: '#10B981',
    background: '#F9FAFB',
    surface: '#FFFFFF',
    text: '#1F2937',
    textSecondary: '#6B7280',
    border: '#E5E7EB',
    error: '#EF4444',
    success: '#10B981',
    warning: '#F59E0B',
  },
  fonts: {
    regular: 'System',
    medium: 'System',
    bold: 'System',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
  },
};

// 파트너별 테마 커스터마이징
export const createPartnerTheme = (partnerConfig: any): Theme => {
  return {
    ...defaultTheme,
    colors: {
      ...defaultTheme.colors,
      primary: partnerConfig.primary_color || defaultTheme.colors.primary,
      secondary: partnerConfig.secondary_color || defaultTheme.colors.secondary,
      accent: partnerConfig.accent_color || defaultTheme.colors.accent,
    },
    fonts: {
      ...defaultTheme.fonts,
      regular: partnerConfig.font_family || defaultTheme.fonts.regular,
      medium: partnerConfig.font_family || defaultTheme.fonts.medium,
      bold: partnerConfig.font_family || defaultTheme.fonts.bold,
    },
  };
};
```

## 📱 PWA 버전 지원

### PWA 설정
```json
// public/manifest.json
{
  "name": "DantaroWallet User App",
  "short_name": "DantaroWallet",
  "description": "안전한 디지털 지갑 서비스",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#3B82F6",
  "background_color": "#FFFFFF",
  "orientation": "portrait",
  "categories": ["finance", "utilities"],
  "icons": [
    {
      "src": "/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

## ✅ 검증 체크리스트

### 기능 테스트
- [ ] 인증 시스템 (로그인/회원가입/생체인증)
- [ ] 지갑 기능 (잔액조회/송금/받기)
- [ ] QR 코드 스캔 및 생성
- [ ] 거래 내역 조회 및 필터링
- [ ] 실시간 데이터 업데이트
- [ ] 오프라인 모드 지원
- [ ] 푸시 알림
- [ ] 보안 기능 (PIN/생체인증)

### UI/UX 테스트
- [ ] 반응형 디자인 (모바일/태블릿)
- [ ] 다크모드 지원
- [ ] 접근성 준수
- [ ] 로딩 상태 표시
- [ ] 오류 처리 및 사용자 피드백
- [ ] 부드러운 애니메이션
- [ ] 직관적인 네비게이션

### 성능 테스트
- [ ] 앱 시작 시간 < 3초
- [ ] 페이지 전환 속도 < 1초
- [ ] 메모리 사용량 최적화
- [ ] 배터리 소모 최소화
- [ ] 네트워크 사용 최적화

### 보안 테스트
- [ ] 민감 정보 암호화
- [ ] 안전한 키 저장
- [ ] SSL 인증서 확인
- [ ] 중간자 공격 방지
- [ ] 앱 위변조 탐지

## 📈 예상 효과

### 파트너사 관점
- **개발 시간 단축**: 기본 UI 제공으로 80% 개발 시간 절약
- **품질 보장**: 검증된 컴포넌트와 패턴 사용
- **브랜딩 일관성**: 쉬운 커스터마이징으로 브랜드 정체성 유지
- **유지보수 효율성**: 표준화된 코드 구조

### 사용자 관점
- **일관된 경험**: 익숙한 인터페이스 패턴
- **성능 최적화**: 빠른 로딩과 부드러운 애니메이션
- **접근성**: 모든 사용자가 쉽게 사용 가능
- **보안**: 검증된 보안 기능과 모범 사례

이 사용자 UI 샘플은 파트너사들이 자체 모바일 앱을 빠르고 안전하게 구축할 수 있도록 완전한 레퍼런스를 제공합니다.
