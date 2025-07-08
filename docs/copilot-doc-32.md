# Copilot 문서 #32: 사용자 모바일 앱 템플릿

## 목표
파트너사 커스터마이징이 가능한 사용자 앱을 구축합니다. React Native 기반 모바일 앱으로 지갑 잔액 및 거래 내역, QR 코드 입금/송금, 실시간 거래 알림, 다국어 지원, 생체 인증 및 보안 기능을 포함한 완전한 사용자 경험을 제공합니다.

## 전제 조건
- Copilot 문서 #24-31이 완료되어 있어야 합니다
- 백엔드 API가 모바일 앱을 지원해야 합니다
- React Native 개발 환경이 구성되어 있어야 합니다
- 파트너사 브랜딩 설정 시스템이 구축되어 있어야 합니다

## 🎯 모바일 앱 구조

### 📱 앱 화면 구성
```
User Mobile App
├── 🔐 인증 플로우
│   ├── 로그인 화면
│   ├── 회원가입 화면
│   ├── 생체 인증 설정
│   └── PIN 설정/확인
├── 💳 메인 지갑
│   ├── 잔액 표시
│   ├── 최근 거래 내역
│   ├── 입금 QR 코드
│   └── 빠른 액션 버튼
├── 💸 송금 기능
│   ├── 송금 주소 입력
│   ├── QR 코드 스캔
│   ├── 금액 입력
│   └── 수수료 확인
├── 📊 거래 내역
│   ├── 전체 거래 목록
│   ├── 거래 상세 정보
│   ├── 필터 및 검색
│   └── 거래 영수증
├── ⚙️ 설정
│   ├── 프로필 관리
│   ├── 보안 설정
│   ├── 언어 설정
│   └── 알림 설정
└── 🔔 알림
    ├── 푸시 알림
    ├── 인앱 알림
    ├── 거래 알림
    └── 시스템 공지
```

## 🛠️ 구현 단계

### Phase 1: React Native 프로젝트 설정 (1일)

#### 1.1 프로젝트 초기화
```bash
# React Native 프로젝트 생성
npx react-native@latest init PartnerWalletApp --template react-native-template-typescript

# 필수 패키지 설치
cd PartnerWalletApp
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler react-native-reanimated
npm install @reduxjs/toolkit react-redux
npm install react-native-keychain # 생체 인증
npm install react-native-qrcode-svg react-native-svg # QR 코드
npm install react-native-push-notification # 푸시 알림
npm install i18n-js # 다국어 지원
npm install react-native-config # 환경 변수
```

#### 1.2 프로젝트 구조
```
PartnerWalletApp/
├── src/
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── RegisterScreen.tsx
│   │   │   └── BiometricSetupScreen.tsx
│   │   ├── wallet/
│   │   │   ├── WalletScreen.tsx
│   │   │   ├── DepositScreen.tsx
│   │   │   └── WithdrawScreen.tsx
│   │   ├── transaction/
│   │   │   ├── TransactionListScreen.tsx
│   │   │   └── TransactionDetailScreen.tsx
│   │   └── settings/
│   │       ├── SettingsScreen.tsx
│   │       └── ProfileScreen.tsx
│   ├── components/
│   │   ├── common/
│   │   ├── wallet/
│   │   └── transaction/
│   ├── navigation/
│   │   ├── AppNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   └── TabNavigator.tsx
│   ├── store/
│   │   ├── index.ts
│   │   ├── authSlice.ts
│   │   ├── walletSlice.ts
│   │   └── transactionSlice.ts
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── wallet.ts
│   ├── utils/
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   └── locales/
│       ├── en.json
│       ├── ko.json
│       └── zh.json
```

### Phase 2: 핵심 화면 구현 (2일)

