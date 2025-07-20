'use client'

import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Zap, Activity, Users, DollarSign, Loader2 } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { EnergyStats as EnergyStatsType } from '@/types'

interface EnergyStatsProps {
  stats: EnergyStatsType
  loading?: boolean
}

export function EnergyStats({ stats, loading = false }: EnergyStatsProps) {
  const LoadingIcon = () => (
    <Loader2 className="w-6 h-6 animate-spin" />
  )

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">총 에너지 용량</p>
              <p className="text-2xl font-bold text-blue-600">
                {loading ? <LoadingIcon /> : stats.total_capacity.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">Energy Units</p>
            </div>
            <Zap className="w-8 h-8 text-blue-600" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">이용률</p>
              <p className="text-2xl font-bold text-purple-600">
                {loading ? <LoadingIcon /> : `${stats.utilization_rate.toFixed(1)}%`}
              </p>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${stats.utilization_rate}%` }}
                />
              </div>
            </div>
            <Activity className="w-8 h-8 text-purple-600" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">활성 대여</p>
              <p className="text-2xl font-bold text-green-600">
                {loading ? <LoadingIcon /> : stats.active_rentals.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">건</p>
            </div>
            <Users className="w-8 h-8 text-green-600" />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">총 수익</p>
              <p className="text-2xl font-bold text-orange-600">
                {loading ? <LoadingIcon /> : formatCurrency(stats.total_revenue, 'TRX')}
              </p>
              <p className="text-xs text-gray-500">
                평균 {loading ? '...' : stats.avg_price_per_unit.toFixed(6)} TRX/Unit
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-orange-600" />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
