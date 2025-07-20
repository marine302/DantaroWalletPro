'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '../ui/badge'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { Activity, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react'
import { formatNumber, formatCurrency } from '@/lib/utils'

interface EnergyUsageData {
  time: string
  usage: number
  cost: number
  efficiency: number
}

interface RealtimeEnergyMonitorProps {
  className?: string
}

export function RealtimeEnergyMonitor({ className }: RealtimeEnergyMonitorProps) {
  const [data, setData] = useState<EnergyUsageData[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  // 실시간 데이터 시뮬레이션
  useEffect(() => {
    setIsConnected(true)
    
    // 초기 데이터 생성
    const initialData: EnergyUsageData[] = []
    for (let i = 19; i >= 0; i--) {
      const time = new Date(Date.now() - i * 5000)
      initialData.push({
        time: time.toLocaleTimeString(),
        usage: Math.floor(Math.random() * 1000) + 500,
        cost: (Math.random() * 0.5 + 0.2),
        efficiency: Math.floor(Math.random() * 20) + 80
      })
    }
    setData(initialData)
    setLastUpdate(new Date())

    // 실시간 업데이트 (5초마다)
    const interval = setInterval(() => {
      const now = new Date()
      const newPoint: EnergyUsageData = {
        time: now.toLocaleTimeString(),
        usage: Math.floor(Math.random() * 1000) + 500,
        cost: (Math.random() * 0.5 + 0.2),
        efficiency: Math.floor(Math.random() * 20) + 80
      }
      
      setData(prev => {
        const newData = [...prev, newPoint]
        return newData.slice(-20) // 최근 20개 포인트만 유지
      })
      setLastUpdate(now)
    }, 5000)

    return () => {
      clearInterval(interval)
      setIsConnected(false)
    }
  }, [])

  const currentUsage = data[data.length - 1]?.usage || 0
  const previousUsage = data[data.length - 2]?.usage || 0
  const usageTrend = currentUsage - previousUsage
  const currentCost = data[data.length - 1]?.cost || 0
  const averageEfficiency = data.length > 0 
    ? data.reduce((sum, item) => sum + item.efficiency, 0) / data.length 
    : 0

  const refreshData = () => {
    setLastUpdate(new Date())
    // 실제 구현에서는 WebSocket 재연결 또는 API 호출
  }

  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-semibold flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-500" />
          실시간 에너지 모니터링
        </CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant={isConnected ? 'default' : 'secondary'} className="gap-1">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
            {isConnected ? '연결됨' : '연결 끊김'}
          </Badge>
          <Button variant="outline" size="sm" onClick={refreshData}>
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 현재 상태 요약 */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">현재 사용량</p>
            <div className="flex items-center gap-1">
              <span className="text-2xl font-bold">{formatNumber(currentUsage)}</span>
              <span className="text-xs text-muted-foreground">에너지/시간</span>
            </div>
            <div className="flex items-center gap-1 text-xs">
              {usageTrend > 0 ? (
                <>
                  <TrendingUp className="w-3 h-3 text-red-500" />
                  <span className="text-red-500">+{formatNumber(usageTrend)}</span>
                </>
              ) : (
                <>
                  <TrendingDown className="w-3 h-3 text-green-500" />
                  <span className="text-green-500">{formatNumber(usageTrend)}</span>
                </>
              )}
            </div>
          </div>
          
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">현재 비용</p>
            <div className="flex items-center gap-1">
              <span className="text-2xl font-bold">{formatCurrency(currentCost)}</span>
              <span className="text-xs text-muted-foreground">TRX/시간</span>
            </div>
          </div>
          
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">평균 효율성</p>
            <div className="flex items-center gap-1">
              <span className="text-2xl font-bold">{averageEfficiency.toFixed(1)}%</span>
            </div>
            <div className="text-xs text-muted-foreground">
              지난 {data.length}개 데이터 포인트
            </div>
          </div>
        </div>
        
        {/* 실시간 차트 */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <h4 className="text-sm font-medium">에너지 사용량 추이</h4>
            <span className="text-xs text-muted-foreground">
              마지막 업데이트: {lastUpdate.toLocaleTimeString()}
            </span>
          </div>
          
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="usageGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="time" 
                  tick={{ fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => formatNumber(value)}
                />
                <Tooltip 
                  formatter={(value: number, name: string) => [
                    formatNumber(value), 
                    name === 'usage' ? '에너지 사용량' : '비용'
                  ]}
                  labelFormatter={(label) => `시간: ${label}`}
                />
                <Area
                  type="monotone"
                  dataKey="usage"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  fill="url(#usageGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* 효율성 차트 */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">효율성 지표</h4>
          <div className="h-32">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <XAxis 
                  dataKey="time" 
                  tick={{ fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis 
                  domain={[70, 100]}
                  tick={{ fontSize: 10 }}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip 
                  formatter={(value: number) => [`${value}%`, '효율성']}
                  labelFormatter={(label) => `시간: ${label}`}
                />
                <Line
                  type="monotone"
                  dataKey="efficiency"
                  stroke="#10B981"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        {/* 알림 및 권장사항 */}
        {currentUsage > 800 && (
          <div className="mt-4 p-3 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-orange-600" />
              <span className="text-sm text-orange-800">
                에너지 사용량이 평소보다 높습니다. 사용 패턴을 확인해보세요.
              </span>
            </div>
          </div>
        )}
        
        {averageEfficiency < 75 && (
          <div className="mt-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-yellow-800">
                효율성이 낮습니다. 에너지 최적화 설정을 검토해보세요.
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default RealtimeEnergyMonitor