#### 2.1 인증 화면
```typescript
// src/screens/auth/LoginScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform
} from 'react-native';
import { useDispatch } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import * as Keychain from 'react-native-keychain';
import { login } from '../../store/authSlice';
import { usePartnerTheme } from '../../hooks/usePartnerTheme';
import BiometricAuth from '../../components/auth/BiometricAuth';

const LoginScreen = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  
  const dispatch = useDispatch();
  const navigation = useNavigation();
  const theme = usePartnerTheme();
  
  useEffect(() => {
    checkBiometricAvailability();
  }, []);
  
  const checkBiometricAvailability = async () => {
    try {
      const biometryType = await Keychain.getSupportedBiometryType();
      setBiometricAvailable(!!biometryType);
    } catch (error) {
      console.log('Biometric check error:', error);
    }
  };
  
  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('오류', '이메일과 비밀번호를 입력해주세요.');
      return;
    }
    
    setLoading(true);
    try {
      const result = await dispatch(login({ email, password })).unwrap();
      
      // 생체 인증 사용 여부 확인
      if (biometricAvailable && !result.user.biometricEnabled) {
        navigation.navigate('BiometricSetup');
      } else {
        navigation.navigate('Main');
      }
    } catch (error: any) {
      Alert.alert('로그인 실패', error.message || '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleBiometricLogin = async () => {
    try {
      const credentials = await Keychain.getInternetCredentials('wallet_app');
      if (credentials) {
        setEmail(credentials.username);
        setPassword(credentials.password);
        handleLogin();
      }
    } catch (error) {
      Alert.alert('오류', '생체 인증에 실패했습니다.');
    }
  };
  
  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={[styles.container, { backgroundColor: theme.colors.background }]}
    >
      <View style={styles.logoContainer}>
        <Text style={[styles.logo, { color: theme.colors.primary }]}>
          {theme.partnerName} Wallet
        </Text>
      </View>
      
      <View style={styles.formContainer}>
        <TextInput
          style={[styles.input, { 
            borderColor: theme.colors.border,
            color: theme.colors.text
          }]}
          placeholder="이메일"
          placeholderTextColor={theme.colors.placeholder}
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
        
        <TextInput
          style={[styles.input, { 
            borderColor: theme.colors.border,
            color: theme.colors.text
          }]}
          placeholder="비밀번호"
          placeholderTextColor={theme.colors.placeholder}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
        
        <TouchableOpacity
          style={[styles.button, { backgroundColor: theme.colors.primary }]}
          onPress={handleLogin}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? '로그인 중...' : '로그인'}
          </Text>
        </TouchableOpacity>
        
        {biometricAvailable && (
          <BiometricAuth onSuccess={handleBiometricLogin} />
        )}
        
        <TouchableOpacity
          style={styles.linkButton}
          onPress={() => navigation.navigate('Register')}
        >
          <Text style={[styles.linkText, { color: theme.colors.primary }]}>
            계정이 없으신가요? 회원가입
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 50,
  },
  logo: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  formContainer: {
    width: '100%',
  },
  input: {
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 15,
    marginBottom: 15,
    fontSize: 16,
  },
  button: {
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  linkButton: {
    marginTop: 20,
    alignItems: 'center',
  },
  linkText: {
    fontSize: 14,
  },
});

export default LoginScreen;
```

