/**
 * 회원가입 페이지
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import type { RegisterData } from '../../types';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  
  const [formData, setFormData] = useState<RegisterData>({
    email: '',
    username: '',
    password: '',
    password_confirmation: '',
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">DantaroWallet</h1>
          <p className="mt-2 text-sm text-gray-600">Partner Admin Dashboard</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create your account</CardTitle>
            <CardDescription>
              Sign up to access the partner admin dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {errors.general && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                  {errors.general}
                </div>
              )}

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email address
                </label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className={errors.email ? 'border-red-300' : ''}
                  placeholder="Enter your email"
                />
                {errors.email && (
                  <p className="mt-1 text-xs text-red-600">{errors.email}</p>
                )}
              </div>

              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                  Username
                </label>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={formData.username}
                  onChange={handleChange}
                  className={errors.username ? 'border-red-300' : ''}
                  placeholder="Enter your username"
                />
                {errors.username && (
                  <p className="mt-1 text-xs text-red-600">{errors.username}</p>
                )}
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password
                </label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className={errors.password ? 'border-red-300' : ''}
                  placeholder="Enter your password"
                />
                {errors.password && (
                  <p className="mt-1 text-xs text-red-600">{errors.password}</p>
                )}
              </div>

              <div>
                <label htmlFor="password_confirmation" className="block text-sm font-medium text-gray-700">
                  Confirm Password
                </label>
                <Input
                  id="password_confirmation"
                  name="password_confirmation"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={formData.password_confirmation}
                  onChange={handleChange}
                  className={errors.password_confirmation ? 'border-red-300' : ''}
                  placeholder="Confirm your password"
                />
                {errors.password_confirmation && (
                  <p className="mt-1 text-xs text-red-600">{errors.password_confirmation}</p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center">
                  <input
                    id="terms_accepted"
                    name="terms_accepted"
                    type="checkbox"
                    checked={formData.terms_accepted}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="terms_accepted" className="ml-2 block text-sm text-gray-900">
                    I accept the{' '}
                    <button type="button" className="text-blue-600 hover:text-blue-800">
                      Terms of Service
                    </button>
                  </label>
                </div>
                {errors.terms_accepted && (
                  <p className="text-xs text-red-600">{errors.terms_accepted}</p>
                )}

                <div className="flex items-center">
                  <input
                    id="privacy_accepted"
                    name="privacy_accepted"
                    type="checkbox"
                    checked={formData.privacy_accepted}
                    onChange={handleChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="privacy_accepted" className="ml-2 block text-sm text-gray-900">
                    I accept the{' '}
                    <button type="button" className="text-blue-600 hover:text-blue-800">
                      Privacy Policy
                    </button>
                  </label>
                </div>
                {errors.privacy_accepted && (
                  <p className="text-xs text-red-600">{errors.privacy_accepted}</p>
                )}
              </div>

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                    Creating account...
                  </>
                ) : (
                  'Create account'
                )}
              </Button>

              <div className="text-center">
                <div className="text-sm text-gray-600">
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => router.push('/login')}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Sign in
                  </button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        <div className="text-center text-xs text-gray-500">
          <p>© 2024 DantaroWallet. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}
