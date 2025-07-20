'use client';

import { useState, useEffect } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import { apiClient } from '@/lib/api';
import { Partner } from '@/types';
import { useTranslation } from '@/contexts/I18nContext';
import { withRBAC } from '@/components/auth/withRBAC';
import { PermissionGuard } from '@/components/auth/PermissionGuard';

function PartnersPage() {
  const { t } = useTranslation();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPartners();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchPartners = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 임시 목 데이터 (백엔드 연동 전까지)
      const mockPartners: Partner[] = [
        {
          id: 1,
          name: "DantaroExchange",
          slug: "dantaro-exchange",
          domain: "dantaro.exchange",
          api_key: "api_key_1234",
          contact_email: "admin@dantaro.exchange",
          status: "active",
          created_at: "2025-01-15T10:30:00Z",
          updated_at: "2025-07-17T14:22:00Z",
        },
        {
          id: 2,
          name: "CryptoLink Korea",
          slug: "cryptolink-korea",
          domain: "cryptolink.kr",
          api_key: "api_key_5678",
          contact_email: "support@cryptolink.kr",
          status: "active",
          created_at: "2025-02-20T09:15:00Z",
          updated_at: "2025-07-17T12:45:00Z",
        },
        {
          id: 3,
          name: "TronWallet Pro",
          slug: "tronwallet-pro",
          domain: "tronwallet.pro",
          api_key: "api_key_9012",
          contact_email: "info@tronwallet.pro",
          status: "inactive",
          created_at: "2025-07-10T16:20:00Z",
          updated_at: "2025-07-16T18:30:00Z",
        }
      ];
      
      // 실제 API 호출 시도, 실패하면 목 데이터 사용
      try {
        const response = await apiClient.getPartners();
        setPartners(response.items || mockPartners);
      } catch (apiErr) {
        console.warn('API failed, using mock data:', apiErr);
        setPartners(mockPartners);
      }
    } catch (err) {
      console.error('Failed to fetch partners:', err);
      setError(t.partners.failedToLoad);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPartner = () => {
    alert('파트너 추가 모달을 여기에 구현할 예정입니다.');
  };

  const headerActions = (
    <Button variant="primary" onClick={handleAddPartner}>
      {t.partners.addPartner}
    </Button>
  );

  return (
    <BasePage 
      title={t.partners.title}
      description={t.partners.description}
      headerActions={headerActions}
    >
      <Section title={t.partners.partnerList}>
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto"></div>
            <p className="mt-2 text-gray-300">{t.partners.loadingPartners}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-800 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-300">
                  {t.common.error}
                </h3>
                <div className="mt-2 text-sm text-red-200">
                  <p>{error}</p>
                </div>
                <div className="mt-3">
                  <button
                    onClick={fetchPartners}
                    className="text-sm bg-red-800/30 text-red-200 px-3 py-1 rounded-md hover:bg-red-800/50"
                  >
                    {t.common.retry}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {!loading && !error && partners.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-400">{t.partners.noPartnersFound}</p>
          </div>
        )}

        {!loading && !error && partners.length > 0 && (
          <div className="overflow-hidden shadow ring-1 ring-gray-700 md:rounded-lg">
            <table className="min-w-full divide-y divide-gray-600">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    {t.partners.partner}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    {t.common.domain}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    {t.common.status}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    {t.common.created}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    {t.common.actions}
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
                          : partner.status === 'inactive'
                          ? 'bg-red-900/30 text-red-300'
                          : 'bg-yellow-900/30 text-yellow-300'
                      }`}>
                        {partner.status === 'active' ? t.partners.active : 
                         partner.status === 'inactive' ? t.partners.suspended :
                         t.partners.pending}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                      {new Date(partner.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <PermissionGuard permission="partners.edit">
                        <button className="text-blue-400 hover:text-blue-300 mr-3">
                          {t.common.edit}
                        </button>
                      </PermissionGuard>
                      <PermissionGuard permission="partners.delete">
                        <button className="text-red-400 hover:text-red-300">
                          {t.common.delete}
                        </button>
                      </PermissionGuard>
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

// Export protected component
export default withRBAC(PartnersPage, { 
  requiredPermissions: ['partners.view']
});
