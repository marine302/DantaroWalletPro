'use client';

import { useState } from 'react';
import BasePage from '@/components/ui/BasePage';
import { StatCard } from '@/components/ui/DarkThemeComponents';
import { withRBAC } from '@/components/auth/withRBAC';
import { UserManagement } from '@/components/auth/UserManagement';
import { User } from '@/types/auth';

function AdminsPage() {
  const [users, setUsers] = useState<User[]>([
    {
      id: '1',
      email: 'admin@dantaro.com',
      name: 'Super Admin',
      role: 'super_admin',
      isActive: true,
      lastLogin: new Date().toISOString(),
      createdAt: new Date().toISOString()
    },
    {
      id: '2',
      email: 'manager@dantaro.com',
      name: 'System Manager',
      role: 'admin',
      isActive: true,
      lastLogin: new Date(Date.now() - 86400000).toISOString(),
      createdAt: new Date().toISOString()
    },
    {
      id: '3',
      email: 'auditor@dantaro.com',
      name: 'Compliance Auditor',
      role: 'auditor',
      isActive: true,
      lastLogin: new Date(Date.now() - 172800000).toISOString(),
      createdAt: new Date().toISOString()
    },
    {
      id: '4',
      email: 'viewer@dantaro.com',
      name: 'Read Only User',
      role: 'viewer',
      isActive: false,
      createdAt: new Date().toISOString()
    }
  ]);

  const handleDeleteUser = (userId: string) => {
    setUsers(users.filter(user => user.id !== userId));
  };

  const handleUpdateUser = (updatedUser: any) => {
    setUsers(users.map(user => user.id === updatedUser.id ? { ...user, ...updatedUser } : user));
  };

  const activeUsersCount = users.filter(user => user.isActive).length;
  const totalUsersCount = users.length;
  const adminUsersCount = users.filter(user => user.role === 'admin' || user.role === 'super_admin').length;

  return (
    <BasePage title="관리자 관리" description="시스템 관리자 계정을 관리합니다">
      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="전체 사용자"
          value={totalUsersCount.toString()}
          icon="👥"
          trend="neutral"
        />
        <StatCard
          title="활성 사용자"
          value={activeUsersCount.toString()}
          icon="✅"
          trend="neutral"
        />
        <StatCard
          title="관리자 계정"
          value={adminUsersCount.toString()}
          icon="🔐"
          trend="neutral"
        />
      </div>

      {/* 사용자 관리 테이블 */}
      <UserManagement
        users={users}
        onUpdateUser={handleUpdateUser}
        onDeleteUser={handleDeleteUser}
      />
    </BasePage>
  );
}

// Export protected component
export default withRBAC(AdminsPage, {
  requiredPermissions: ['users.view']
});
