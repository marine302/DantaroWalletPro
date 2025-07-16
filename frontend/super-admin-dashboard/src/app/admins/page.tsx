import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';

export default function AdminsPage() {
  const headerActions = (
    <Button variant="primary">
      Add Administrator
    </Button>
  );

  return (
    <BasePage 
      title="System Administrators"
      description="Manage system administrator accounts, roles, and permissions."
      headerActions={headerActions}
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <StatCard
          title="Super Admins"
          value="3"
          icon="👑"
          trend="neutral"
        />
        <StatCard
          title="System Admins"
          value="8"
          icon="🔧"
          trend="up"
        />
        <StatCard
          title="Support Staff"
          value="15"
          icon="🎧"
          trend="up"
        />
      </div>

      <Section title="Administrator List">
        <div className="overflow-hidden shadow ring-1 ring-gray-700 rounded-lg">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Administrator
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Last Login
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-gray-900 divide-y divide-gray-700">
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 bg-red-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-medium">SA</span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-white">Super Admin</div>
                      <div className="text-sm text-gray-300">superadmin@dantaro.com</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-red-900/30 text-red-300 rounded-full">
                    Super Admin
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    Active
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  2 hours ago
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-blue-400 hover:text-blue-300 mr-3">Edit</button>
                  <button className="text-red-400 hover:text-red-300">Disable</button>
                </td>
              </tr>
              
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 bg-blue-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-medium">JD</span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-white">John Doe</div>
                      <div className="text-sm text-gray-300">john.doe@dantaro.com</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-blue-900/30 text-blue-300 rounded-full">
                    System Admin
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    Active
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  5 hours ago
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-blue-400 hover:text-blue-300 mr-3">Edit</button>
                  <button className="text-red-400 hover:text-red-300">Disable</button>
                </td>
              </tr>
              
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 bg-green-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-medium">JS</span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-white">Jane Smith</div>
                      <div className="text-sm text-gray-300">jane.smith@dantaro.com</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    Support Staff
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    Active
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  1 day ago
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-blue-400 hover:text-blue-300 mr-3">Edit</button>
                  <button className="text-red-400 hover:text-red-300">Disable</button>
                </td>
              </tr>
              
              <tr>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 bg-gray-600 rounded-full flex items-center justify-center">
                      <span className="text-white font-medium">MB</span>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-400">Mike Brown</div>
                      <div className="text-sm text-gray-500">mike.brown@dantaro.com</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-blue-900/30 text-blue-300 rounded-full">
                    System Admin
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-gray-700 text-gray-400 rounded-full">
                    Suspended
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  1 week ago
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button className="text-green-400 hover:text-green-300 mr-3">Enable</button>
                  <button className="text-red-400 hover:text-red-300">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Section title="Role Permissions">
          <div className="space-y-4">
            <div className="p-4 bg-gray-800 rounded-lg">
              <h4 className="text-red-300 font-medium mb-2">Super Admin</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Full system access</li>
                <li>• User management</li>
                <li>• System configuration</li>
                <li>• Financial operations</li>
              </ul>
            </div>
            
            <div className="p-4 bg-gray-800 rounded-lg">
              <h4 className="text-blue-300 font-medium mb-2">System Admin</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Partner management</li>
                <li>• Energy management</li>
                <li>• Analytics access</li>
                <li>• Basic configuration</li>
              </ul>
            </div>
            
            <div className="p-4 bg-gray-800 rounded-lg">
              <h4 className="text-green-300 font-medium mb-2">Support Staff</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Read-only access</li>
                <li>• Customer support</li>
                <li>• Basic analytics</li>
                <li>• Ticket management</li>
              </ul>
            </div>
          </div>
        </Section>

        <Section title="Recent Admin Activity">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <div className="text-white text-sm">Partner created</div>
                <div className="text-gray-400 text-xs">by John Doe</div>
              </div>
              <div className="text-gray-300 text-xs">2 hours ago</div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <div className="text-white text-sm">System settings updated</div>
                <div className="text-gray-400 text-xs">by Super Admin</div>
              </div>
              <div className="text-gray-300 text-xs">5 hours ago</div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
              <div>
                <div className="text-white text-sm">User suspended</div>
                <div className="text-gray-400 text-xs">by Jane Smith</div>
              </div>
              <div className="text-gray-300 text-xs">1 day ago</div>
            </div>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
