'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { 
  Zap, 
  TrendingUp, 
  AlertTriangle, 
  Settings, 
  RefreshCw, 
  Activity, 
  Loader2,
  ArrowUp,
  ArrowDown,
  DollarSign
} from 'lucide-react'
import { formatNumber, formatCurrency, formatDate } from '@/lib/utils'
import { useEnergyPoolDetails, useEnergyTransactions, useEnergyStaking } from '@/lib/hooks'

interface EnergyPoolData {
  totalEnergy: number
  availableEnergy: number
  usedEnergy: number
  frozenTrx: number
  stakingApr: number
  dailyConsumption: number
  efficiency: number
  status: 'active' | 'warning' | 'critical'
}

interface EnergyTransaction {
  id: string
  type: 'stake' | 'unstake' | 'burn' | 'allocate'
  amount: number
  energy: number
  timestamp: string
  status: 'completed' | 'pending' | 'failed'
  txHash?: string
}

export default function EnergyPage() {
  const [partnerId] = useState(1);
  const [stakeAmount, setStakeAmount] = useState('');
  const [unstakeAmount, setUnstakeAmount] = useState('');
  const [currentPage] = useState(1);

  // API 훅 사용
  const { data: poolData, loading: poolLoading, error: poolError } = useEnergyPoolDetails(partnerId);
  const { data: transactionsData, loading: transactionsLoading, error: transactionsError } = useEnergyTransactions(partnerId, currentPage, 10);
  const { stakeForEnergy, unstakeEnergy, loading: stakingLoading } = useEnergyStaking();

  // 폴백 데이터
  const fallbackPool: EnergyPoolData = useMemo(() => ({
    totalEnergy: 1000000,
    availableEnergy: 750000,
    usedEnergy: 250000,
    frozenTrx: 50000,
    stakingApr: 4.2,
    dailyConsumption: 15000,
    efficiency: 85.5,
    status: 'active'
  }), []);

  const fallbackTransactions: EnergyTransaction[] = useMemo(() => [
    {
      id: '1',
      type: 'stake',
      amount: 10000,
      energy: 50000,
      timestamp: '2025-01-15T10:30:00Z',
      status: 'completed',
      txHash: '0x123abc456def...'
    },
    {
      id: '2',
      type: 'unstake',
      amount: 5000,
      energy: 25000,
      timestamp: '2025-01-15T09:15:00Z',
      status: 'completed',
      txHash: '0x456def789abc...'
    },
    {
      id: '3',
      type: 'allocate',
      amount: 0,
      energy: 10000,
      timestamp: '2025-01-15T08:45:00Z',
      status: 'completed'
    }
  ], []);

  // 실제 데이터 매핑
  const energyPool = useMemo(() => {
    if (!poolData || poolError) {
      return fallbackPool;
    }
    return (poolData as EnergyPoolData) || fallbackPool;
  }, [poolData, poolError, fallbackPool]);

  const transactions = useMemo(() => {
    if (!transactionsData || transactionsError) {
      return fallbackTransactions;
    }
    const apiTransactions = (transactionsData as any)?.data || (transactionsData as any)?.items || transactionsData;
    return Array.isArray(apiTransactions) ? apiTransactions : fallbackTransactions;
  }, [transactionsData, transactionsError, fallbackTransactions]);

  // 계산된 값들
  const usagePercentage = (energyPool.usedEnergy / energyPool.totalEnergy) * 100;
  const availablePercentage = (energyPool.availableEnergy / energyPool.totalEnergy) * 100;
  const estimatedDaysRemaining = Math.floor(energyPool.availableEnergy / energyPool.dailyConsumption);

  // 스테이킹 핸들러
  const handleStake = async () => {
    if (!stakeAmount || isNaN(Number(stakeAmount))) return;
    
    try {
      await stakeForEnergy(partnerId, Number(stakeAmount));
      setStakeAmount('');
      console.log('스테이킹 성공');
    } catch (error) {
      console.error('스테이킹 실패:', error);
    }
  };

  const handleUnstake = async () => {
    if (!unstakeAmount || isNaN(Number(unstakeAmount))) return;
    
    try {
      await unstakeEnergy(partnerId, Number(unstakeAmount));
      setUnstakeAmount('');
      console.log('언스테이킹 성공');
    } catch (error) {
      console.error('언스테이킹 실패:', error);
    }
  };

  // 상태별 색상
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'critical':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case 'stake':
        return <ArrowUp className="w-4 h-4 text-green-600" />;
      case 'unstake':
        return <ArrowDown className="w-4 h-4 text-red-600" />;
      case 'burn':
        return <Activity className="w-4 h-4 text-orange-600" />;
      case 'allocate':
        return <Zap className="w-4 h-4 text-blue-600" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  const getTransactionTypeName = (type: string) => {
    switch (type) {
      case 'stake':
        return '스테이킹';
      case 'unstake':
        return '언스테이킹';
      case 'burn':
        return '소모';
      case 'allocate':
        return '할당';
      default:
        return type;
    }
  };

  if (poolLoading || transactionsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>에너지 풀 데이터를 불러오는 중...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 페이지 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">에너지 풀 관리</h1>
          <p className="text-gray-600">TRX 스테이킹을 통한 에너지 생성 및 관리</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            새로고침
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            설정
          </Button>
        </div>
      </div>

      {/* 주요 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">총 에너지</p>
                <p className="text-2xl font-bold">{formatNumber(energyPool.totalEnergy)}</p>
                <p className="text-xs text-gray-500">Energy</p>
              </div>
              <Zap className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">사용 가능</p>
                <p className="text-2xl font-bold text-green-600">{formatNumber(energyPool.availableEnergy)}</p>
                <p className="text-xs text-gray-500">{availablePercentage.toFixed(1)}%</p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">스테이킹 TRX</p>
                <p className="text-2xl font-bold text-purple-600">{formatNumber(energyPool.frozenTrx)}</p>
                <p className="text-xs text-green-600">APR {energyPool.stakingApr}%</p>
              </div>
              <DollarSign className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">효율성</p>
                <p className="text-2xl font-bold text-orange-600">{energyPool.efficiency}%</p>
                <p className="text-xs text-gray-500">Pool Efficiency</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">예상 지속일</p>
                <p className="text-2xl font-bold text-indigo-600">{estimatedDaysRemaining}</p>
                <p className="text-xs text-gray-500">일</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-indigo-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 에너지 사용량 차트 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            에너지 사용 현황
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="flex justify-between mb-1">
                <span>사용된 에너지</span>
                <span>{formatNumber(energyPool.usedEnergy)} / {formatNumber(energyPool.totalEnergy)}</span>
              </div>
              <Progress value={usagePercentage} className="h-2" />
              <div className="mt-1 flex justify-between">
                <Badge className={getStatusColor(energyPool.status)}>
                  {energyPool.status === 'active' && '정상'}
                  {energyPool.status === 'warning' && '경고'}
                  {energyPool.status === 'critical' && '위험'}
                </Badge>
                <span className="text-xs text-gray-500">{usagePercentage.toFixed(1)}%</span>
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span>일일 소모량</span>
                <span>{formatNumber(energyPool.dailyConsumption)} Energy</span>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                평균 일일 에너지 소모량
              </div>
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span>예상 지속 기간</span>
                <span>{estimatedDaysRemaining}일</span>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                현재 소모율 기준
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 스테이킹 관리 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ArrowUp className="w-5 h-5 text-green-600" />
              TRX 스테이킹
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Badge className={getStatusColor(energyPool.status)}>
                {energyPool.status === 'active' && '정상'}
                {energyPool.status === 'warning' && '경고'}
                {energyPool.status === 'critical' && '위험'}
              </Badge>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">스테이킹 금액 (TRX)</label>
                <Input
                  type="number"
                  placeholder="스테이킹할 TRX 금액"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(e.target.value)}
                />
              </div>
              <Button 
                onClick={handleStake}
                disabled={stakingLoading || !stakeAmount}
                className="w-full"
              >
                {stakingLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ArrowUp className="w-4 h-4 mr-2" />
                )}
                스테이킹 실행
              </Button>
              <div className="text-xs text-gray-500">
                예상 생성 에너지: {stakeAmount ? formatNumber(Number(stakeAmount) * 5) : '0'} Energy
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ArrowDown className="w-5 h-5 text-red-600" />
              TRX 언스테이킹
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <span className="text-sm text-gray-600">
                언스테이킹 가능: {formatCurrency(energyPool.frozenTrx)} TRX
              </span>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium">언스테이킹 금액 (TRX)</label>
                <Input
                  type="number"
                  placeholder="언스테이킹할 TRX 금액"
                  value={unstakeAmount}
                  onChange={(e) => setUnstakeAmount(e.target.value)}
                />
              </div>
              <Button 
                onClick={handleUnstake}
                disabled={stakingLoading || !unstakeAmount}
                variant="outline"
                className="w-full"
              >
                {stakingLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <ArrowDown className="w-4 h-4 mr-2" />
                )}
                언스테이킹 실행
              </Button>
              <div className="text-xs text-gray-500">
                14일 잠금 기간 후 인출 가능
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 최근 거래 내역 */}
      <Card>
        <CardHeader>
          <CardTitle>최근 에너지 거래 내역</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3">타입</th>
                  <th className="text-left p-3">TRX 금액</th>
                  <th className="text-left p-3">에너지</th>
                  <th className="text-left p-3">상태</th>
                  <th className="text-left p-3">시간</th>
                  <th className="text-left p-3">트랜잭션</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx: EnergyTransaction) => (
                  <tr key={tx.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        {getTransactionIcon(tx.type)}
                        <span>{getTransactionTypeName(tx.type)}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className="font-medium">
                        {tx.amount > 0 ? formatCurrency(tx.amount) : '-'}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className="text-blue-600 font-medium">
                        {formatNumber(tx.energy)}
                      </span>
                    </td>
                    <td className="p-3">
                      <Badge 
                        className={
                          tx.status === 'completed' ? 'bg-green-100 text-green-800' :
                          tx.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }
                      >
                        {tx.status === 'completed' && '완료'}
                        {tx.status === 'pending' && '진행중'}
                        {tx.status === 'failed' && '실패'}
                      </Badge>
                    </td>
                    <td className="p-3">
                      <span className="text-sm text-gray-500">
                        {formatDate(tx.timestamp)}
                      </span>
                    </td>
                    <td className="p-3">
                      {tx.txHash ? (
                        <span className="text-xs text-blue-600 font-mono">
                          {tx.txHash.substring(0, 8)}...
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* 에러 표시 */}
      {(poolError || transactionsError) && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              <span>데이터를 불러오는 중 오류가 발생했습니다. 폴백 데이터를 표시합니다.</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
