'use client';

import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';
import { useI18n } from '@/contexts/I18nContext';

export default function AdminsPage() {
  const { t } = useI18n();
  
  const handleAddAdmin = () => {
    alert('관리자 추가 모달을 여기에 구현할 예정입니다.');
  };

  const handleEditAdmin = (adminName: string) => {
    alert(`${adminName} 편집 모달을 여기에 구현할 예정입니다.`);
  };

  const handleDisableAdmin = (adminName: string) => {
    if (confirm(`${adminName}을(를) 비활성화하시겠습니까?`)) {
      alert(`${adminName}이(가) 비활성화되었습니다.`);
    }
  };

  const handleEnableAdmin = (adminName: string) => {
    if (confirm(`${adminName}을(를) 활성화하시겠습니까?`)) {
      alert(`${adminName}이(가) 활성화되었습니다.`);
    }
  };
  
  const headerActions = (
    <Button variant="primary" onClick={handleAddAdmin}>
      {t.admins.addAdministrator}
    </Button>
  );

  return (
    <BasePage 
      title={t.admins.title}
      description={t.admins.description}
      headerActions={headerActions}
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <StatCard
          title={t.admins.superAdmins}
          value="3"
          icon="👑"
          trend="neutral"
        />
        <StatCard
          title={t.admins.systemAdmins}
          value="8"
          icon="🔧"
          trend="up"
        />
        <StatCard
          title={t.admins.supportStaff}
          value="15"
          icon="🎧"
          trend="up"
        />
      </div>

      <Section title={t.admins.administratorList}>
        <div className="overflow-hidden shadow ring-1 ring-gray-700 rounded-lg">
          <table className="min-w-full divide-y divide-gray-600">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  {t.admins.administrator}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  {t.admins.role}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  {t.common.status}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  {t.admins.lastLogin}
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                  {t.common.actions}
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
                    {t.admins.superAdmins}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    {t.admins.active}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  2시간 전
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button 
                    className="text-blue-400 hover:text-blue-300 mr-3"
                    onClick={() => handleEditAdmin('Super Admin')}
                  >
                    {t.common.edit}
                  </button>
                  <button 
                    className="text-red-400 hover:text-red-300"
                    onClick={() => handleDisableAdmin('Super Admin')}
                  >
                    {t.admins.disable}
                  </button>
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
                    {t.admins.systemAdmins}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    {t.admins.active}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  5시간 전
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button 
                    className="text-blue-400 hover:text-blue-300 mr-3"
                    onClick={() => handleEditAdmin('John Doe')}
                  >
                    {t.common.edit}
                  </button>
                  <button 
                    className="text-red-400 hover:text-red-300"
                    onClick={() => handleDisableAdmin('John Doe')}
                  >
                    {t.admins.disable}
                  </button>
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
                    {t.admins.supportStaff}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-green-900/30 text-green-300 rounded-full">
                    {t.admins.active}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  1일 전
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button 
                    className="text-blue-400 hover:text-blue-300 mr-3"
                    onClick={() => handleEditAdmin('Jane Smith')}
                  >
                    {t.common.edit}
                  </button>
                  <button 
                    className="text-red-400 hover:text-red-300"
                    onClick={() => handleDisableAdmin('Jane Smith')}
                  >
                    {t.admins.disable}
                  </button>
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
                    {t.admins.systemAdmins}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 text-xs bg-gray-700 text-gray-400 rounded-full">
                    {t.admins.suspended}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  3일 전
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button 
                    className="text-green-400 hover:text-green-300 mr-3"
                    onClick={() => handleEnableAdmin('Mike Brown')}
                  >
                    {t.admins.enable}
                  </button>
                  <button 
                    className="text-blue-400 hover:text-blue-300"
                    onClick={() => handleEditAdmin('Mike Brown')}
                  >
                    {t.common.edit}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Section>

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title={t.admins.rolePermissions}>
          <div className="space-y-4">
            <div className="p-4 bg-gray-800 rounded-lg">
              <h4 className="text-sm font-medium text-white mb-2">{t.admins.superAdmins}</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• 전체 시스템 관리</li>
                <li>• 모든 관리자 계정 관리</li>
                <li>• 시스템 설정 변경</li>
                <li>• 감사 로그 접근</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg">
              <h4 className="text-sm font-medium text-white mb-2">{t.admins.systemAdmins}</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• 파트너 관리</li>
                <li>• 거래 모니터링</li>
                <li>• 에너지 풀 관리</li>
                <li>• 사용자 지원</li>
              </ul>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg">
              <h4 className="text-sm font-medium text-white mb-2">{t.admins.supportStaff}</h4>
              <ul className="text-sm text-gray-300 space-y-1">
                <li>• 사용자 문의 처리</li>
                <li>• 기본 계정 관리</li>
                <li>• 보고서 생성</li>
                <li>• 제한된 시스템 접근</li>
              </ul>
            </div>
          </div>
        </Section>

        <Section title={t.admins.recentActivity}>
          <div className="space-y-3">
            <div className="flex items-center p-3 bg-gray-800 rounded-lg">
              <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-xs text-white">👤</span>
              </div>
              <div className="flex-1">
                <p className="text-sm text-white">John Doe가 파트너 설정을 수정했습니다</p>
                <p className="text-xs text-gray-400">30분 전</p>
              </div>
            </div>
            <div className="flex items-center p-3 bg-gray-800 rounded-lg">
              <div className="h-8 w-8 bg-green-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-xs text-white">✅</span>
              </div>
              <div className="flex-1">
                <p className="text-sm text-white">새 관리자 계정이 승인되었습니다</p>
                <p className="text-xs text-gray-400">2시간 전</p>
              </div>
            </div>
            <div className="flex items-center p-3 bg-gray-800 rounded-lg">
              <div className="h-8 w-8 bg-red-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-xs text-white">🚫</span>
              </div>
              <div className="flex-1">
                <p className="text-sm text-white">Mike Brown 계정이 정지되었습니다</p>
                <p className="text-xs text-gray-400">3일 전</p>
              </div>
            </div>
          </div>
        </Section>
      </div>
    </BasePage>
  );
}