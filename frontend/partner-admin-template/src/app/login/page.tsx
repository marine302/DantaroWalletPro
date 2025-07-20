/**
 * 로그인 페이지 - 공통 컴포넌트 사용
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';
import { 
  AuthForm, 
  AuthInput, 
  AuthCheckbox, 
  AuthSubmitButton, 
  AuthLink 
} from '../../components/auth';
import type { LoginCredentials } from '../../types';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  
  // 개발 환경에서는 임시 계정 정보를 기본값으로 설정
  const [formData, setFormData] = useState<LoginCredentials>({
    email: process.env.NEXT_PUBLIC_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_DEMO_EMAIL || 'partner@dantarowallet.com')
      : '',
    password: process.env.NEXT_PUBLIC_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_DEMO_PASSWORD || 'DantaroPartner2024!')
      : '',
    remember_me: false
  });
  
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // 입력 시 해당 필드 에러 제거
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const result = await login(formData);
      
      if (result.success) {
        router.push('/dashboard');
      } else {
        setErrors({ general: result.message });
      }
    } catch (error) {
      console.error('Login error:', error);
      setErrors({ general: 'An unexpected error occurred' });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  return (
    <AuthForm
      title="Sign in to your account"
      description="Enter your email and password to access the admin dashboard"
      onSubmit={handleSubmit}
      isSubmitting={isSubmitting}
      error={errors.general}
    >
      {/* 개발 환경에서만 데모 계정 정보 표시 */}
      {process.env.NEXT_PUBLIC_ENV === 'development' && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
          <h4 className="text-sm font-medium text-blue-800 mb-2">🧪 개발용 데모 계정</h4>
          <div className="text-xs text-blue-700 space-y-1">
            <p><strong>Email:</strong> {process.env.NEXT_PUBLIC_DEMO_EMAIL}</p>
            <p><strong>Password:</strong> {process.env.NEXT_PUBLIC_DEMO_PASSWORD}</p>
            <p className="text-blue-600 mt-2">* 위 정보가 자동으로 입력되어 있습니다</p>
          </div>
        </div>
      )}

      <AuthInput
        id="email"
        name="email"
        type="email"
        label="Email address"
        placeholder="Enter your email"
        value={formData.email}
        onChange={handleChange}
        error={errors.email}
        required
        autoComplete="email"
      />

      <AuthInput
        id="password"
        name="password"
        type="password"
        label="Password"
        placeholder="Enter your password"
        value={formData.password}
        onChange={handleChange}
        error={errors.password}
        required
        autoComplete="current-password"
      />

      <AuthCheckbox
        id="remember_me"
        name="remember_me"
        label="Remember me"
        checked={formData.remember_me || false}
        onChange={handleChange}
      />

      <AuthSubmitButton
        isSubmitting={isSubmitting}
        loadingText="Signing in..."
      >
        Sign in
      </AuthSubmitButton>

      <div className="text-center">
        <button
          type="button"
          onClick={() => router.push('/forgot-password')}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          Forgot your password?
        </button>
      </div>

      <AuthLink
        text="Don&apos;t have an account?"
        linkText="Sign up"
        onClick={() => router.push('/register')}
      />
    </AuthForm>
  );
}
