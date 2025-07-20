'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { SettingsManagementSection } from '@/components/settings/SettingsManagementSection'

interface PartnerProfile {
  id: string
  name: string
  email: string
  phone: string
  company_name: string
  business_registration: string
  address: string
  created_at: string
  verified: boolean
  tier: 'bronze' | 'silver' | 'gold' | 'platinum'
}

interface SecuritySettings {
  two_factor_enabled: boolean
  login_notifications: boolean
  api_access_enabled: boolean
  ip_whitelist: string[]
  session_timeout: number
}

interface SystemSettings {
  maintenance_mode: boolean
  debug_mode: boolean
  api_rate_limit: number
  auto_backup: boolean
  backup_frequency: 'daily' | 'weekly' | 'monthly'
  timezone: string
  language: string
}

export default function SettingsPage() {
  const [profile, setProfile] = useState<PartnerProfile>({
    id: 'partner_001',
    name: 'DantaroWallet Partner',
    email: 'partner@dantarowallet.com',
    phone: '+82-10-1234-5678',
    company_name: 'DantaroWallet Co., Ltd.',
    business_registration: '123-45-67890',
    address: '서울특별시 강남구 테헤란로 123',
    created_at: '2024-01-15T09:00:00Z',
    verified: true,
    tier: 'gold'
  })

  const [securitySettings, setSecuritySettings] = useState<SecuritySettings>({
    two_factor_enabled: true,
    login_notifications: true,
    api_access_enabled: true,
    ip_whitelist: ['192.168.1.100', '203.0.113.0'],
    session_timeout: 30
  })

  const [systemSettings, setSystemSettings] = useState<SystemSettings>({
    maintenance_mode: false,
    debug_mode: false,
    api_rate_limit: 1000,
    auto_backup: true,
    backup_frequency: 'daily',
    timezone: 'Asia/Seoul',
    language: 'ko'
  })

  const handleSave = () => {
    // TODO: API 호출하여 설정 저장
    console.log('Saving settings:', { profile, securitySettings, systemSettings })
  }

  const handleRefresh = () => {
    // TODO: 설정 데이터 새로고침
    console.log('Refreshing settings...')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6">
        <SettingsManagementSection
          profile={profile}
          securitySettings={securitySettings}
          systemSettings={systemSettings}
          onProfileUpdate={setProfile}
          onSecurityUpdate={setSecuritySettings}
          onSystemUpdate={setSystemSettings}
          onSave={handleSave}
          onRefresh={handleRefresh}
        />
      </div>
    </Sidebar>
  )
}
