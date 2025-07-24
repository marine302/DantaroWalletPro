'use client';

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

// 타입 정의
interface ChartData {
  date: string;
  transactions: number;
  volume: number;
  revenue: number;
}

interface WalletDistributionData {
  type: string;
  value: number;
  percentage: number;
  color: string;
}

interface TransactionTrendChartProps {
  data: ChartData[];
  height?: number;
}

interface WalletDistributionChartProps {
  data: WalletDistributionData[];
  height?: number;
}

interface RevenueChartProps {
  data: ChartData[];
  height?: number;
}

// 거래량 트렌드 차트
export function TransactionTrendChart({ data, height = 300 }: TransactionTrendChartProps) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9CA3AF"
            fontSize={12}
          />
          <YAxis stroke="#9CA3AF" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F3F4F6'
            }}
          />
          <Line
            type="monotone"
            dataKey="transactions"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// 거래량 영역 차트
export function VolumeAreaChart({ data, height = 300 }: TransactionTrendChartProps) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9CA3AF"
            fontSize={12}
          />
          <YAxis stroke="#9CA3AF" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F3F4F6'
            }}
          />
          <Area
            type="monotone"
            dataKey="volume"
            stroke="#10B981"
            fill="#10B981"
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// 지갑 분산 파이 차트
export function WalletDistributionChart({ data, height = 300 }: WalletDistributionChartProps) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ type, percentage }) => `${type}: ${percentage}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F3F4F6'
            }}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// 수익 바 차트
export function RevenueBarChart({ data, height = 300 }: RevenueChartProps) {
  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9CA3AF"
            fontSize={12}
          />
          <YAxis stroke="#9CA3AF" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#F3F4F6'
            }}
          />
          <Bar
            dataKey="revenue"
            fill="#8B5CF6"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// 차트 데이터 생성 함수들
export function generateTransactionTrendData(): ChartData[] {
  const _days = 7;
  const data: ChartData[] = [];

  for (let _i = 0; _i < _days; _i++) {
    const _date = new Date();
    _date.setDate(_date.getDate() - (_days - 1 - _i));

    data.push({
      date: _date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }),
      transactions: Math.floor(Math.random() * 500) + 300,
      volume: Math.floor(Math.random() * 1000000) + 500000,
      revenue: Math.floor(Math.random() * 50000) + 25000
    });
  }

  return data;
}

export function generateWalletDistributionData(): WalletDistributionData[] {
  return [
    { type: 'Hot Wallet', value: 40, percentage: 40, color: '#EF4444' },
    { type: 'Warm Wallet', value: 35, percentage: 35, color: '#F59E0B' },
    { type: 'Cold Wallet', value: 25, percentage: 25, color: '#3B82F6' }
  ];
}
