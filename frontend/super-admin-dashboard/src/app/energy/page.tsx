import { DashboardLayout } from "@/components/layout/DashboardLayout";
import Link from "next/link";

export default function EnergyPage() {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="md:flex md:items-center md:justify-between mb-6">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
              Energy Management
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Monitor and manage energy pools, allocations, and usage across the platform.
            </p>
          </div>
          <div className="mt-4 flex md:ml-4 md:mt-0">
            <button
              type="button"
              className="inline-flex items-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
            >
              Create Energy Pool
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">⚡</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Energy
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">1,250,000 TRX</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">🔋</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Available Energy
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">850,000 TRX</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">📊</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Usage Rate
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">68%</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 외부 에너지 시장 섹션 */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              외부 에너지 시장
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              에너지 부족 시 외부 공급자에서 에너지를 구매하여 서비스 안정성을 확보하세요.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Link href="/energy/external-market">
                <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 text-sm">🏪</span>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-900">시장 모니터링</h4>
                      <p className="text-xs text-gray-500">실시간 가격 및 공급자 현황</p>
                    </div>
                  </div>
                </div>
              </Link>
              
              <Link href="/energy/external-market/purchase">
                <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <span className="text-green-600 text-sm">💰</span>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-900">수동 구매</h4>
                      <p className="text-xs text-gray-500">즉시 에너지 구매</p>
                    </div>
                  </div>
                </div>
              </Link>
              
              <Link href="/energy/auto-purchase">
                <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-purple-600 text-sm">🤖</span>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-900">자동 구매 설정</h4>
                      <p className="text-xs text-gray-500">임계값 및 정책 관리</p>
                    </div>
                  </div>
                </div>
              </Link>
              
              <Link href="/energy/purchase-history">
                <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                      <span className="text-orange-600 text-sm">📊</span>
                    </div>
                    <div className="ml-3">
                      <h4 className="text-sm font-medium text-gray-900">구매 이력</h4>
                      <p className="text-xs text-gray-500">구매 기록 및 통계</p>
                    </div>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Energy Pool Management
            </h3>
            <div className="text-center py-12">
              <p className="text-gray-500">Energy management functionality coming soon...</p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
