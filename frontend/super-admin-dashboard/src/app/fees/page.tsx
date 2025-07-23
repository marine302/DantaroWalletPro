'use client';

import BasePage from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
// import { useI18n } from '@/contexts/I18nContext';

export default function FeesPage() {
  const { t } = useI18n();

  const _headerActions = (
    <Button variant="primary">
      {t.fees.updateRates}
    </Button>
  );

  return (
    <BasePage
      title={t.fees.title}
      description={t.fees.description}
      headerActions={headerActions}
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
        <StatCard
          title={t.fees.totalRevenue}
          value="$12,430"
          icon="💰"
          trend="up"
          description="+15% from yesterday"
        />
        <StatCard
          title="Total Fees Collected"
          value="$234,567"
          icon="📊"
          trend="up"
          description="This month"
        />
        <StatCard
          title={t.fees.partnerCommission}
          value="$87,432"
          icon="🤝"
          trend="up"
          description="This month"
        />
        <StatCard
          title="Platform Revenue"
          value="$147,135"
          icon="🏦"
          trend="up"
          description="This month"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Section title="Current Fee Structure">
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-gray-800 rounded-lg">
              <span className="text-gray-300">Transaction Fee</span>
              <span className="text-white font-medium">2.5%</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-800 rounded-lg">
              <span className="text-gray-300">Partner Commission</span>
              <span className="text-white font-medium">1.5%</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-800 rounded-lg">
              <span className="text-gray-300">Platform Fee</span>
              <span className="text-white font-medium">1.0%</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-800 rounded-lg">
              <span className="text-gray-300">Energy Fee</span>
              <span className="text-white font-medium">0.1 TRX</span>
            </div>
          </div>
        </Section>

        <Section title="Fee Configuration">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Base Transaction Fee (%)
              </label>
              <input
                type="number"
                value="2.5"
                step="0.1"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Partner Commission Rate (%)
              </label>
              <input
                type="number"
                value="1.5"
                step="0.1"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Energy Fee (TRX)
              </label>
              <input
                type="number"
                value="0.1"
                step="0.01"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <Button variant="primary" className="w-full">
              Save Configuration
            </Button>
          </div>
        </Section>
      </div>

      <Section title="Fee Analytics">
        <div className="overflow-hidden shadow ring-1 ring-gray-700 rounded-lg">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Partner
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Transaction Volume
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Fees Collected
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Commission Paid
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Net Revenue
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-900 divide-y divide-gray-700">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                  CryptoExchange Pro
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $284,729
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $7,118
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $4,271
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400">
                  $2,847
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                  DeFi Platform
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $154,783
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $3,870
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $2,322
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400">
                  $1,548
                </td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                  Wallet Service
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $84,563
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $2,114
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                  $1,268
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-400">
                  $846
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
    </BasePage>
  );
}