#### 2.2 메인 지갑 화면
```typescript
// src/screens/wallet/WalletScreen.tsx
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { fetchWalletData } from '../../store/walletSlice';
import { fetchRecentTransactions } from '../../store/transactionSlice';
import { usePartnerTheme } from '../../hooks/usePartnerTheme';
import BalanceCard from '../../components/wallet/BalanceCard';
import QuickActions from '../../components/wallet/QuickActions';
import RecentTransactions from '../../components/wallet/RecentTransactions';
import QRCodeModal from '../../components/wallet/QRCodeModal';

const WalletScreen = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  
  const dispatch = useDispatch();
  const navigation = useNavigation();
  const theme = usePartnerTheme();
  
  const { balance, address, loading } = useSelector((state: any) => state.wallet);
  const { recentTransactions } = useSelector((state: any) => state.transaction);
  
  useEffect(() => {
    loadWalletData();
  }, []);
  
  const loadWalletData = async () => {
    await dispatch(fetchWalletData());
    await dispatch(fetchRecentTransactions());
  };
  
  const onRefresh = async () => {
    setRefreshing(true);
    await loadWalletData();
    setRefreshing(false);
  };
  
  const handleDeposit = () => {
    setShowQRModal(true);
  };
  
  const handleWithdraw = () => {
    navigation.navigate('Withdraw');
  };
  
  const handleScan = () => {
    navigation.navigate('QRScanner');
  };
  
  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
          내 지갑
        </Text>
        <TouchableOpacity onPress={() => navigation.navigate('Notifications')}>
          <Icon name="notifications-outline" size={24} color={theme.colors.text} />
        </TouchableOpacity>
      </View>
      
      <BalanceCard
        balance={balance}
        currency="USDT"
        fiatValue={balance * 1.0} // 실시간 환율 적용 필요
        theme={theme}
      />
      
      <QuickActions
        onDeposit={handleDeposit}
        onWithdraw={handleWithdraw}
        onScan={handleScan}
        theme={theme}
      />
      
      <RecentTransactions
        transactions={recentTransactions}
        onViewAll={() => navigation.navigate('TransactionList')}
        theme={theme}
      />
      
      <QRCodeModal
        visible={showQRModal}
        onClose={() => setShowQRModal(false)}
        address={address}
        theme={theme}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 50,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
  },
});

export default WalletScreen;
```

### Phase 3: 송금 및 거래 기능 (2일)

#### 3.1 송금 화면 구현
```typescript
// src/screens/wallet/WithdrawScreen.tsx
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useSelector, useDispatch } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';
import { createWithdrawal } from '../../store/walletSlice';
import { usePartnerTheme } from '../../hooks/usePartnerTheme';
import { validateTronAddress } from '../../utils/validators';
import FeeEstimator from '../../components/wallet/FeeEstimator';
import AmountInput from '../../components/wallet/AmountInput';

const WithdrawScreen = () => {
  const [address, setAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [memo, setMemo] = useState('');
  const [loading, setLoading] = useState(false);
  const [fee, setFee] = useState(0);
  
  const navigation = useNavigation();
  const dispatch = useDispatch();
  const theme = usePartnerTheme();
  
  const { balance } = useSelector((state: any) => state.wallet);
  
  const handleQRScan = () => {
    navigation.navigate('QRScanner', {
      onScan: (data: string) => {
        setAddress(data);
        navigation.goBack();
      }
    });
  };
  
  const validateForm = () => {
    if (!address || !amount) {
      Alert.alert('오류', '주소와 금액을 입력해주세요.');
      return false;
    }
    
    if (!validateTronAddress(address)) {
      Alert.alert('오류', '유효하지 않은 TRON 주소입니다.');
      return false;
    }
    
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) {
      Alert.alert('오류', '유효한 금액을 입력해주세요.');
      return false;
    }
    
    if (numAmount + fee > balance) {
      Alert.alert('오류', '잔액이 부족합니다.');
      return false;
    }
    
    return true;
  };
  
  const handleWithdraw = async () => {
    if (!validateForm()) return;
    
    Alert.alert(
      '출금 확인',
      `${amount} USDT를 ${address}로 전송하시겠습니까?\n\n수수료: ${fee} USDT`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '확인',
          onPress: async () => {
            setLoading(true);
            try {
              await dispatch(createWithdrawal({
                address,
                amount: parseFloat(amount),
                memo,
              })).unwrap();
              
              Alert.alert('성공', '출금 요청이 완료되었습니다.', [
                { text: '확인', onPress: () => navigation.goBack() }
              ]);
            } catch (error: any) {
              Alert.alert('오류', error.message || '출금 요청에 실패했습니다.');
            } finally {
              setLoading(false);
            }
          }
        }
      ]
    );
  };
  
  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color={theme.colors.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
          USDT 출금
        </Text>
        <View style={{ width: 24 }} />
      </View>
      
      <View style={styles.content}>
        <View style={styles.section}>
          <Text style={[styles.label, { color: theme.colors.text }]}>
            받는 주소
          </Text>
          <View style={styles.addressContainer}>
            <TextInput
              style={[styles.addressInput, { 
                borderColor: theme.colors.border,
                color: theme.colors.text
              }]}
              placeholder="TRON 주소 입력"
              placeholderTextColor={theme.colors.placeholder}
              value={address}
              onChangeText={setAddress}
            />
            <TouchableOpacity
              style={styles.scanButton}
              onPress={handleQRScan}
            >
              <Icon name="qr-code-outline" size={24} color={theme.colors.primary} />
            </TouchableOpacity>
          </View>
        </View>
        
        <View style={styles.section}>
          <Text style={[styles.label, { color: theme.colors.text }]}>
            금액
          </Text>
          <AmountInput
            value={amount}
            onChange={setAmount}
            balance={balance}
            currency="USDT"
            theme={theme}
          />
        </View>
        
        <View style={styles.section}>
          <Text style={[styles.label, { color: theme.colors.text }]}>
            메모 (선택사항)
          </Text>
          <TextInput
            style={[styles.memoInput, { 
              borderColor: theme.colors.border,
              color: theme.colors.text
            }]}
            placeholder="메모 입력"
            placeholderTextColor={theme.colors.placeholder}
            value={memo}
            onChangeText={setMemo}
            multiline
          />
        </View>
        
        <FeeEstimator
          amount={parseFloat(amount) || 0}
          onFeeCalculated={setFee}
          theme={theme}
        />
        
        <TouchableOpacity
          style={[styles.button, { 
            backgroundColor: theme.colors.primary,
            opacity: loading ? 0.6 : 1
          }]}
          onPress={handleWithdraw}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.buttonText}>출금하기</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 50,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  content: {
    padding: 20,
  },
  section: {
    marginBottom: 25,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 10,
  },
  addressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  addressInput: {
    flex: 1,
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 15,
    fontSize: 16,
  },
  scanButton: {
    marginLeft: 10,
    padding: 10,
  },
  memoInput: {
    height: 80,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    textAlignVertical: 'top',
  },
  button: {
    height: 50,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default WithdrawScreen;
```

