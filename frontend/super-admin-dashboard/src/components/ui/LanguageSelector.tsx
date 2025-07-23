'use client';

import React from 'react';
// import { useI18n } from '@/contexts/I18nContext';
import { Locale } from '@/types/i18n';

interface LanguageSelectorProps {
  className?: string;
}

export function LanguageSelector({ className = '' }: LanguageSelectorProps) {
  const { locale, setLocale } = useI18n();

  const languages: { code: Locale; name: string; flag: string }[] = [
    { code: 'ko', name: '한국어', flag: '🇰🇷' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
  ];

  return (
    <div className={`relative ${className}`}>
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className="bg-gray-800 border border-gray-600 text-gray-100 text-sm rounded-lg
                   focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5
                   appearance-none cursor-pointer hover:bg-gray-700 transition-colors"
      >
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.flag} {lang.name}
          </option>
        ))}
      </select>
    </div>
  );
}

// Header용 간단한 언어 토글
export function LanguageToggle() {
  const { locale, setLocale } = useI18n();

  const _toggleLanguage = () => {
    setLocale(locale === 'ko' ? 'en' : 'ko');
  };

  return (
    <button
      onClick={toggleLanguage}
      className="p-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
      title={locale === 'ko' ? 'Switch to English' : '한국어로 변경'}
    >
      <span className="text-sm font-medium">
        {locale === 'ko' ? '🇰🇷 KO' : '🇺🇸 EN'}
      </span>
    </button>
  );
}
