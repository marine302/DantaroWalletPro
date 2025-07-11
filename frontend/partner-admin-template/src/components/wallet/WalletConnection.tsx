'use client'

import { useState } from 'react'
import { Wallet, ExternalLink, Copy, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useTronWallet } from '@/contexts/TronWalletContext'
import { formatAddress, formatCurrency } from '@/lib/utils'

export function WalletConnection() {
  const { wallet, isConnecting, connect, disconnect, getBalance } = useTronWallet()
  const [copied, setCopied] = useState(false)

  const handleConnect = async () => {
    try {
      await connect()
    } catch (error) {
      console.error('Failed to connect wallet:', error)
    }
  }

  const handleCopyAddress = async () => {
    if (wallet?.address) {
      await navigator.clipboard.writeText(wallet.address)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const handleRefreshBalance = async () => {
    try {
      await getBalance()
    } catch (error) {
      console.error('Failed to refresh balance:', error)
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-5 w-5" />
          TronLink 지갑
        </CardTitle>
        <CardDescription>
          TronLink 지갑을 연결하여 거래를 시작하세요
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!wallet ? (
          <div className="text-center space-y-4">
            <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg">
              <Wallet className="mx-auto h-8 w-8 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">지갑이 연결되지 않음</p>
            </div>
            <Button 
              onClick={handleConnect}
              disabled={isConnecting}
              className="w-full"
            >
              {isConnecting ? '연결 중...' : 'TronLink 연결'}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium text-green-800">연결됨</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-green-600">
                  {wallet.network.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">지갑 주소</span>
                <div className="flex items-center gap-2">
                  <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                    {formatAddress(wallet.address)}
                  </code>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCopyAddress}
                    className="p-1"
                  >
                    {copied ? (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">잔액</span>
                <div className="flex items-center gap-2">
                  <span className="font-semibold">
                    {formatCurrency(wallet.balance)}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleRefreshBalance}
                    className="p-1"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t">
              <Button
                variant="outline"
                onClick={disconnect}
                className="w-full"
              >
                지갑 연결 해제
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

interface MultiWalletManagerProps {
  wallets: Array<{
    id: string
    name: string
    address: string
    balance: number
    status: 'connected' | 'disconnected' | 'error'
  }>
}

export function MultiWalletManager({ wallets }: MultiWalletManagerProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'disconnected':
        return <AlertCircle className="h-4 w-4 text-gray-400" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>다중 지갑 관리</CardTitle>
        <CardDescription>
          여러 지갑을 동시에 관리하고 모니터링하세요
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {wallets.map((wallet) => (
            <div 
              key={wallet.id}
              className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                {getStatusIcon(wallet.status)}
                <div>
                  <div className="font-medium">{wallet.name}</div>
                  <div className="text-sm text-gray-500">
                    {formatAddress(wallet.address)}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">
                  {formatCurrency(wallet.balance)}
                </div>
                <div className="text-sm text-gray-500 capitalize">
                  {wallet.status}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 pt-4 border-t">
          <Button variant="outline" className="w-full">
            새 지갑 추가
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