### Phase 4: 보안 및 설정 기능 (1일)

#### 4.1 생체 인증 설정
```typescript
// src/components/auth/BiometricAuth.tsx
import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import * as Keychain from 'react-native-keychain';
import Icon from 'react-native-vector-icons/Ionicons';
import { usePartnerTheme } from '../../hooks/usePartnerTheme';

interface BiometricAuthProps {
  onSuccess: () => void;
  onFail?: () => void;
}

const BiometricAuth: React.FC<BiometricAuthProps> = ({ onSuccess, onFail }) => {
  const [biometryType, setBiometryType] = useState<string | null>(null);
  const theme = usePartnerTheme();
  
  useEffect(() => {
    checkBiometry();
  }, []);
  
  const checkBiometry = async () => {
    try {
      const type = await Keychain.getSupportedBiometryType();
      setBiometryType(type);
    } catch (error) {
      console.log('Biometry check error:', error);
    }
  };
  
  const authenticate = async () => {
    try {
      const options = {
        authenticationPrompt: {
          title: '생체 인증',
          subtitle: '계속하려면 인증해주세요',
          cancel: '취소',
        },
      };
      
      const credentials = await Keychain.getInternetCredentials(
        'wallet_app',
        options
      );
      
      if (credentials) {
        onSuccess();
      } else {
        onFail?.();
      }
    } catch (error) {
      Alert.alert('인증 실패', '생체 인증에 실패했습니다.');
      onFail?.();
    }
  };
  
  if (!biometryType) return null;
  
  const getIcon = () => {
    switch (biometryType) {
      case Keychain.BIOMETRY_TYPE.FACE_ID:
        return 'scan-outline';
      case Keychain.BIOMETRY_TYPE.TOUCH_ID:
      case Keychain.BIOMETRY_TYPE.FINGERPRINT:
        return 'finger-print-outline';
      default:
        return 'lock-closed-outline';
    }
  };
  
  const getLabel = () => {
    switch (biometryType) {
      case Keychain.BIOMETRY_TYPE.FACE_ID:
        return 'Face ID로 로그인';
      case Keychain.BIOMETRY_TYPE.TOUCH_ID:
        return 'Touch ID로 로그인';
      case Keychain.BIOMETRY_TYPE.FINGERPRINT:
        return '지문으로 로그인';
      default:
        return '생체 인증으로 로그인';
    }
  };
  
  return (
    <TouchableOpacity
      style={[styles.container, { borderColor: theme.colors.primary }]}
      onPress={authenticate}
    >
      <Icon name={getIcon()} size={24} color={theme.colors.primary} />
      <Text style={[styles.label, { color: theme.colors.primary }]}>
        {getLabel()}
      </Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 50,
    borderWidth: 1,
    borderRadius: 8,
    marginTop: 15,
  },
  label: {
    marginLeft: 10,
    fontSize: 16,
    fontWeight: '500',
  },
});

export default BiometricAuth;
```

