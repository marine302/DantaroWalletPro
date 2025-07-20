'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Settings, CheckCircle, Timer, AlertTriangle } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { EnergyPoolInfo } from '@/types'

interface EnergyPoolCardProps {
  pool: EnergyPoolInfo
}

export function EnergyPoolCard({ pool }: EnergyPoolCardProps) {
  const getStatusBadge = (status: string) => {
    const variants = {
      active: { class: 'bg-green-100 text-green-800', icon: CheckCircle, text: '활성' },
      maintenance: { class: 'bg-yellow-100 text-yellow-800', icon: Timer, text: '점검중' },
      depleted: { class: 'bg-red-100 text-red-800', icon: AlertTriangle, text: '고갈' }
    }
    return variants[status as keyof typeof variants] || variants.active
  }

  const status = getStatusBadge(pool.status)
  const StatusIcon = status.icon
  const utilizationRate = (pool.used_capacity / pool.total_capacity) * 100

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-semibold text-lg text-gray-900">{pool.name}</h3>
            <p className="text-sm text-gray-500">ID: {pool.id}</p>
          </div>
          <Badge className={status.class}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {status.text}
          </Badge>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">이용률</span>
              <span className="font-medium">{utilizationRate.toFixed(1)}%</span>
            </div>
            <Progress value={utilizationRate} className="h-2" />
          </div>

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-gray-600">총 용량</p>
              <p className="font-medium">{pool.total_capacity.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600">사용 중</p>
              <p className="font-medium text-red-600">{pool.used_capacity.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600">사용 가능</p>
              <p className="font-medium text-green-600">{pool.available_capacity.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-gray-600">단가</p>
              <p className="font-medium">{pool.price_per_unit.toFixed(6)} TRX</p>
            </div>
          </div>

          <div className="border-t pt-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-600">대여 건수: {pool.rental_count}건</span>
              <span className="font-medium text-blue-600">
                수익: {formatCurrency(pool.revenue, 'TRX')}
              </span>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button size="sm" variant="outline" className="flex-1">
              <Settings className="w-3 h-3 mr-1" />
              설정
            </Button>
            <Button size="sm" className="flex-1">
              상세보기
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
