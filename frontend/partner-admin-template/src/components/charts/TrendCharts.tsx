'use client'

import React from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

// 트렌드 차트용 데이터 타입
interface TrendData {
  date: string
  revenue: number
  cost: number
  profit: number
  users: number
  transactions: number
}

// 트렌드 차트 컴포넌트
interface TrendChartProps {
  data: TrendData[]
  period: string
}

export const RevenueTrendChart: React.FC<TrendChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis 
          dataKey="date" 
          className="text-gray-600 dark:text-gray-300"
          fontSize={12}
        />
        <YAxis 
          className="text-gray-600 dark:text-gray-300"
          fontSize={12}
          tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'rgb(255 255 255)',
            border: '1px solid rgb(229 231 235)',
            borderRadius: '8px',
            fontSize: '14px'
          }}
          formatter={(value: number, name: string) => [
            `${value.toLocaleString()} TRX`,
            name === 'revenue' ? '수익' : name === 'cost' ? '비용' : '순이익'
          ]}
          labelFormatter={(label) => `날짜: ${label}`}
        />
        <Area 
          type="monotone" 
          dataKey="revenue" 
          stackId="1"
          stroke="#10b981" 
          fill="#10b981" 
          fillOpacity={0.3}
        />
        <Area 
          type="monotone" 
          dataKey="cost" 
          stackId="2"
          stroke="#ef4444" 
          fill="#ef4444" 
          fillOpacity={0.3}
        />
        <Line 
          type="monotone" 
          dataKey="profit" 
          stroke="#3b82f6" 
          strokeWidth={2}
          dot={{ fill: '#3b82f6', strokeWidth: 2, r: 3 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export const UserGrowthChart: React.FC<TrendChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis 
          dataKey="date" 
          className="text-gray-600 dark:text-gray-300"
          fontSize={12}
        />
        <YAxis 
          className="text-gray-600 dark:text-gray-300"
          fontSize={12}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'rgb(255 255 255)',
            border: '1px solid rgb(229 231 235)',
            borderRadius: '8px',
            fontSize: '14px'
          }}
          formatter={(value: number) => [`${value.toLocaleString()}명`, '사용자 수']}
          labelFormatter={(label) => `날짜: ${label}`}
        />
        <Line 
          type="monotone" 
          dataKey="users" 
          stroke="#8b5cf6" 
          strokeWidth={3}
          dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#8b5cf6', strokeWidth: 2, fill: '#ffffff' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export const TransactionVolumeChart: React.FC<TrendChartProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
        <XAxis 
          dataKey="date" 
          className="text-gray-600 dark:text-gray-300"
          fontSize={12}
        />
        <YAxis 
          className="text-gray-600 dark:text-gray-300"
          fontSize={12}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'rgb(255 255 255)',
            border: '1px solid rgb(229 231 235)',
            borderRadius: '8px',
            fontSize: '14px'
          }}
          formatter={(value: number) => [`${value.toLocaleString()}건`, '거래 수']}
          labelFormatter={(label) => `날짜: ${label}`}
        />
        <Bar 
          dataKey="transactions" 
          fill="#f59e0b"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

// 파이차트용 데이터 생성 함수
export const generateBreakdownChart = (
  data: Array<{ name: string; value: number; percentage: number }>,
  colors: string[]
) => {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={80}
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip 
          contentStyle={{
            backgroundColor: 'rgb(255 255 255)',
            border: '1px solid rgb(229 231 235)',
            borderRadius: '8px',
            fontSize: '14px'
          }}
          formatter={(value: number, name: string) => [
            `${value.toLocaleString()} TRX`,
            name
          ]}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

// 샘플 데이터 생성 함수
export const generateSampleTrendData = (period: '7d' | '30d' | '90d' | '1y'): TrendData[] => {
  const days = period === '7d' ? 7 : period === '30d' ? 30 : period === '90d' ? 90 : 365
  const data: TrendData[] = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    
    // 기본값에서 랜덤 변동 추가
    const baseRevenue = 4200
    const baseCost = 2300
    const baseUsers = 42
    const baseTransactions = 280
    
    const revenue = baseRevenue + (Math.random() - 0.5) * 1000
    const cost = baseCost + (Math.random() - 0.5) * 500
    
    data.push({
      date: date.toLocaleDateString('ko-KR', { 
        month: 'short', 
        day: 'numeric' 
      }),
      revenue: Math.round(revenue),
      cost: Math.round(cost),
      profit: Math.round(revenue - cost),
      users: Math.round(baseUsers + (Math.random() - 0.5) * 10),
      transactions: Math.round(baseTransactions + (Math.random() - 0.5) * 50)
    })
  }
  
  return data
}