### Phase 5: 푸시 알림 및 다국어 지원 (1일)

#### 5.1 푸시 알림 설정
```typescript
// src/services/notifications.ts
import PushNotification from 'react-native-push-notification';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

class NotificationService {
  constructor() {
    this.configure();
  }
  
  configure() {
    PushNotification.configure({
      onRegister: async (token) => {
        console.log('TOKEN:', token);
        await AsyncStorage.setItem('pushToken', token.token);
        // 서버에 토큰 등록
        await this.registerToken(token.token);
      },
      
      onNotification: (notification) => {
        console.log('NOTIFICATION:', notification);
        this.handleNotification(notification);
      },
      
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
      
      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });
    
    // 채널 생성 (Android)
    PushNotification.createChannel(
      {
        channelId: 'wallet-channel',
        channelName: 'Wallet Notifications',
        channelDescription: '지갑 알림',
        importance: 4,
        vibrate: true,
      },
      (created) => console.log(`createChannel returned '${created}'`)
    );
  }
  
  async registerToken(token: string) {
    try {
      // API 호출하여 서버에 토큰 등록
      await api.notifications.registerDevice({ token });
    } catch (error) {
      console.error('Token registration failed:', error);
    }
  }
  
  handleNotification(notification: any) {
    const { data, title, message } = notification;
    
    switch (data.type) {
      case 'transaction':
        this.handleTransactionNotification(data);
        break;
      case 'security':
        this.handleSecurityNotification(data);
        break;
      case 'announcement':
        this.handleAnnouncementNotification(data);
        break;
      default:
        break;
    }
  }
  
  handleTransactionNotification(data: any) {
    // 거래 알림 처리
    // 예: 거래 상세 화면으로 이동
  }
  
  handleSecurityNotification(data: any) {
    // 보안 알림 처리
    // 예: 보안 설정 화면으로 이동
  }
  
  handleAnnouncementNotification(data: any) {
    // 공지사항 알림 처리
    // 예: 공지사항 화면으로 이동
  }
  
  // 로컬 알림 표시
  showLocalNotification(title: string, message: string, data?: any) {
    PushNotification.localNotification({
      channelId: 'wallet-channel',
      title,
      message,
      data,
      playSound: true,
      soundName: 'default',
      importance: 'high',
      priority: 'high',
    });
  }
  
  // 거래 알림 표시
  showTransactionNotification(type: 'deposit' | 'withdraw', amount: number) {
    const title = type === 'deposit' ? '입금 완료' : '출금 완료';
    const message = `${amount} USDT가 ${type === 'deposit' ? '입금' : '출금'}되었습니다.`;
    
    this.showLocalNotification(title, message, {
      type: 'transaction',
      transactionType: type,
      amount,
    });
  }
}

export default new NotificationService();
```

