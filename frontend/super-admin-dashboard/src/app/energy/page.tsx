import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import Link from "next/link";

export default function EnergyPage() {
  const headerActions = (
    <Button variant="primary">
      Create Energy Pool
    </Button>
  );

  return (
    <BasePage 
      title="Energy Management"
      description="Monitor and manage energy pools, allocations, and usage across the platform."
      headerActions={headerActions}
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <StatCard
          title="Total Energy"
          value="1,250,000 TRX"
          icon="⚡"
          trend="up"
        />
        <StatCard
          title="Available Energy"
          value="890,500 TRX"
          icon="🔋"
          trend="neutral"
        />
        <StatCard
          title="Daily Usage"
          value="45,200 TRX"
          icon="📊"
          trend="down"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Section title="Quick Actions">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link
              href="/energy/auto-purchase"
              className="block p-4 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              <div className="text-blue-400 text-2xl mb-2">🤖</div>
              <h3 className="text-lg font-medium text-white mb-1">Auto Purchase</h3>
              <p className="text-gray-300 text-sm">Configure automatic energy purchasing</p>
            </Link>

            <Link
              href="/energy/external-market"
              className="block p-4 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              <div className="text-green-400 text-2xl mb-2">🏪</div>
              <h3 className="text-lg font-medium text-white mb-1">External Market</h3>
              <p className="text-gray-300 text-sm">Buy energy from external sources</p>
            </Link>

            <Link
              href="/energy/purchase-history"
              className="block p-4 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors"
            >
              <div className="text-purple-400 text-2xl mb-2">📈</div>
              <h3 className="text-lg font-medium text-white mb-1">Purchase History</h3>
              <p className="text-gray-300 text-sm">View all energy transactions</p>
            </Link>

            <div className="block p-4 rounded-lg bg-gray-800 hover:bg-gray-700 transition-colors cursor-pointer">
              <div className="text-orange-400 text-2xl mb-2">⚙️</div>
              <h3 className="text-lg font-medium text-white mb-1">Energy Settings</h3>
              <p className="text-gray-300 text-sm">Configure energy policies</p>
            </div>
          </div>
        </Section>

        <Section title="Energy Pools">
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div>
                <h4 className="text-white font-medium">Main Pool</h4>
                <p className="text-gray-300 text-sm">850,000 TRX available</p>
              </div>
              <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                Active
              </span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div>
                <h4 className="text-white font-medium">Emergency Pool</h4>
                <p className="text-gray-300 text-sm">40,500 TRX available</p>
              </div>
              <span className="px-2 py-1 text-xs bg-blue-900/30 text-blue-300 rounded-full">
                Reserve
              </span>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
              <div>
                <h4 className="text-white font-medium">Partner Pool</h4>
                <p className="text-gray-300 text-sm">0 TRX available</p>
              </div>
              <span className="px-2 py-1 text-xs bg-red-900/30 text-red-300 rounded-full">
                Empty
              </span>
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
                  Action
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Pool
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-900 divide-y divide-gray-700">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">Auto Purchase</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">+50,000 TRX</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">Main Pool</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">2 hours ago</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">Manual Transfer</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">-15,000 TRX</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">Emergency Pool</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">5 hours ago</td>
              </tr>
              <tr>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-white">Pool Creation</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">+100,000 TRX</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">Partner Pool</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">1 day ago</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>
    </BasePage>
  );
}
