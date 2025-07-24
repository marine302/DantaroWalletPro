'use client'

import { useState } from 'react'
import { Sidebar } from '@/components/layout/Sidebar'
import { WalletManagementSection } from '@/components/wallet/WalletManagementSection'

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

export default function WalletPage() {
  const [balances] = useState<WalletBalance[]>([
    {
      symbol: 'TRX',
      balance: 15420.50,
      value_usd: 1234.56,
      value_krw: 1654320,
      change_24h: 2.34
    },
    {
      symbol: 'USDT',
      balance: 5000.00,
      value_usd: 5000.00,
      value_krw: 6700000,
      change_24h: -0.12
    },
    {
      symbol: 'BTT',
      balance: 1000000,
      value_usd: 890.45,
      value_krw: 1192000,
      change_24h: 5.67
    }
  ])

  const [transactions] = useState<WalletTransaction[]>([
    {
      id: '1',
      type: 'receive',
      amount: 1000,
      currency: 'TRX',
      from: 'TQn9Y2khEsLMG73Vo9s6VPKcgGWiKDJZjn',
      to: 'TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH',
      status: 'confirmed',
      timestamp: '2024-07-20T10:30:00Z',
      tx_hash: '0x1234567890abcdef',
      fee: 1.05
    },
    {
      id: '2',
      type: 'send',
      amount: 500,
      currency: 'TRX',
      from: 'TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH',
      to: 'TQn9Y2khEsLMG73Vo9s6VPKcgGWiKDJZjn',
      status: 'pending',
      timestamp: '2024-07-20T09:15:00Z',
      tx_hash: '0xabcdef1234567890',
      fee: 1.05
    },
    {
      id: '4',
      type: 'stake',
      amount: 1000,
      currency: 'TRX',
      from: 'TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH',
      to: 'Staking Pool',
      status: 'confirmed',
      timestamp: '2024-07-19T14:20:00Z',
      tx_hash: '0xdef1234567890abc',
      fee: 2.1
    }
  ])

  const [connectedWallets] = useState([
    {
      id: '1',
      name: 'Main Wallet',
      address: 'TLyqzVGLV1srkB7dToTAEqgDSfPtXRJZYH',
      balance: 15420.50,
      status: 'connected' as const
    },
    {
      id: '2',
      name: 'Secondary Wallet',
      address: 'TQn9Y2khEsLMG73Vo9s6VPKcgGWiKDJZjn',
      balance: 8932.15,
      status: 'connected' as const
    },
    {
      id: '3',
      name: 'Cold Storage',
      address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
      balance: 0,
      status: 'disconnected' as const
    }
  ])

  const handleRefresh = () => {
    // TODO: 지갑 데이터 새로고침
    console.log('Refreshing wallet data...')
  }

  const handleAddWallet = () => {
    // TODO: 새 지갑 추가
    console.log('Adding new wallet...')
  }

  const handleSendTransaction = () => {
    // TODO: 거래 전송
    console.log('Sending transaction...')
  }

  return (
    <Sidebar>
      <div className="container mx-auto p-6">
        <WalletManagementSection
          balances={balances}
          transactions={transactions}
          connectedWallets={connectedWallets}
          onRefresh={handleRefresh}
          onAddWallet={handleAddWallet}
          onSendTransaction={handleSendTransaction}
        />
      </div>
    </Sidebar>
  )
}
