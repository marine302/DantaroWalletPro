'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '../ui/badge'
import { Progress } from '../ui/progress'
import { Zap, DollarSign, TrendingUp, Calendar, Settings, Loader2 } from 'lucide-react'
import { formatCurrency, formatNumber } from '@/lib/utils'
import { useEnergyPoolStatus } from '@/lib/hooks'

interface EnergyRentalData {
  plan_type: 'subscription' | 'pay_per_use' | 'hybrid'
  subscription_tier: string
  is_active: boolean
  monthly_energy_quota: number
  current_rate: number
  monthly_used: number
  estimated_monthly_cost: number
  daily_consumption: number
  efficiency_score: number
}

interface EnergyRentalWidgetProps {
  className?: string
}

export function EnergyRentalWidget({ className }: EnergyRentalWidgetProps) {
  // 실제 API에서 데이터 가져오기 (Doc-31 에너지 렌탈 서비스)
  const partnerId = 1; // 실제로는 현재 로그인된 파트너 ID
  const { isLoading, error } = useEnergyPoolStatus(partnerId);
  
  // 에너지 렌탈 사용량 데이터 추가 로드
  const [rentalUsage, setRentalUsage] = React.useState<EnergyRentalData | null>(null);
  const [isLoadingRental, setIsLoadingRental] = React.useState(true);

  React.useEffect(() => {
    const loadRentalData = async () => {
      try {
        // TODO: 실제 API 연동 (현재는 임시 테스트 데이터 사용)
        console.log('에너지 렌탈 데이터 로드 시작...');
        
        // 임시 테스트 데이터로 화면 검증
        setTimeout(() => {
          setRentalUsage({
            plan_type: 'subscription',
            subscription_tier: 'Standard',
            is_active: true,
            monthly_energy_quota: 1000000,
            current_rate: 0.000420,
            monthly_used: 650000,
            estimated_monthly_cost: 273.0,
            daily_consumption: 21500,
            efficiency_score: 85.5
          });
          setIsLoadingRental(false);
          console.log('에너지 렌탈 데이터 로드 완료 (테스트 데이터)');
        }, 1000);
        
        /* 실제 API 호출 코드 (나중에 활성화)
        const [currentPlan, usageStats, costAnalysis] = await Promise.all([
          api.energyRental.getCurrentPlan(partnerId),
          api.energyRental.getUsageStats(partnerId, '30d'),
          api.energyRental.getCostAnalysis(partnerId)
        ]);
        
        // API 타입이 정의되지 않아서 임시로 unknown 사용
        const currentPlanData = currentPlan as Record<string, unknown>;
        const usageStatsData = usageStats as Record<string, unknown>;
        const costAnalysisData = costAnalysis as Record<string, unknown>;
        
        setRentalUsage({
          plan_type: (currentPlanData?.plan_type as 'subscription' | 'pay_per_use' | 'hybrid') || 'subscription',
          subscription_tier: (currentPlanData?.tier as string) || 'Standard',
          is_active: (currentPlanData?.is_active as boolean) || true,
          monthly_energy_quota: (currentPlanData?.monthly_quota as number) || 1000000,
          current_rate: (costAnalysisData?.current_rate as number) || 0.000420,
          monthly_used: (usageStatsData?.monthly_used as number) || 650000,
          estimated_monthly_cost: (costAnalysisData?.estimated_cost as number) || 273.0,
          daily_consumption: (usageStatsData?.daily_average as number) || 21500,
          efficiency_score: (usageStatsData?.efficiency_score as number) || 85.5
        });
        setIsLoadingRental(false);
        */
      } catch (error) {
        console.error('에너지 렌탈 데이터 로드 실패:', error);
        // 폴백 데이터 사용
        setRentalUsage({
          plan_type: 'subscription',
          subscription_tier: 'Standard',
          is_active: true,
          monthly_energy_quota: 1000000,
          current_rate: 0.000420,
          monthly_used: 650000,
          estimated_monthly_cost: 273.0,
          daily_consumption: 21500,
          efficiency_score: 85.5
        });
        setIsLoadingRental(false);
      }
    };

    loadRentalData();
  }, [partnerId]);

  // 로딩 상태
  if (isLoading || isLoadingRental || !rentalUsage) {
    return (
      <Card className={`${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Zap className="w-5 h-5 text-yellow-500" />
            <span className="text-gray-900">에너지 렌탈 현황</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-500">데이터 로딩 중...</span>
        </CardContent>
      </Card>
    );
  }

  // 오류 상태
  if (error) {
    return (
      <Card className={`${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900">
            <Zap className="w-5 h-5 text-yellow-500" />
            <span className="text-gray-900">에너지 렌탈 현황</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center py-8">
          <p className="text-red-500 mb-2">데이터 로드 실패</p>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => window.location.reload()}
          >
            다시 시도
          </Button>
        </CardContent>
      </Card>
    );
  }

  const usagePercentage = (rentalUsage.monthly_used / rentalUsage.monthly_energy_quota) * 100
  const remainingEnergy = rentalUsage.monthly_energy_quota - rentalUsage.monthly_used
  const estimatedDaysRemaining = Math.floor(remainingEnergy / rentalUsage.daily_consumption)

  return (
    <Card className={`${className}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold flex items-center gap-2 text-gray-900">
          <Zap className="w-5 h-5 text-yellow-500" />
          에너지 렌탈 현황
        </CardTitle>
        <Badge variant={rentalUsage.is_active ? 'default' : 'secondary'}>
          {rentalUsage.subscription_tier}
        </Badge>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 구독 플랜 정보 */}
        {rentalUsage.plan_type === 'subscription' && (
          <div className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">월 할당량</span>
              <span className="font-medium text-gray-900">
                {formatNumber(rentalUsage.monthly_energy_quota)} 에너지
              </span>
            </div>
            
            <div className="space-y-2">
              <Progress value={usagePercentage} className="h-2" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>{formatNumber(rentalUsage.monthly_used)} 사용</span>
                <span>{usagePercentage.toFixed(1)}% 사용됨</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="space-y-1">
                <span className="text-gray-600">남은 에너지</span>
                <div className="font-medium text-green-600">
                  {formatNumber(remainingEnergy)}
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-gray-600">예상 소진일</span>
                <div className="font-medium text-blue-600">
                  {estimatedDaysRemaining}일 후
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* 실시간 효율성 */}
        <div className="border-t pt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">에너지 효율성</span>
            <div className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-green-500" />
              <span className="text-sm font-medium text-green-600">
                {rentalUsage.efficiency_score}%
              </span>
            </div>
          </div>
          <Progress value={rentalUsage.efficiency_score} className="h-1.5" />
        </div>
        
        {/* 비용 정보 */}
        <div className="border-t pt-4 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">현재 단가</span>
            <span className="font-medium text-gray-900">
              {rentalUsage.current_rate} TRX/에너지
            </span>
          </div>
          
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">일일 평균 소비량</span>
            <span className="font-medium text-gray-900">
              {formatNumber(rentalUsage.daily_consumption)} 에너지
            </span>
          </div>
          
          <div className="flex justify-between items-center">
            <span className="text-gray-600">이번 달 예상 비용</span>
            <div className="text-right">
              <div className="font-semibold text-lg flex items-center gap-1 text-gray-900">
                <DollarSign className="w-4 h-4" />
                {formatCurrency(rentalUsage.estimated_monthly_cost)}
              </div>
              <div className="text-xs text-gray-500">
                TRX 기준
              </div>
            </div>
          </div>
        </div>
        
        {/* 액션 버튼 */}
        <div className="flex gap-2 pt-2">
          <Button variant="outline" size="sm" className="flex-1">
            <Calendar className="w-3 h-3 mr-1" />
            사용 내역
          </Button>
          <Button variant="outline" size="sm" className="flex-1">
            <Settings className="w-3 h-3 mr-1" />
            플랜 변경
          </Button>
        </div>
        
        {/* 알림 메시지 */}
        {usagePercentage > 80 && (
          <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-yellow-800">
                에너지 사용량이 80%를 초과했습니다. 플랜 업그레이드를 고려해보세요.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default EnergyRentalWidget
