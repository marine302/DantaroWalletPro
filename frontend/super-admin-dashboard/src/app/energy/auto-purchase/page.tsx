'use client';

import { useState } from 'react';
import { BasePage } from "@/components/ui/BasePage";
import { Section, StatCard, Button, FormField } from '@/components/ui/DarkThemeComponents';
import { Save, ToggleLeft, ToggleRight, AlertTriangle, CheckCircle } from 'lucide-react';

interface AutoPurchaseConfig {
  enabled: boolean;
  minEnergyThreshold: number;
  maxPurchaseAmount: number;
  preferredProviders: string[];
  maxPricePerEnergy: number;
  emergencyThreshold: number;
  normalMargin: number;
  highMargin: number;
  emergencyMargin: number;
  dailySpendLimit: number;
  requireApproval: boolean;
  notificationSettings: {
    email: boolean;
    sms: boolean;
    webhook: boolean;
  };
}

export default function AutoPurchaseSettingsPage() {
  const [config, setConfig] = useState<AutoPurchaseConfig>({
    enabled: false,
    minEnergyThreshold: 100000,
    maxPurchaseAmount: 1000000,
    preferredProviders: ['P2P Energy Trading', 'Energy Market Pro'],
    maxPricePerEnergy: 0.005,
    emergencyThreshold: 50000,
    normalMargin: 0.10,
    highMargin: 0.15,
    emergencyMargin: 0.20,
    dailySpendLimit: 10000,
    requireApproval: true,
    notificationSettings: {
      email: true,
      sms: false,
      webhook: true
    }
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    // 모의 저장 프로세스
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSaving(false);
    alert('설정이 저장되었습니다.');
  };

  const updateConfig = (field: keyof AutoPurchaseConfig, value: number | boolean | string[]) => {
    setConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const updateNotificationSetting = (setting: keyof AutoPurchaseConfig['notificationSettings'], value: boolean) => {
    setConfig(prev => ({
      ...prev,
      notificationSettings: {
        ...prev.notificationSettings,
        [setting]: value
      }
    }));
  };

  return (
    <BasePage title="자동 구매 설정" description="에너지 자동 구매 시스템을 설정하고 관리합니다">
      <div className="space-y-6">
        {/* 상태 요약 */}
        <Section title="현재 상태">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <StatCard
              title="자동 구매"
              value={config.enabled ? "활성화" : "비활성화"}
              trend={config.enabled ? "up" : "down"}
              icon={config.enabled ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
            />
            <StatCard
              title="최소 임계값"
              value={config.minEnergyThreshold.toLocaleString()}
            />
            <StatCard
              title="최대 구매량"
              value={config.maxPurchaseAmount.toLocaleString()}
            />
            <StatCard
              title="일일 한도"
              value={`$${config.dailySpendLimit.toLocaleString()}`}
            />
          </div>
        </Section>

        {/* 기본 설정 */}
        <Section title="기본 설정">
          <div className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
              <div>
                <h4 className="font-medium">자동 구매 활성화</h4>
                <p className="text-sm text-gray-400">에너지 부족 시 자동으로 구매를 실행합니다</p>
              </div>
              <button
                onClick={() => updateConfig('enabled', !config.enabled)}
                className="text-2xl"
              >
                {config.enabled ? 
                  <ToggleRight className="w-8 h-8 text-green-400" /> : 
                  <ToggleLeft className="w-8 h-8 text-gray-400" />
                }
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <FormField
                label="최소 에너지 임계값"
                type="number"
                value={config.minEnergyThreshold}
                onChange={(value) => updateConfig('minEnergyThreshold', Number(value))}
                placeholder="100000"
              />
              <FormField
                label="최대 구매량"
                type="number"
                value={config.maxPurchaseAmount}
                onChange={(value) => updateConfig('maxPurchaseAmount', Number(value))}
                placeholder="1000000"
              />
              <FormField
                label="최대 단가 ($)"
                type="number"
                value={config.maxPricePerEnergy}
                onChange={(value) => updateConfig('maxPricePerEnergy', Number(value))}
                placeholder="0.005"
              />
              <FormField
                label="비상 임계값"
                type="number"
                value={config.emergencyThreshold}
                onChange={(value) => updateConfig('emergencyThreshold', Number(value))}
                placeholder="50000"
              />
            </div>
          </div>
        </Section>

        {/* 마진 설정 */}
        <Section title="마진 설정">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FormField
              label="일반 마진 (%)"
              type="number"
              value={config.normalMargin * 100}
              onChange={(value) => updateConfig('normalMargin', Number(value) / 100)}
              placeholder="10"
            />
            <FormField
              label="높은 우선순위 마진 (%)"
              type="number"
              value={config.highMargin * 100}
              onChange={(value) => updateConfig('highMargin', Number(value) / 100)}
              placeholder="15"
            />
            <FormField
              label="비상 마진 (%)"
              type="number"
              value={config.emergencyMargin * 100}
              onChange={(value) => updateConfig('emergencyMargin', Number(value) / 100)}
              placeholder="20"
            />
          </div>
        </Section>

        {/* 제한 설정 */}
        <Section title="제한 설정">
          <div className="space-y-6">
            <FormField
              label="일일 지출 한도 ($)"
              type="number"
              value={config.dailySpendLimit}
              onChange={(value) => updateConfig('dailySpendLimit', Number(value))}
              placeholder="10000"
            />

            <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
              <div>
                <h4 className="font-medium">승인 필요</h4>
                <p className="text-sm text-gray-400">고액 구매 시 수동 승인을 요구합니다</p>
              </div>
              <button
                onClick={() => updateConfig('requireApproval', !config.requireApproval)}
                className="text-2xl"
              >
                {config.requireApproval ? 
                  <ToggleRight className="w-8 h-8 text-green-400" /> : 
                  <ToggleLeft className="w-8 h-8 text-gray-400" />
                }
              </button>
            </div>
          </div>
        </Section>

        {/* 알림 설정 */}
        <Section title="알림 설정">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
              <div>
                <h4 className="font-medium">이메일 알림</h4>
                <p className="text-sm text-gray-400">구매 완료 시 이메일 알림을 받습니다</p>
              </div>
              <button
                onClick={() => updateNotificationSetting('email', !config.notificationSettings.email)}
                className="text-2xl"
              >
                {config.notificationSettings.email ? 
                  <ToggleRight className="w-8 h-8 text-green-400" /> : 
                  <ToggleLeft className="w-8 h-8 text-gray-400" />
                }
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
              <div>
                <h4 className="font-medium">SMS 알림</h4>
                <p className="text-sm text-gray-400">긴급 상황 시 SMS 알림을 받습니다</p>
              </div>
              <button
                onClick={() => updateNotificationSetting('sms', !config.notificationSettings.sms)}
                className="text-2xl"
              >
                {config.notificationSettings.sms ? 
                  <ToggleRight className="w-8 h-8 text-green-400" /> : 
                  <ToggleLeft className="w-8 h-8 text-gray-400" />
                }
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
              <div>
                <h4 className="font-medium">웹훅 알림</h4>
                <p className="text-sm text-gray-400">외부 시스템으로 알림을 전송합니다</p>
              </div>
              <button
                onClick={() => updateNotificationSetting('webhook', !config.notificationSettings.webhook)}
                className="text-2xl"
              >
                {config.notificationSettings.webhook ? 
                  <ToggleRight className="w-8 h-8 text-green-400" /> : 
                  <ToggleLeft className="w-8 h-8 text-gray-400" />
                }
              </button>
            </div>
          </div>
        </Section>

        {/* 저장 버튼 */}
        <div className="flex justify-end">
          <Button onClick={handleSave} className="min-w-[120px]">
            {isSaving ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                저장 중...
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Save className="w-4 h-4" />
                설정 저장
              </div>
            )}
          </Button>
        </div>
      </div>
    </BasePage>
  );
}
