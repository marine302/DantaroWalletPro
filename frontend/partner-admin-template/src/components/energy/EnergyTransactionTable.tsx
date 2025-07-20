'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatCurrency, formatDate } from '@/lib/utils'
import { EnergyTransaction } from '@/types'

interface EnergyTransactionTableProps {
  transactions: EnergyTransaction[]
}

export function EnergyTransactionTable({ transactions }: EnergyTransactionTableProps) {
  const getRentalStatusBadge = (status: string) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      completed: 'bg-blue-100 text-blue-800',
      expired: 'bg-gray-100 text-gray-800'
    }
    return variants[status as keyof typeof variants] || variants.active
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>에너지 대여 내역</CardTitle>
        <CardDescription>사용자별 에너지 대여 및 사용 내역</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  사용자
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  에너지 풀
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  수량
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  비용
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  기간
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  시작일
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4">
                    <div className="text-sm font-medium text-gray-900">{transaction.user_name}</div>
                    <div className="text-sm text-gray-500">{transaction.user_id}</div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-900">{transaction.pool_name}</div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {transaction.amount.toLocaleString()} Energy
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm font-medium text-gray-900">
                      {formatCurrency(transaction.total_cost, 'TRX')}
                    </div>
                    <div className="text-sm text-gray-500">
                      @{transaction.price.toFixed(6)} TRX/Unit
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-900">{transaction.duration_hours}시간</div>
                  </td>
                  <td className="px-4 py-4">
                    <Badge className={getRentalStatusBadge(transaction.status)}>
                      {transaction.status === 'active' ? '활성' :
                       transaction.status === 'completed' ? '완료' : '만료'}
                    </Badge>
                  </td>
                  <td className="px-4 py-4">
                    <div className="text-sm text-gray-900">
                      {formatDate(transaction.created_at)}
                    </div>
                    <div className="text-sm text-gray-500">
                      만료: {formatDate(transaction.expires_at)}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
