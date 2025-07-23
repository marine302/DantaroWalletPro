'use client';

import BasePage from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import { useI18n } from '@/contexts/I18nContext';

export default function AnalyticsPage() {
  const { t } = useI18n();

  const _headerActions = (
    <Button variant="primary">
      {t.analytics.downloadReport}
    </Button>
  );

  return (
    <BasePage
      title={t.analytics.title}
      description={t.analytics.description}
      headerActions={headerActions}
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
        <StatCard
          title="Daily Transactions"
          value="2,847"
          icon="📈"
          trend="up"
          description="+12% from yesterday"
        />
        <StatCard
          title="Revenue Today"
          value="$45,230"
          icon="💰"
          trend="up"
          description="+8% from yesterday"
        />
        <StatCard
          title="Active Partners"
          value="156"
          icon="👥"
          trend="neutral"
          description="No change"
        />
        <StatCard
          title="System Health"
          value="99.8%"
          icon="⚡"
          trend="up"
          description="All systems operational"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Section title="Performance Metrics">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Average Transaction Time</span>
              <span className="text-white font-medium">2.3s</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Success Rate</span>
              <span className="text-green-400 font-medium">99.2%</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Peak Daily Volume</span>
              <span className="text-white font-medium">$2.4M</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Energy Efficiency</span>
              <span className="text-blue-400 font-medium">94.7%</span>
            </div>
          </div>
        </Section>

        <Section title="Top Partners by Volume">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <div className="text-white font-medium">CryptoExchange Pro</div>
                <div className="text-gray-400 text-sm">crypto-exchange.com</div>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">$125,430</div>
                <div className="text-green-400 text-sm">+15%</div>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <div className="text-white font-medium">DeFi Platform</div>
                <div className="text-gray-400 text-sm">defi-platform.com</div>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">$98,750</div>
                <div className="text-green-400 text-sm">+8%</div>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <div className="text-white font-medium">Wallet Service</div>
                <div className="text-gray-400 text-sm">wallet-service.com</div>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">$76,420</div>
                <div className="text-red-400 text-sm">-3%</div>
              </div>
            </div>
          </div>
        </Section>
      </div>

      <Section title="Recent Activity">
        <div className="overflow-hidden shadow ring-1 ring-gray-700 rounded-lg">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Event
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Partner
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Time
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-900 divide-y divide-gray-700">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">Transaction</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">CryptoExchange Pro</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">$1,234.50</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    Success
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">2 min ago</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">Energy Purchase</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">DeFi Platform</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">50,000 TRX</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-blue-900/30 text-blue-300 rounded-full">
                    Processing
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">5 min ago</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">Withdrawal</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">Wallet Service</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">$2,567.80</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    Completed
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">8 min ago</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
    </BasePage>
  );
}
