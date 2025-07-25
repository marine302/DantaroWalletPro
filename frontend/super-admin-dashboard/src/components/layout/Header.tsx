'use client';

import { Menu, Transition } from '@headlessui/react';
import { Bars3Icon, BellIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { Fragment } from 'react';
import { cn } from '@/lib/utils';
import { LanguageToggle } from '@/components/ui/LanguageSelector';
import BackendStatusMonitor from '@/components/ui/BackendStatusMonitor';
// import { useI18n } from '@/contexts/I18nContext';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

interface HeaderProps {
  setSidebarOpen: (open: boolean) => void;
}

export function Header({ setSidebarOpen }: HeaderProps) {
  const { t } = useI18n();
  const { user, logout } = useAuth();
  const _router = useRouter();

  const _handleLogout = () => {
    logout();
    router.push('/login');
  };

  const _userNavigation = [
    { name: t.common.profile, href: '#' },
    { name: t.settings.title, href: '/settings' },
    { name: t.nav.logout, href: '#', onClick: handleLogout },
  ];

  return (
    <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-700 bg-gray-900 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      <button type="button" className="-m-2.5 p-2.5 text-gray-300 lg:hidden" onClick={() => setSidebarOpen(true)}>
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>

      {/* Separator */}
      <div className="h-6 w-px bg-gray-700 lg:hidden" aria-hidden="true" />

      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <div className="flex flex-1 items-center">
          {/* 백엔드 API 상태 모니터 */}
          <BackendStatusMonitor className="mr-4" />
        </div>
        <div className="flex items-center gap-x-4 lg:gap-x-6">
          {/* Language Toggle */}
          <LanguageToggle />

          {/* Notifications */}

          {/* Separator */}
          <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-700" aria-hidden="true" />

          {/* Profile dropdown */}
          <Menu as="div" className="relative">
            <Menu.Button className="-m-1.5 flex items-center p-1.5">
              <span className="sr-only">Open user menu</span>
              <div className="flex items-center">
                <UserCircleIcon className="h-8 w-8 text-gray-300" aria-hidden="true" />
                {user && (
                  <div className="ml-3 hidden lg:block">
                    <p className="text-sm font-medium text-gray-300">{user.name}</p>
                    <p className="text-xs text-gray-400 capitalize">{user.role.replace('_', ' ')}</p>
                  </div>
                )}
              </div>
            </Menu.Button>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 z-10 mt-2.5 w-48 origin-top-right rounded-md bg-gray-800 py-2 shadow-lg ring-1 ring-gray-700 focus:outline-none">
                {userNavigation.map((item) => (
                  <Menu.Item key={item.name}>
                    {({ active }) => (
                      <button
                        onClick={item.onClick || (() => {})}
                        className={cn(
                          active ? 'bg-gray-700' : '',
                          'block w-full text-left px-3 py-1 text-sm leading-6 text-gray-300'
                        )}
                      >
                        {item.name}
                      </button>
                    )}
                  </Menu.Item>
                ))}
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </div>
  );
}
