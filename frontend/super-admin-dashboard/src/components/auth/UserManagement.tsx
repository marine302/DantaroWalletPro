'use client';

import React, { useState } from 'react';
import { User, Role, Permission } from '@/types/auth';
import { useAuth } from '@/contexts/AuthContext';
import { PermissionGuard } from '@/components/auth/PermissionGuard';
import { Button } from '@/components/ui/Button';
import { logActivity } from '@/lib/activity-logger';

interface UserManagementProps {
  users: User[];
  onUpdateUser: (user: User) => void;
  onDeleteUser: (userId: string) => void;
}

export function UserManagement({ users, onUpdateUser, onDeleteUser }: UserManagementProps) {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const { hasPermission, user: currentUser } = useAuth();

  const roleLabels: Record<Role, string> = {
    super_admin: '슈퍼 관리자',
    admin: '관리자',
    viewer: '뷰어',
    auditor: '감사자'
  };

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
    setIsEditModalOpen(true);
  };

  const handleSaveUser = (updatedUser: User) => {
    onUpdateUser(updatedUser);
    
    // Log the activity
    if (currentUser) {
      logActivity({
        user: currentUser,
        action: 'update',
        resource: 'user',
        details: {
          targetUserId: updatedUser.id,
          targetUserName: updatedUser.name,
          changes: {
            role: updatedUser.role,
            isActive: updatedUser.isActive
          }
        }
      });
    }
    
    setIsEditModalOpen(false);
    setSelectedUser(null);
  };

  const handleDeleteUser = (userId: string) => {
    if (confirm('정말로 이 사용자를 삭제하시겠습니까?')) {
      const userToDelete = users.find(u => u.id === userId);
      onDeleteUser(userId);
      
      // Log the activity
      if (currentUser && userToDelete) {
        logActivity({
          user: currentUser,
          action: 'delete',
          resource: 'user',
          details: {
            targetUserId: userToDelete.id,
            targetUserName: userToDelete.name
          }
        });
      }
    }
  };

  const getRoleColor = (role: Role) => {
    switch (role) {
      case 'super_admin': return 'bg-red-100 text-red-800';
      case 'admin': return 'bg-blue-100 text-blue-800';
      case 'viewer': return 'bg-green-100 text-green-800';
      case 'auditor': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-semibold text-white">사용자 관리</h2>
        <PermissionGuard permission="users.create">
          <Button variant="default">
            사용자 추가
          </Button>
        </PermissionGuard>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                사용자
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                역할
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                상태
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                마지막 로그인
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                작업
              </th>
            </tr>
          </thead>
          <tbody className="bg-gray-800 divide-y divide-gray-700">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-gray-600 flex items-center justify-center">
                        <span className="text-white font-medium">
                          {user.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-white">{user.name}</div>
                      <div className="text-sm text-gray-400">{user.email}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColor(user.role)}`}>
                    {roleLabels[user.role]}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.isActive 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {user.isActive ? '활성' : '비활성'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                  {user.lastLogin 
                    ? new Date(user.lastLogin).toLocaleString('ko-KR')
                    : '로그인 기록 없음'
                  }
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    <PermissionGuard permission="users.edit">
                      <button
                        onClick={() => handleEditUser(user)}
                        className="text-blue-400 hover:text-blue-300"
                      >
                        편집
                      </button>
                    </PermissionGuard>
                    <PermissionGuard permission="users.delete">
                      {user.role !== 'super_admin' && (
                        <button
                          onClick={() => handleDeleteUser(user.id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          삭제
                        </button>
                      )}
                    </PermissionGuard>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* User Edit Modal */}
      {isEditModalOpen && selectedUser && (
        <UserEditModal
          user={selectedUser}
          onSave={handleSaveUser}
          onCancel={() => {
            setIsEditModalOpen(false);
            setSelectedUser(null);
          }}
        />
      )}
    </div>
  );
}

interface UserEditModalProps {
  user: User;
  onSave: (user: User) => void;
  onCancel: () => void;
}

function UserEditModal({ user, onSave, onCancel }: UserEditModalProps) {
  const [editedUser, setEditedUser] = useState<User>({ ...user });
  const { hasPermission } = useAuth();

  const roles: { value: Role; label: string }[] = [
    { value: 'viewer', label: '뷰어' },
    { value: 'auditor', label: '감사자' },
    { value: 'admin', label: '관리자' },
    { value: 'super_admin', label: '슈퍼 관리자' },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(editedUser);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
        <h3 className="text-lg font-semibold text-white mb-4">사용자 편집</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              이름
            </label>
            <input
              type="text"
              value={editedUser.name}
              onChange={(e) => setEditedUser({ ...editedUser, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              이메일
            </label>
            <input
              type="email"
              value={editedUser.email}
              onChange={(e) => setEditedUser({ ...editedUser, email: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <PermissionGuard permission="users.manage_roles">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                역할
              </label>
              <select
                value={editedUser.role}
                onChange={(e) => setEditedUser({ ...editedUser, role: e.target.value as Role })}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {roles.map(role => (
                  <option key={role.value} value={role.value}>
                    {role.label}
                  </option>
                ))}
              </select>
            </div>
          </PermissionGuard>

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={editedUser.isActive}
                onChange={(e) => setEditedUser({ ...editedUser, isActive: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-300">활성 상태</span>
            </label>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <Button type="button" variant="secondary" onClick={onCancel}>
              취소
            </Button>
            <Button type="submit" variant="default">
              저장
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
