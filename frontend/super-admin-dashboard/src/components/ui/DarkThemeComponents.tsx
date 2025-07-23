'use client';

import React, { useMemo } from 'react';
import { createDarkClasses } from '@/styles/dark-theme';

interface PageHeaderProps {
  title: string
  description?: string
  children?: React.ReactNode
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, description, children }) => {
  return (
    <div className="mb-8">
      <h1 className={createDarkClasses.pageTitle()}>{title}</h1>
      {description && (
        <div className={createDarkClasses.description()}>
          {description}
        </div>
      )}
      {children && (
        <div className="flex items-center gap-4 mt-6">
          {children}
        </div>
      )}
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string | number
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
  description?: string
}

export const StatCard: React.FC<StatCardProps> = React.memo(({
  title,
  value,
  icon,
  trend,
  description
}) => {
  const _getTrendColor = useMemo(() => {
    switch (trend) {
      case 'up': return 'text-green-400'
      case 'down': return 'text-red-400'
      default: return 'text-gray-300'
    }
  }, [trend]);

  const _formattedValue = useMemo(() => {
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return value;
  }, [value]);

  return (
    <div className={createDarkClasses.statCard()}>
      <div className="flex items-center justify-between mb-2">
        <span className={createDarkClasses.description()}>{title}</span>
        {icon && <div className="text-blue-400">{icon}</div>}
      </div>
      <div className={`text-2xl font-bold text-white`}>
        {formattedValue}
      </div>
      {description && (
        <div className={`text-xs mt-1 ${getTrendColor}`}>
          {description}
        </div>
      )}
    </div>
  )
});

StatCard.displayName = 'StatCard';

interface SectionProps {
  title: string
  children: React.ReactNode
  className?: string
}

export const Section: React.FC<SectionProps> = React.memo(({ title, children, className = '' }) => {
  const _sectionClasses = useMemo(() =>
    `${createDarkClasses.card()} ${className}`,
    [className]
  );

  return (
    <div className={sectionClasses}>
      <h3 className={createDarkClasses.sectionTitle()}>{title}</h3>
      {children}
    </div>
  )
});

Section.displayName = 'Section';

interface FormFieldProps {
  label: string
  type?: string
  value: string | number
  onChange: (value: string | number) => void
  placeholder?: string
  min?: number | string
  max?: number | string
  step?: string
  helpText?: string
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  min,
  max,
  step,
  helpText
}) => {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-4">
        <label className={createDarkClasses.label()}>{label}:</label>
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(type === 'number' ? parseInt(e.target.value) : e.target.value)}
          className={createDarkClasses.input()}
          placeholder={placeholder}
          min={min}
          max={max}
          step={step}
        />
      </div>
      {helpText && (
        <p className="text-sm text-gray-400 ml-0">{helpText}</p>
      )}
    </div>
  )
}

interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary' | 'danger' | 'outline'
  className?: string
  disabled?: boolean
}

export const Button: React.FC<ButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  className = '',
  disabled = false
}) => {
  const _getVariantClasses = () => {
    switch (variant) {
      case 'primary':
        return createDarkClasses.button.primary()
      case 'secondary':
        return createDarkClasses.button.secondary()
      case 'danger':
        return 'px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
      case 'outline':
        return 'px-4 py-2 rounded-lg border border-gray-600 bg-transparent text-gray-200 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
      default:
        return createDarkClasses.button.primary()
    }
  }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${getVariantClasses()} ${className}`}
    >
      {children}
    </button>
  )
}
