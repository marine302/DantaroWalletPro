/**
 * 비밀번호 재설정 요청 페이지 - 공통 컴포넌트 사용
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '../../lib/services/auth.service';
import { 
  AuthForm, 
  AuthInput, 
  AuthSubmitButton, 
  AuthLink 
} from '../../components/auth';

export default function ForgotPasswordPage() {
  const router = useRouter();
  
  const [email, setEmail] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (errors.email) {
      setErrors(prev => ({ ...prev, email: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await authService.requestPasswordReset(email);
      setIsSuccess(true);
    } catch (error) {
      console.error('Password reset request error:', error);
      setErrors({ general: 'Failed to send reset email. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <AuthForm
        title="Check your email"
        description="We've sent a password reset link to your email address"
        onSubmit={() => {}}
      >
        <div className="text-center py-4">
          <p className="text-sm text-gray-600 mb-4">
            If an account with that email exists, you&apos;ll receive a password reset link shortly.
          </p>
          <p className="text-xs text-gray-500">
            Didn&apos;t receive the email? Check your spam folder or try again in a few minutes.
          </p>
        </div>

        <AuthLink
          text="Remember your password?"
          linkText="Back to sign in"
          onClick={() => router.push('/login')}
        />
      </AuthForm>
    );
  }

  return (
    <AuthForm
      title="Reset your password"
      description="Enter your email address and we'll send you a reset link"
      onSubmit={handleSubmit}
      isSubmitting={isSubmitting}
      error={errors.general}
    >
      <AuthInput
        id="email"
        name="email"
        type="email"
        label="Email address"
        placeholder="Enter your email"
        value={email}
        onChange={handleChange}
        error={errors.email}
        required
        autoComplete="email"
      />

      <AuthSubmitButton
        isSubmitting={isSubmitting}
        loadingText="Sending reset link..."
      >
        Send reset link
      </AuthSubmitButton>

      <AuthLink
        text="Remember your password?"
        linkText="Back to sign in"
        onClick={() => router.push('/login')}
      />
    </AuthForm>
  );
}
