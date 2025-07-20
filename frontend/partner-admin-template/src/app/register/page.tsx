/**
 * 회원가입 페이지 - 공통 컴포넌트 사용
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
import type { RegisterData } from '../../types';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  
  // 개발 환경에서는 임시 계정 정보를 기본값으로 설정
  const [formData, setFormData] = useState<RegisterData>({
    email: process.env.NEXT_PUBLIC_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_DEMO_EMAIL || 'partner@dantarowallet.com')
      : '',
    username: process.env.NEXT_PUBLIC_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_DEMO_USERNAME || 'dantaro_partner_admin')
      : '',
    password: process.env.NEXT_PUBLIC_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_DEMO_PASSWORD || 'DantaroPartner2024!')
      : '',
    password_confirmation: process.env.NEXT_PUBLIC_ENV === 'development' 
      ? (process.env.NEXT_PUBLIC_DEMO_PASSWORD || 'DantaroPartner2024!')
      : '',
    terms_accepted: false,
    privacy_accepted: false
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

    if (!formData.username) {
      newErrors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      newErrors.password = 'Password must contain uppercase, lowercase, and number';
    }

    if (!formData.password_confirmation) {
      newErrors.password_confirmation = 'Password confirmation is required';
    } else if (formData.password !== formData.password_confirmation) {
      newErrors.password_confirmation = 'Passwords do not match';
    }

    if (!formData.terms_accepted) {
      newErrors.terms_accepted = 'You must accept the terms of service';
    }

    if (!formData.privacy_accepted) {
      newErrors.privacy_accepted = 'You must accept the privacy policy';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      const result = await register(formData);
      
      if (result.success) {
        router.push('/dashboard');
      } else {
        setErrors({ general: result.message });
      }
    } catch (error) {
      console.error('Registration error:', error);
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
      title="Create your account"
      description="Sign up to access the partner admin dashboard"
      onSubmit={handleSubmit}
      isSubmitting={isSubmitting}
      error={errors.general}
    >
      {/* 개발 환경에서만 데모 계정 정보 표시 */}
      {process.env.NEXT_PUBLIC_ENV === 'development' && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
          <h4 className="text-sm font-medium text-green-800 mb-2">🧪 개발용 데모 계정 정보</h4>
          <div className="text-xs text-green-700 space-y-1">
            <p><strong>Email:</strong> {process.env.NEXT_PUBLIC_DEMO_EMAIL}</p>
            <p><strong>Username:</strong> {process.env.NEXT_PUBLIC_DEMO_USERNAME}</p>
            <p><strong>Password:</strong> {process.env.NEXT_PUBLIC_DEMO_PASSWORD}</p>
            <p className="text-green-600 mt-2">* 위 정보가 자동으로 입력되어 있습니다</p>
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
        id="username"
        name="username"
        type="text"
        label="Username"
        placeholder="Enter your username"
        value={formData.username}
        onChange={handleChange}
        error={errors.username}
        required
        autoComplete="username"
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
        autoComplete="new-password"
      />

      <AuthInput
        id="password_confirmation"
        name="password_confirmation"
        type="password"
        label="Confirm Password"
        placeholder="Confirm your password"
        value={formData.password_confirmation}
        onChange={handleChange}
        error={errors.password_confirmation}
        required
        autoComplete="new-password"
      />

      <div className="space-y-2">
        <AuthCheckbox
          id="terms_accepted"
          name="terms_accepted"
          label={
            <>
              I accept the{' '}
              <button type="button" className="text-blue-600 hover:text-blue-800">
                Terms of Service
              </button>
            </>
          }
          checked={formData.terms_accepted}
          onChange={handleChange}
          error={errors.terms_accepted}
        />

        <AuthCheckbox
          id="privacy_accepted"
          name="privacy_accepted"
          label={
            <>
              I accept the{' '}
              <button type="button" className="text-blue-600 hover:text-blue-800">
                Privacy Policy
              </button>
            </>
          }
          checked={formData.privacy_accepted}
          onChange={handleChange}
          error={errors.privacy_accepted}
        />
      </div>

      <AuthSubmitButton
        isSubmitting={isSubmitting}
        loadingText="Creating account..."
      >
        Create account
      </AuthSubmitButton>

      <AuthLink
        text="Already have an account?"
        linkText="Sign in"
        onClick={() => router.push('/login')}
      />
    </AuthForm>
  );
}
