'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/common/PageHeader'
import { 
  User, 
  Shield, 
  Bell, 
  Database, 
  Globe, 
  Key, 
  Mail, 
  Phone,
  Save
} from 'lucide-react'

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

interface SettingsManagementSectionProps {
  profile: PartnerProfile
  securitySettings: SecuritySettings
  systemSettings: SystemSettings
  onProfileUpdate?: (profile: PartnerProfile) => void
  onSecurityUpdate?: (settings: SecuritySettings) => void
  onSystemUpdate?: (settings: SystemSettings) => void
  onSave?: () => void
  onRefresh?: () => void
}

export function SettingsManagementSection({
  profile,
  securitySettings,
  systemSettings,
  onProfileUpdate,
  onSecurityUpdate,
  onSystemUpdate,
  onSave,
  onRefresh
}: SettingsManagementSectionProps) {
  const getTierColor = (tier: string) => {
    const colors = {
      bronze: 'bg-orange-100 text-orange-800',
      silver: 'bg-gray-100 text-gray-800',
      gold: 'bg-yellow-100 text-yellow-800',
      platinum: 'bg-purple-100 text-purple-800'
    }
    return colors[tier as keyof typeof colors] || colors.bronze
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="설정"
        description="파트너 계정 및 시스템 설정 관리"
        onRefresh={onRefresh}
      >
        <Button className="flex items-center gap-2" onClick={onSave}>
          <Save className="w-4 h-4" />
          설정 저장
        </Button>
      </PageHeader>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile" className="flex items-center gap-2">
            <User className="w-4 h-4" />
            프로필
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center gap-2">
            <Shield className="w-4 h-4" />
            보안
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            알림
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            시스템
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>파트너 프로필</CardTitle>
              <CardDescription>기본 정보 및 사업자 정보 관리</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <User className="w-8 h-8 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{profile.name}</h3>
                  <div className="flex items-center gap-2">
                    <Badge className={getTierColor(profile.tier)}>
                      {profile.tier.toUpperCase()} 등급
                    </Badge>
                    {profile.verified && (
                      <Badge className="bg-green-100 text-green-800">인증됨</Badge>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    파트너명
                  </label>
                  <Input
                    value={profile.name}
                    onChange={(e) => onProfileUpdate?.({ ...profile, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    이메일
                  </label>
                  <Input
                    type="email"
                    value={profile.email}
                    onChange={(e) => onProfileUpdate?.({ ...profile, email: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    전화번호
                  </label>
                  <Input
                    value={profile.phone}
                    onChange={(e) => onProfileUpdate?.({ ...profile, phone: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    회사명
                  </label>
                  <Input
                    value={profile.company_name}
                    onChange={(e) => onProfileUpdate?.({ ...profile, company_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    사업자등록번호
                  </label>
                  <Input
                    value={profile.business_registration}
                    onChange={(e) => onProfileUpdate?.({ ...profile, business_registration: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    주소
                  </label>
                  <Input
                    value={profile.address}
                    onChange={(e) => onProfileUpdate?.({ ...profile, address: e.target.value })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>보안 설정</CardTitle>
              <CardDescription>계정 보안 및 접근 제어 설정</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Key className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">2단계 인증</p>
                      <p className="text-sm text-gray-500">추가 보안 계층 활성화</p>
                    </div>
                  </div>
                  <Switch
                    checked={securitySettings.two_factor_enabled}
                    onCheckedChange={(checked) =>
                      onSecurityUpdate?.({ ...securitySettings, two_factor_enabled: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Bell className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">로그인 알림</p>
                      <p className="text-sm text-gray-500">새로운 로그인 시 알림 발송</p>
                    </div>
                  </div>
                  <Switch
                    checked={securitySettings.login_notifications}
                    onCheckedChange={(checked) =>
                      onSecurityUpdate?.({ ...securitySettings, login_notifications: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">API 접근</p>
                      <p className="text-sm text-gray-500">API 키를 통한 접근 허용</p>
                    </div>
                  </div>
                  <Switch
                    checked={securitySettings.api_access_enabled}
                    onCheckedChange={(checked) =>
                      onSecurityUpdate?.({ ...securitySettings, api_access_enabled: checked })
                    }
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    세션 타임아웃 (분)
                  </label>
                  <Input
                    type="number"
                    value={securitySettings.session_timeout}
                    onChange={(e) =>
                      onSecurityUpdate?.({ ...securitySettings, session_timeout: parseInt(e.target.value) })
                    }
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    IP 화이트리스트
                  </label>
                  <div className="space-y-2">
                    {securitySettings.ip_whitelist.map((ip, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <Input value={ip} readOnly />
                        <Button size="sm" variant="outline">제거</Button>
                      </div>
                    ))}
                    <Button size="sm" variant="outline">IP 추가</Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>알림 설정</CardTitle>
              <CardDescription>각종 알림 수신 설정</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Mail className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">이메일 알림</p>
                      <p className="text-sm text-gray-500">중요한 알림을 이메일로 수신</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Phone className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">SMS 알림</p>
                      <p className="text-sm text-gray-500">긴급 알림을 SMS로 수신</p>
                    </div>
                  </div>
                  <Switch />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Bell className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">거래 알림</p>
                      <p className="text-sm text-gray-500">출금 및 대량 거래 알림</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Shield className="w-5 h-5 text-gray-600" />
                    <div>
                      <p className="font-medium">보안 알림</p>
                      <p className="text-sm text-gray-500">의심스러운 활동 감지 알림</p>
                    </div>
                  </div>
                  <Switch defaultChecked />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>시스템 설정</CardTitle>
              <CardDescription>시스템 운영 및 관리 설정</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">점검 모드</p>
                    <p className="text-sm text-gray-500">시스템 점검을 위한 서비스 일시 중단</p>
                  </div>
                  <Switch
                    checked={systemSettings.maintenance_mode}
                    onCheckedChange={(checked) =>
                      onSystemUpdate?.({ ...systemSettings, maintenance_mode: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">디버그 모드</p>
                    <p className="text-sm text-gray-500">상세한 로그 및 오류 정보 표시</p>
                  </div>
                  <Switch
                    checked={systemSettings.debug_mode}
                    onCheckedChange={(checked) =>
                      onSystemUpdate?.({ ...systemSettings, debug_mode: checked })
                    }
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">자동 백업</p>
                    <p className="text-sm text-gray-500">정기적인 데이터 백업 실행</p>
                  </div>
                  <Switch
                    checked={systemSettings.auto_backup}
                    onCheckedChange={(checked) =>
                      onSystemUpdate?.({ ...systemSettings, auto_backup: checked })
                    }
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      API 요청 제한 (시간당)
                    </label>
                    <Input
                      type="number"
                      value={systemSettings.api_rate_limit}
                      onChange={(e) =>
                        onSystemUpdate?.({ ...systemSettings, api_rate_limit: parseInt(e.target.value) })
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      백업 주기
                    </label>
                    <select
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white"
                      value={systemSettings.backup_frequency}
                      onChange={(e) =>
                        onSystemUpdate?.({ ...systemSettings, backup_frequency: e.target.value as 'daily' | 'weekly' | 'monthly' })
                      }
                    >
                      <option value="daily">매일</option>
                      <option value="weekly">매주</option>
                      <option value="monthly">매월</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      시간대
                    </label>
                    <Input
                      value={systemSettings.timezone}
                      onChange={(e) =>
                        onSystemUpdate?.({ ...systemSettings, timezone: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      언어
                    </label>
                    <select
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-white"
                      value={systemSettings.language}
                      onChange={(e) =>
                        onSystemUpdate?.({ ...systemSettings, language: e.target.value })
                      }
                    >
                      <option value="ko">한국어</option>
                      <option value="en">English</option>
                      <option value="zh">中文</option>
                    </select>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
