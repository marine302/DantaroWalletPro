'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { WalletConnection } from '@/types'

interface TronTransaction {
  to: string
  value: number
  data?: string
}

interface TronWalletContextType {
  wallet: WalletConnection | null
  isConnecting: boolean
  connect: () => Promise<void>
  disconnect: () => void
  signTransaction: (transaction: TronTransaction) => Promise<string>
  getBalance: () => Promise<number>
}

const TronWalletContext = createContext<TronWalletContextType | null>(null)

export function useTronWallet() {
  const context = useContext(TronWalletContext)
  if (!context) {
    throw new Error('useTronWallet must be used within a TronWalletProvider')
  }
  return context
}

interface TronWalletProviderProps {
  children: ReactNode
}

export function TronWalletProvider({ children }: TronWalletProviderProps) {
  const [wallet, setWallet] = useState<WalletConnection | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)

  useEffect(() => {
    // Check if TronLink is available
    const checkTronLink = async () => {
      if (typeof window !== 'undefined' && window.tronWeb) {
        const tronWeb = window.tronWeb
        if (tronWeb.defaultAddress.base58) {
          const address = tronWeb.defaultAddress.base58
          const balance = await getBalance()
          setWallet({
            address,
            connected: true,
            network: 'mainnet',
            balance,
            provider: 'tronlink'
          })
        }
      }
    }

    checkTronLink()
  }, [])

  const connect = async () => {
    if (typeof window === 'undefined' || !window.tronWeb) {
      throw new Error('TronLink is not installed')
    }

    setIsConnecting(true)
    try {
      const tronWeb = window.tronWeb
      
      // Request account access
      await tronWeb.request({ method: 'tron_requestAccounts' })
      
      const address = tronWeb.defaultAddress.base58
      const balance = await getBalance()
      
      setWallet({
        address,
        connected: true,
        network: 'mainnet',
        balance,
        provider: 'tronlink'
      })
    } catch (error) {
      console.error('Failed to connect wallet:', error)
      throw error
    } finally {
      setIsConnecting(false)
    }
  }

  const disconnect = () => {
    setWallet(null)
  }

  const signTransaction = async (transaction: TronTransaction): Promise<string> => {
    if (!wallet || typeof window === 'undefined' || !window.tronWeb) {
      throw new Error('Wallet not connected')
    }

    try {
      const tronWeb = window.tronWeb
      const signedTx = await tronWeb.trx.sign(transaction)
      return signedTx.signature[0]
    } catch (error) {
      console.error('Failed to sign transaction:', error)
      throw error
    }
  }

  const getBalance = async (): Promise<number> => {
    if (typeof window === 'undefined' || !window.tronWeb) {
      return 0
    }

    try {
      const tronWeb = window.tronWeb
      const address = tronWeb.defaultAddress.base58
      const balance = await tronWeb.trx.getBalance(address)
      return balance / 1000000 // Convert from SUN to TRX
    } catch (error) {
      console.error('Failed to get balance:', error)
      return 0
    }
  }

  return (
    <TronWalletContext.Provider
      value={{
        wallet,
        isConnecting,
        connect,
        disconnect,
        signTransaction,
        getBalance
      }}
    >
      {children}
    </TronWalletContext.Provider>
  )
}

// Extend window type for TronWeb
declare global {
  interface Window {
    tronWeb: {
      defaultAddress: {
        base58: string
      }
      trx: {
        sign: (transaction: TronTransaction) => Promise<{ signature: string[] }>
        getBalance: (address: string) => Promise<number>
      }
      request: (params: { method: string }) => Promise<void>
    }
  }
}
