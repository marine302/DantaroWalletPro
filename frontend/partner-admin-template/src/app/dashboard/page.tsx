/**
 * 대시보드 메인 페이지 - 기존 개발된 컴포넌트들 활용
 */

'use client';

import { withAuth } from '../../contexts/AuthContext';
import { Sidebar } from '../../components/layout/Sidebar';
import { StatsCards } from '../../components/dashboard/StatsCards';
import { RealtimeEnergyMonitor } from '../../components/dashboard/RealtimeEnergyMonitor';
import { EnergyRentalWidget } from '../../components/dashboard/EnergyRentalWidget';
import { MOCK_DASHBOARD_STATS } from '../../lib/services/mock.service';

function DashboardPage() {
  return (
    <Sidebar>
      <div className="p-8">
        {/* 페이지 헤더 */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-2">
            Welcome to your partner admin dashboard. Monitor your operations and manage your resources.
          </p>
        </div>

        {/* 통계 카드들 - 기존 개발된 컴포넌트 사용 */}
        <div className="mb-8">
          <StatsCards stats={MOCK_DASHBOARD_STATS} />
        </div>

        {/* 메인 콘텐츠 그리드 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 실시간 에너지 모니터 */}
          <div className="lg:col-span-1">
            <RealtimeEnergyMonitor />
          </div>

          {/* 에너지 렌탈 위젯 */}
          <div className="lg:col-span-1">
            <EnergyRentalWidget />
          </div>
        </div>

        {/* 추가 섹션들 */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 빠른 액션들 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors">
                View All Transactions
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors">
                Manage Users
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors">
                Process Withdrawals
              </button>
              <button className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors">
                Energy Settings
              </button>
            </div>
          </div>

          {/* 최근 활동 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-3">
              <div className="flex items-center text-sm text-gray-600">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-3"></div>
                <span>New user registered</span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
                <span>Withdrawal processed</span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <div className="w-2 h-2 bg-yellow-400 rounded-full mr-3"></div>
                <span>Energy pool updated</span>
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <div className="w-2 h-2 bg-purple-400 rounded-full mr-3"></div>
                <span>System maintenance</span>
              </div>
            </div>
          </div>

          {/* 시스템 상태 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Server</span>
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Online</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Online</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Tron Network</span>
                <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">Synced</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">WebSocket</span>
                <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full">Connecting</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Sidebar>
  );
}

// 인증이 필요한 페이지로 래핑
export default withAuth(DashboardPage);
