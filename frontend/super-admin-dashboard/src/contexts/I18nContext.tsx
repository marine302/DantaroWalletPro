'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Locale, TranslationMessages } from '@/types/i18n';
import { ko } from '@/lib/i18n/ko';
import { en } from '@/lib/i18n/en';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: TranslationMessages;
  isLoading: boolean;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const translations: Record<Locale, TranslationMessages> = {
  ko,
  en,
};

interface I18nProviderProps {
  children: ReactNode;
  defaultLocale?: Locale;
}

export function I18nProvider({ children, defaultLocale = 'ko' }: I18nProviderProps) {
  const [locale, setLocale] = useState<Locale>(defaultLocale);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 브라우저 저장소에서 언어 설정 로드
    const _savedLocale = localStorage.getItem('locale') as Locale;
    if (savedLocale && translations[savedLocale]) {
      setLocale(savedLocale);
    } else {
      // 브라우저 언어 감지
      const _browserLang = navigator.language.split('-')[0] as Locale;
      if (translations[browserLang]) {
        setLocale(browserLang);
      }
    }
    setIsLoading(false);
  }, []);

  const _handleSetLocale = (newLocale: Locale) => {
    setLocale(newLocale);
    localStorage.setItem('locale', newLocale);
  };

  const contextValue: I18nContextType = {
    locale,
    setLocale: handleSetLocale,
    t: translations[locale],
    isLoading,
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  return <I18nContext.Provider value={contextValue}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextType {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}

// 편의를 위한 Hook
export function useTranslation() {
  const { t, locale, setLocale } = useI18n();
  return { t, locale, setLocale };
}
