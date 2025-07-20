/**
 * StatsCards 컴포넌트 테스트
 */

import { render, screen } from '@testing-library/react'
import { StatsCards } from '@/components/dashboard/StatsCards'

// Mock data
const mockStats = [
  {
    title: 'Total Users',
    value: '1,234',
    change: '+12%',
    trend: 'up' as const,
    icon: 'users'
  },
  {
    title: 'Revenue',
    value: '$45,678',
    change: '+8.5%',
    trend: 'up' as const,
    icon: 'dollar-sign'
  },
  {
    title: 'Transactions',
    value: '5,432',
    change: '-2.3%',
    trend: 'down' as const,
    icon: 'activity'
  }
]

describe('StatsCards', () => {
  it('renders correctly', () => {
    render(<StatsCards stats={mockStats} />)
    
    // 각 stat 카드가 렌더링되는지 확인
    expect(screen.getByText('Total Users')).toBeInTheDocument()
    expect(screen.getByText('1,234')).toBeInTheDocument()
    expect(screen.getByText('+12%')).toBeInTheDocument()
    
    expect(screen.getByText('Revenue')).toBeInTheDocument()
    expect(screen.getByText('$45,678')).toBeInTheDocument()
    expect(screen.getByText('+8.5%')).toBeInTheDocument()
    
    expect(screen.getByText('Transactions')).toBeInTheDocument()
    expect(screen.getByText('5,432')).toBeInTheDocument()
    expect(screen.getByText('-2.3%')).toBeInTheDocument()
  })

  it('applies correct trend colors', () => {
    render(<StatsCards stats={mockStats} />)
    
    // up trend는 green 색상
    const upTrend = screen.getByText('+12%')
    expect(upTrend).toHaveClass('text-green-600')
    
    // down trend는 red 색상
    const downTrend = screen.getByText('-2.3%')
    expect(downTrend).toHaveClass('text-red-600')
  })

  it('renders with empty stats array', () => {
    render(<StatsCards stats={[]} />)
    
    // 빈 상태가 적절히 처리되는지 확인
    const container = screen.getByRole('group')
    expect(container).toBeInTheDocument()
    expect(container.children).toHaveLength(0)
  })

  it('handles loading state', () => {
    render(<StatsCards stats={mockStats} loading={true} />)
    
    // 로딩 상태의 skeleton이 렌더링되는지 확인
    const skeletons = screen.getAllByTestId('stat-skeleton')
    expect(skeletons).toHaveLength(3)
  })

  it('applies custom className', () => {
    render(<StatsCards stats={mockStats} className="custom-class" />)
    
    const container = screen.getByRole('group')
    expect(container).toHaveClass('custom-class')
  })
})
