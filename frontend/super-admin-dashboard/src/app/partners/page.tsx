'use client';

import { useState, useEffect } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import { apiClient } from '@/lib/api';
import { Partner } from '@/types';

export default function PartnersPage() {
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPartners();
  }, []);

  const fetchPartners = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 백엔드 API 호출
      const response = await apiClient.getPartners();
      setPartners(response.items || []);
    } catch (err) {
      console.error('Failed to fetch partners:', err);
      setError('파트너 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const headerActions = (
    <Button variant="primary">
      Add Partner
    </Button>
  );

  return (
    <BasePage 
      title="Partners Management"
      description="Manage and monitor all partner accounts and their activities."
      headerActions={headerActions}
    >
      <Section title="Partner List">
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
            <p className="mt-2 text-gray-300">Loading partners...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-300">
                  Error
                </h3>
                <div className="mt-2 text-sm text-red-200">
                  <p>{error}</p>
                </div>
                <div className="mt-3">
                  <button
                    onClick={fetchPartners}
                    className="text-sm bg-red-800/30 text-red-200 px-3 py-1 rounded-md hover:bg-red-800/50"
                  >
                    Retry
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {!loading && !error && partners.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">No partners found.</p>
          </div>
        )}

        {!loading && !error && partners.length > 0 && (
          <div className="overflow-hidden shadow ring-1 ring-gray-700 md:rounded-lg">
            <table className="min-w-full divide-y divide-gray-600">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Partner
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Domain
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-900 divide-y divide-gray-700">
                {partners.map((partner) => (
                  <tr key={partner.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-white">
                          {partner.name}
                        </div>
                        <div className="text-sm text-gray-300">
                          {partner.contact_email}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-100">
                      {partner.domain}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        partner.status === 'active' 
                          ? 'bg-green-900/30 text-green-300'
                          : 'bg-red-900/30 text-red-300'
                      }`}>
                        {partner.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {new Date(partner.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button className="text-blue-400 hover:text-blue-300 mr-3">
                        Edit
                      </button>
                      <button className="text-red-400 hover:text-red-300">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </BasePage>
  );
}
