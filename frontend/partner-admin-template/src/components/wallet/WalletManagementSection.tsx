'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Wallet, 
  Plus, 
  Send, 
  ArrowUpRight,
  ArrowDownLeft,
  Eye,
  Shield
} from 'lucide-react'
import { PageHeader } from '@/components/common/PageHeader'
import { WalletConnection, MultiWalletManager } from './WalletConnection'
import { formatCurrency, formatDate } from '@/lib/utils'

interface WalletBalance {
  symbol: string
  balance: number
  value_usd: number
  value_krw: number
  change_24h: number
}

interface WalletTransaction {
  id: string
  type: 'send' | 'receive' | 'stake'
  amount: number
  currency: string
  from: string
  to: string
  status: 'pending' | 'confirmed' | 'failed'
  timestamp: string
  tx_hash: string
  fee: number
}

interface WalletManagementSectionProps {
  balances: WalletBalance[]
  transactions: WalletTransaction[]
  connectedWallets: Array<{
    id: string
    name: string
    address: string
    balance: number
    status: 'connected' | 'disconnected' | 'error'
  }>
  onRefresh?: () => void
  onAddWallet?: () => void
  onSendTransaction?: () => void
}

export function WalletManagementSection({
  balances,
  transactions,
  connectedWallets,
  onRefresh,
  onAddWallet,
  onSendTransaction
}: WalletManagementSectionProps) {
  const totalBalance = balances.reduce((sum, balance) => sum + balance.value_usd, 0)
  
  const getTransactionIcon = (type: string) => {
    const icons = {
      send: ArrowUpRight,
      receive: ArrowDownLeft,
      stake: Shield
    }
    return icons[type as keyof typeof icons] || ArrowUpRight
  }

  const getStatusColor = (status: string) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    }
    return colors[status as keyof typeof colors] || colors.pending
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="지갑 관리"
        description="TronLink 지갑 연동 및 자산 관리"
        onRefresh={onRefresh}
      >
        <div className="flex gap-3">
          <Button variant="outline" className="flex items-center gap-2" onClick={onAddWallet}>
            <Plus className="w-4 h-4" />
            지갑 추가
          </Button>
          <Button className="flex items-center gap-2" onClick={onSendTransaction}>
            <Send className="w-4 h-4" />
            전송
          </Button>
        </div>
      </PageHeader>

      {/* 지갑 요약 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">총 자산 가치</p>
                <p className="text-2xl font-bold text-blue-600">
                  ${totalBalance.toLocaleString()}
                </p>
                <p className="text-xs text-gray-500">USD</p>
              </div>
              <Wallet className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">연결된 지갑</p>
                <p className="text-2xl font-bold text-green-600">
                  {connectedWallets.filter(w => w.status === 'connected').length}
                </p>
                <p className="text-xs text-gray-500">개</p>
              </div>
              <Shield className="w-8 h-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">오늘 거래</p>
                <p className="text-2xl font-bold text-purple-600">
                  {transactions.filter(t => {
                    const today = new Date().toISOString().split('T')[0]
                    return t.timestamp.split('T')[0] === today
                  }).length}
                </p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <Send className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">대기 중 거래</p>
                <p className="text-2xl font-bold text-orange-600">
                  {transactions.filter(t => t.status === 'pending').length}
                </p>
                <p className="text-xs text-gray-500">건</p>
              </div>
              <Eye className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="balances">잔액</TabsTrigger>
          <TabsTrigger value="transactions">거래내역</TabsTrigger>
          <TabsTrigger value="management">지갑 관리</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <WalletConnection />
            
            <Card>
              <CardHeader>
                <CardTitle>최근 거래</CardTitle>
                <CardDescription>최근 5건의 거래 내역</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {transactions.slice(0, 5).map((transaction) => {
                    const TransactionIcon = getTransactionIcon(transaction.type)
                    return (
                      <div key={transaction.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                        <div className="flex items-center gap-3">
                          <TransactionIcon className="w-5 h-5 text-gray-600" />
                          <div>
                            <div className="font-medium">
                              {transaction.type === 'send' ? '전송' :
                               transaction.type === 'receive' ? '수신' :
                               transaction.type === 'stake' ? '스테이킹' : '에너지'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {formatDate(transaction.timestamp)}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold">
                            {transaction.type === 'send' ? '-' : '+'}
                            {formatCurrency(transaction.amount, transaction.currency)}
                          </div>
                          <Badge className={getStatusColor(transaction.status)}>
                            {transaction.status === 'pending' ? '대기' :
                             transaction.status === 'confirmed' ? '완료' : '실패'}
                          </Badge>
                        </div>
                      </div>
                    )
                  })}
                </div>
                <Button variant="outline" className="w-full mt-4">
                  모든 거래 내역 보기
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="balances" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>자산 잔액</CardTitle>
              <CardDescription>보유 중인 모든 토큰 및 자산</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {balances.map((balance) => (
                  <div key={balance.symbol} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="font-bold text-blue-600">{balance.symbol[0]}</span>
                      </div>
                      <div>
                        <div className="font-medium">{balance.symbol}</div>
                        <div className="text-sm text-gray-500">
                          ${balance.value_usd.toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">
                        {balance.balance.toLocaleString()}
                      </div>
                      <div className={`text-sm ${balance.change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {balance.change_24h >= 0 ? '+' : ''}{balance.change_24h.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transactions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>거래 내역</CardTitle>
              <CardDescription>모든 거래 내역 및 상태</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        유형
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        금액
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        주소
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        상태
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        시간
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        액션
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {transactions.map((transaction) => {
                      const TransactionIcon = getTransactionIcon(transaction.type)
                      return (
                        <tr key={transaction.id} className="hover:bg-gray-50">
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-2">
                              <TransactionIcon className="w-4 h-4 text-gray-600" />
                              <span className="text-sm">
                                {transaction.type === 'send' ? '전송' :
                                 transaction.type === 'receive' ? '수신' :
                                 transaction.type === 'stake' ? '스테이킹' : '에너지'}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="text-sm font-medium">
                              {transaction.type === 'send' ? '-' : '+'}
                              {formatCurrency(transaction.amount, transaction.currency)}
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <div className="text-sm text-gray-900">
                              {transaction.type === 'send' ? transaction.to : transaction.from}
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <Badge className={getStatusColor(transaction.status)}>
                              {transaction.status === 'pending' ? '대기' :
                               transaction.status === 'confirmed' ? '완료' : '실패'}
                            </Badge>
                          </td>
                          <td className="px-4 py-4">
                            <div className="text-sm text-gray-900">
                              {formatDate(transaction.timestamp)}
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <Button size="sm" variant="outline">
                              <Eye className="w-3 h-3 mr-1" />
                              보기
                            </Button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="management" className="space-y-6">
          <MultiWalletManager wallets={connectedWallets} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