#### 5.2 다국어 지원
```typescript
// src/i18n/index.ts
import i18n from 'i18n-js';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as RNLocalize from 'react-native-localize';

import en from '../locales/en.json';
import ko from '../locales/ko.json';
import zh from '../locales/zh.json';
import ja from '../locales/ja.json';

const translations = { en, ko, zh, ja };

i18n.translations = translations;
i18n.fallbacks = true;

const LANGUAGE_KEY = '@app_language';

export const initI18n = async () => {
  try {
    // 저장된 언어 설정 확인
    const savedLanguage = await AsyncStorage.getItem(LANGUAGE_KEY);
    
    if (savedLanguage) {
      i18n.locale = savedLanguage;
    } else {
      // 기기 언어 감지
      const locales = RNLocalize.getLocales();
      if (locales.length > 0) {
        const { languageCode } = locales[0];
        i18n.locale = languageCode;
      } else {
        i18n.locale = 'en';
      }
    }
  } catch (error) {
    console.error('Failed to load language settings:', error);
    i18n.locale = 'en';
  }
};

export const changeLanguage = async (language: string) => {
  try {
    await AsyncStorage.setItem(LANGUAGE_KEY, language);
    i18n.locale = language;
  } catch (error) {
    console.error('Failed to save language settings:', error);
  }
};

export const t = (key: string, options?: any) => {
  return i18n.t(key, options);
};

export default i18n;
```

## 🎯 파트너사 커스터마이징 가이드

### 테마 설정
```typescript
// src/config/partnerTheme.ts
export interface PartnerTheme {
  partnerName: string;
  colors: {
    primary: string;
    secondary: string;
    background: string;
    surface: string;
    text: string;
    placeholder: string;
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
}

// 파트너사별 테마 예시
export const partnerThemes: Record<string, PartnerTheme> = {
  default: {
    partnerName: 'Wallet',
    colors: {
      primary: '#007AFF',
      secondary: '#5856D6',
      background: '#F2F2F7',
      surface: '#FFFFFF',
      text: '#000000',
      placeholder: '#8E8E93',
      border: '#C7C7CC',
      error: '#FF3B30',
      success: '#34C759',
      warning: '#FF9500',
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
  },
  partner1: {
    // 파트너사 1 커스텀 테마
  },
  partner2: {
    // 파트너사 2 커스텀 테마
  },
};
```

## 📋 구현 체크리스트

### Phase 1 ✅
- [x] React Native 프로젝트 설정
- [x] 기본 네비게이션 구조
- [x] Redux 상태 관리 설정
- [x] API 서비스 레이어

### Phase 2 ✅
- [x] 로그인/회원가입 화면
- [x] 메인 지갑 화면
- [x] 생체 인증 통합

### Phase 3 ✅
- [x] 송금 기능 구현
- [x] QR 코드 스캔/생성
- [x] 거래 내역 조회

### Phase 4 ✅
- [x] 보안 설정 (PIN, 생체인증)
- [x] 프로필 관리
- [x] 설정 화면

### Phase 5 ✅
- [x] 푸시 알림 시스템
- [x] 다국어 지원 (한/영/중/일)
- [x] 파트너 테마 시스템

## 🚀 배포 준비

### iOS 배포
```bash
# iOS 빌드
cd ios && pod install
npx react-native run-ios --configuration Release

# App Store 배포
# 1. Xcode에서 Archive 생성
# 2. App Store Connect 업로드
# 3. TestFlight 베타 테스트
# 4. 앱 심사 제출
```

### Android 배포
```bash
# APK 빌드
cd android
./gradlew assembleRelease

# AAB 빌드 (Google Play)
./gradlew bundleRelease

# Google Play Console 배포
# 1. AAB 파일 업로드
# 2. 스토어 등록 정보 작성
# 3. 내부 테스트 진행
# 4. 프로덕션 출시
```

## 📱 파트너사 앱 배포 가이드

1. **브랜딩 적용**
   - 앱 아이콘 변경
   - 스플래시 화면 커스터마이징
   - 테마 색상 설정

2. **환경 설정**
   - API 엔드포인트 설정
   - 파트너 API 키 설정
   - 푸시 알림 인증서

3. **스토어 등록**
   - 번들 ID 변경
   - 앱 이름 설정
   - 스토어 설명 작성

4. **테스트**
   - 내부 QA 테스트
   - 베타 테스트 진행
   - 보안 점검