import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function FeesPage() {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="md:flex md:items-center md:justify-between mb-6">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
              Fee Management
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Configure and monitor transaction fees, partner commissions, and revenue sharing.
            </p>
          </div>
          <div className="mt-4 flex md:ml-4 md:mt-0">
            <button
              type="button"
              className="inline-flex items-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
            >
              Update Fee Structure
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Current Fee Structure
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Transaction Fee</span>
                  <span className="text-sm font-medium text-gray-900">2.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Partner Commission</span>
                  <span className="text-sm font-medium text-gray-900">1.5%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Platform Fee</span>
                  <span className="text-sm font-medium text-gray-900">1.0%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Energy Fee</span>
                  <span className="text-sm font-medium text-gray-900">0.1 TRX</span>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Revenue Summary
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Today&apos;s Revenue</span>
                  <span className="text-sm font-medium text-green-600">$2,345.67</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">This Month</span>
                  <span className="text-sm font-medium text-green-600">$56,789.12</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Partner Commissions</span>
                  <span className="text-sm font-medium text-blue-600">$34,073.47</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Net Profit</span>
                  <span className="text-sm font-medium text-gray-900">$22,715.65</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Fee Configuration
            </h3>
            <div className="text-center py-12">
              <p className="text-gray-500">Fee management interface coming soon...</p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
