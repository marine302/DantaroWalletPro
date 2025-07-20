/**
 * 인증 폼 공통 컴포넌트
 */

import React from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';

interface AuthFormProps {
  title: string;
  description: string;
  children: React.ReactNode;
  onSubmit: (e: React.FormEvent) => void;
  isSubmitting?: boolean;
  error?: string;
}

export function AuthForm({ 
  title, 
  description, 
  children, 
  onSubmit,
  error 
}: AuthFormProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* 브랜드 헤더 */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">DantaroWallet</h1>
          <p className="mt-2 text-sm text-gray-600">Partner Admin Dashboard</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
              )}
              
              {children}
            </form>
          </CardContent>
        </Card>

        {/* 푸터 */}
        <div className="text-center text-xs text-gray-500">
          <p>© 2024 DantaroWallet. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

interface AuthInputProps {
  id: string;
  name: string;
  type: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
  required?: boolean;
  autoComplete?: string;
}

export function AuthInput({
  id,
  name,
  type,
  label,
  placeholder,
  value,
  onChange,
  error,
  required = false,
  autoComplete
}: AuthInputProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">
        {label}
      </label>
      <Input
        id={id}
        name={name}
        type={type}
        autoComplete={autoComplete}
        required={required}
        value={value}
        onChange={onChange}
        className={error ? 'border-red-300' : ''}
        placeholder={placeholder}
      />
      {error && (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}

interface AuthCheckboxProps {
  id: string;
  name: string;
  label: React.ReactNode;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  error?: string;
}

export function AuthCheckbox({
  id,
  name,
  label,
  checked,
  onChange,
  error
}: AuthCheckboxProps) {
  return (
    <div>
      <div className="flex items-center">
        <input
          id={id}
          name={name}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor={id} className="ml-2 block text-sm text-gray-900">
          {label}
        </label>
      </div>
      {error && (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}

interface AuthSubmitButtonProps {
  isSubmitting: boolean;
  loadingText: string;
  children: React.ReactNode;
}

export function AuthSubmitButton({ 
  isSubmitting, 
  loadingText, 
  children 
}: AuthSubmitButtonProps) {
  return (
    <Button
      type="submit"
      disabled={isSubmitting}
      className="w-full"
    >
      {isSubmitting ? (
        <>
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
          {loadingText}
        </>
      ) : (
        children
      )}
    </Button>
  );
}

interface AuthLinkProps {
  text: string;
  linkText: string;
  onClick: () => void;
}

export function AuthLink({ text, linkText, onClick }: AuthLinkProps) {
  return (
    <div className="text-center">
      <div className="text-sm text-gray-600">
        {text}{' '}
        <button
          type="button"
          onClick={onClick}
          className="text-blue-600 hover:text-blue-800"
        >
          {linkText}
        </button>
      </div>
    </div>
  );
}
