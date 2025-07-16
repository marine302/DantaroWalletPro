'use client';

import React from 'react'
import { createDarkClasses } from '@/styles/dark-theme'

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

export const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  icon, 
  trend, 
  description 
}) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up': return 'text-green-400'
      case 'down': return 'text-red-400'
      default: return 'text-gray-300'
    }
  }

  return (
    <div className={createDarkClasses.statCard()}>
      <div className="flex items-center justify-between mb-2">
        <span className={createDarkClasses.description()}>{title}</span>
        {icon && <div className="text-blue-400">{icon}</div>}
      </div>
      <div className={`text-2xl font-bold text-white`}>
        {value}
      </div>
      {description && (
        <div className={`text-xs mt-1 ${getTrendColor()}`}>
          {description}
        </div>
      )}
    </div>
  )
}

interface SectionProps {
  title: string
  children: React.ReactNode
  className?: string
}

export const Section: React.FC<SectionProps> = ({ title, children, className = '' }) => {
  return (
    <div className={`${createDarkClasses.card()} ${className}`}>
      <h3 className={createDarkClasses.sectionTitle()}>{title}</h3>
      {children}
    </div>
  )
}

interface FormFieldProps {
  label: string
  type?: string
  value: string | number
  onChange: (value: string | number) => void
  placeholder?: string
  min?: number
}

export const FormField: React.FC<FormFieldProps> = ({
  label,
  type = 'text',
  value,
  onChange,
  placeholder,
  min
}) => {
  return (
    <div className="flex items-center gap-4">
      <label className={createDarkClasses.label()}>{label}:</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(type === 'number' ? parseInt(e.target.value) : e.target.value)}
        className={createDarkClasses.input()}
        placeholder={placeholder}
        min={min}
      />
    </div>
  )
}

interface ButtonProps {
  children: React.ReactNode
  onClick?: () => void
  variant?: 'primary' | 'secondary'
  className?: string
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  onClick, 
  variant = 'primary',
  className = '' 
}) => {
  const baseClasses = variant === 'primary' 
    ? createDarkClasses.button.primary()
    : createDarkClasses.button.secondary()
    
  return (
    <button
      onClick={onClick}
      className={`${baseClasses} ${className}`}
    >
      {children}
    </button>
  )
}
