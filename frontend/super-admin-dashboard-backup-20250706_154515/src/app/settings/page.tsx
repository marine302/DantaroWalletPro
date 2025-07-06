import { DashboardLayout } from "@/components/layout/DashboardLayout";

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        <div className="md:flex md:items-center md:justify-between mb-6">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
              System Settings
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Configure global system settings, security policies, and platform parameters.
            </p>
          </div>
          <div className="mt-4 flex md:ml-4 md:mt-0">
            <button
              type="button"
              className="inline-flex items-center rounded-md bg-gray-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600"
            >
              Save Settings
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Platform Configuration
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="platform-name" className="block text-sm font-medium text-gray-700">
                    Platform Name
                  </label>
                  <input
                    type="text"
                    name="platform-name"
                    id="platform-name"
                    defaultValue="DantaroWallet"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="platform-version" className="block text-sm font-medium text-gray-700">
                    Platform Version
                  </label>
                  <input
                    type="text"
                    name="platform-version"
                    id="platform-version"
                    defaultValue="v2.1.0"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Security Settings
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Two-Factor Authentication</h4>
                    <p className="text-sm text-gray-500">Require 2FA for all admin accounts</p>
                  </div>
                  <button
                    type="button"
                    className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-green-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                    role="switch"
                    aria-checked="true"
                  >
                    <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
                  </button>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Session Timeout</h4>
                    <p className="text-sm text-gray-500">Automatic logout after inactivity</p>
                  </div>
                  <select className="rounded-md border-gray-300 text-sm focus:border-indigo-500 focus:ring-indigo-500">
                    <option>15 minutes</option>
                    <option>30 minutes</option>
                    <option selected>1 hour</option>
                    <option>2 hours</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Blockchain Settings
              </h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="tron-network" className="block text-sm font-medium text-gray-700">
                    TRON Network
                  </label>
                  <select
                    id="tron-network"
                    name="tron-network"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  >
                    <option>Mainnet</option>
                    <option>Testnet (Shasta)</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="energy-threshold" className="block text-sm font-medium text-gray-700">
                    Energy Threshold (TRX)
                  </label>
                  <input
                    type="number"
                    name="energy-threshold"
                    id="energy-threshold"
                    defaultValue="1000"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Notification Settings
              </h3>
              <div className="text-center py-8">
                <p className="text-gray-500">Notification configuration interface coming soon...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
