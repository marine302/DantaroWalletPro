'use client';

import React from 'react'
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { PageHeader } from '@/components/ui/DarkThemeComponents'

interface BasePageProps {
  title: string
  description?: string
  headerActions?: React.ReactNode
  children: React.ReactNode
  className?: string
}

export const BasePage: React.FC<BasePageProps> = ({
  title,
  description,
  headerActions,
  children,
  className = ""
}) => {
  return (
    <DashboardLayout>
      <div className={`max-w-7xl mx-auto ${className}`}>
        <PageHeader
          title={title}
          description={description}
        >
          {headerActions}
        </PageHeader>
        {children}
      </div>
    </DashboardLayout>
  )
}

export default BasePage;
