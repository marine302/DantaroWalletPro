'use client';

import { useState } from 'react';
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Settings, Save, ToggleLeft, ToggleRight, AlertTriangle, CheckCircle } from 'lucide-react';

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
    minEnergyThreshold: 500000,
    maxPurchaseAmount: 2000000,
    preferredProviders: ['1', '4'],
    maxPricePerEnergy: 0.006,
    emergencyThreshold: 100000,
    normalMargin: 0.10,
    highMargin: 0.15,
    emergencyMargin: 0.25,
    dailySpendLimit: 1000,
    requireApproval: false,
    notificationSettings: {
      email: true,
      sms: false,
      webhook: true
    }
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const providers = [
    { id: '1', name: 'JustLend Energy' },
    { id: '2', name: 'TronNRG' },
    { id: '3', name: 'TRONSCAN Energy' },
    { id: '4', name: 'P2P Energy Trading' }
  ];

  const handleSave = async () => {
    setIsSaving(true);
    
    // 모의 API 호출
    setTimeout(() => {
      setIsSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 1000);
  };

  const toggleProvider = (providerId: string) => {
    setConfig(prev => ({
      ...prev,
      preferredProviders: prev.preferredProviders.includes(providerId)
        ? prev.preferredProviders.filter(id => id !== providerId)
        : [...prev.preferredProviders, providerId]
    }));
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">자동 구매 설정</h1>
          <p className="text-gray-600 mt-1">
            에너지 부족 시 자동으로 외부 공급자에서 구매하는 설정을 관리합니다.
          </p>
        </div>

        <div className="space-y-6">
          {/* 기본 설정 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                기본 설정
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">자동 구매 활성화</h3>
                    <p className="text-sm text-gray-500">
                      에너지 부족 시 자동으로 외부에서 구매
                    </p>
                  </div>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, enabled: !prev.enabled }))}
                    className="flex items-center"
                  >
                    {config.enabled ? (
                      <ToggleRight className="w-8 h-8 text-green-500" />
                    ) : (
                      <ToggleLeft className="w-8 h-8 text-gray-400" />
                    )}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      최소 에너지 임계값
                    </label>
                    <input
                      type="number"
                      value={config.minEnergyThreshold}
                      onChange={(e) => setConfig(prev => ({ ...prev, minEnergyThreshold: Number(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={!config.enabled}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      이 값 이하로 떨어지면 자동 구매 실행
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      최대 구매 수량
                    </label>
                    <input
                      type="number"
                      value={config.maxPurchaseAmount}
                      onChange={(e) => setConfig(prev => ({ ...prev, maxPurchaseAmount: Number(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={!config.enabled}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      한 번에 구매할 수 있는 최대 에너지
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      최대 가격 (per 에너지)
                    </label>
                    <input
                      type="number"
                      step="0.0001"
                      value={config.maxPricePerEnergy}
                      onChange={(e) => setConfig(prev => ({ ...prev, maxPricePerEnergy: Number(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={!config.enabled}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      이 가격 이상이면 구매하지 않음
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      일일 지출 한도 (TRX)
                    </label>
                    <input
                      type="number"
                      value={config.dailySpendLimit}
                      onChange={(e) => setConfig(prev => ({ ...prev, dailySpendLimit: Number(e.target.value) }))}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      disabled={!config.enabled}
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      하루 최대 지출 금액
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    긴급 임계값
                  </label>
                  <input
                    type="number"
                    value={config.emergencyThreshold}
                    onChange={(e) => setConfig(prev => ({ ...prev, emergencyThreshold: Number(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!config.enabled}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    이 값 이하로 떨어지면 긴급 구매 실행 (높은 마진 적용)
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 공급자 설정 */}
          <Card>
            <CardHeader>
              <CardTitle>선호 공급자 설정</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  자동 구매 시 우선적으로 사용할 공급자를 선택하세요.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {providers.map(provider => (
                    <div
                      key={provider.id}
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        config.preferredProviders.includes(provider.id)
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      } ${!config.enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                      onClick={() => config.enabled && toggleProvider(provider.id)}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{provider.name}</span>
                        {config.preferredProviders.includes(provider.id) && (
                          <CheckCircle className="w-5 h-5 text-blue-500" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 마진 설정 */}
          <Card>
            <CardHeader>
              <CardTitle>마진 설정</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    일반 마진 (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.normalMargin * 100}
                    onChange={(e) => setConfig(prev => ({ ...prev, normalMargin: Number(e.target.value) / 100 }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!config.enabled}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    일반 상황에서 적용되는 마진
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    높은 우선순위 마진 (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.highMargin * 100}
                    onChange={(e) => setConfig(prev => ({ ...prev, highMargin: Number(e.target.value) / 100 }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!config.enabled}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    높은 우선순위 상황에서 적용되는 마진
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    긴급 마진 (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={config.emergencyMargin * 100}
                    onChange={(e) => setConfig(prev => ({ ...prev, emergencyMargin: Number(e.target.value) / 100 }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={!config.enabled}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    긴급 상황에서 적용되는 마진
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 승인 및 알림 설정 */}
          <Card>
            <CardHeader>
              <CardTitle>승인 및 알림 설정</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">수동 승인 필요</h3>
                    <p className="text-sm text-gray-500">
                      자동 구매 실행 전 관리자 승인 필요
                    </p>
                  </div>
                  <button
                    onClick={() => setConfig(prev => ({ ...prev, requireApproval: !prev.requireApproval }))}
                    className="flex items-center"
                    disabled={!config.enabled}
                  >
                    {config.requireApproval ? (
                      <ToggleRight className="w-8 h-8 text-green-500" />
                    ) : (
                      <ToggleLeft className="w-8 h-8 text-gray-400" />
                    )}
                  </button>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-4">알림 설정</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">이메일 알림</span>
                      <button
                        onClick={() => setConfig(prev => ({
                          ...prev,
                          notificationSettings: {
                            ...prev.notificationSettings,
                            email: !prev.notificationSettings.email
                          }
                        }))}
                        className="flex items-center"
                        disabled={!config.enabled}
                      >
                        {config.notificationSettings.email ? (
                          <ToggleRight className="w-6 h-6 text-green-500" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-gray-400" />
                        )}
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">SMS 알림</span>
                      <button
                        onClick={() => setConfig(prev => ({
                          ...prev,
                          notificationSettings: {
                            ...prev.notificationSettings,
                            sms: !prev.notificationSettings.sms
                          }
                        }))}
                        className="flex items-center"
                        disabled={!config.enabled}
                      >
                        {config.notificationSettings.sms ? (
                          <ToggleRight className="w-6 h-6 text-green-500" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-gray-400" />
                        )}
                      </button>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">웹훅 알림</span>
                      <button
                        onClick={() => setConfig(prev => ({
                          ...prev,
                          notificationSettings: {
                            ...prev.notificationSettings,
                            webhook: !prev.notificationSettings.webhook
                          }
                        }))}
                        className="flex items-center"
                        disabled={!config.enabled}
                      >
                        {config.notificationSettings.webhook ? (
                          <ToggleRight className="w-6 h-6 text-green-500" />
                        ) : (
                          <ToggleLeft className="w-6 h-6 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 주의사항 */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-gray-900 mb-2">주의사항</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• 자동 구매는 설정된 임계값과 조건에 따라 실행됩니다</li>
                    <li>• 일일 지출 한도를 초과하면 자동 구매가 중단됩니다</li>
                    <li>• 공급자 상황에 따라 구매가 실패할 수 있습니다</li>
                    <li>• 긴급 상황에서는 높은 마진이 적용됩니다</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 저장 버튼 */}
          <div className="flex justify-end">
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="min-w-32"
            >
              {isSaving ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  저장 중...
                </div>
              ) : saved ? (
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 mr-2" />
                  저장됨
                </div>
              ) : (
                <div className="flex items-center">
                  <Save className="w-4 h-4 mr-2" />
                  설정 저장
                </div>
              )}
            </Button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
