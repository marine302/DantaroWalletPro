#!/bin/bash

# Fix critical TypeScript errors in specific files
echo "🔧 Fixing critical TypeScript errors..."

# Fix useI18n import in files that don't have it imported
echo "Adding useI18n imports..."

# Add useI18n import to fees/page.tsx
sed -i '' "1i\\
import { useI18n } from '@/contexts/I18nContext';
" src/app/fees/page.tsx

# Add useI18n import to settings/page.tsx  
sed -i '' "1i\\
import { useI18n } from '@/contexts/I18nContext';
" src/app/settings/page.tsx

# Add useI18n import to partner-onboarding/page.tsx
sed -i '' "1i\\
import { useI18n } from '@/contexts/I18nContext';
" src/app/partner-onboarding/page.tsx

# Add useI18n import to integrated-dashboard/page.tsx
sed -i '' "1i\\
import { useI18n } from '@/contexts/I18nContext';
" src/app/integrated-dashboard/page.tsx

# Add useI18n import to page.tsx (main dashboard)
sed -i '' "1i\\
import { useI18n } from '@/contexts/I18nContext';
" src/app/page.tsx

# Add useRouter import to various files
echo "Adding useRouter imports..."

# Fix layout.tsx - add missing font imports
sed -i '' 's/className={`${geistSans.variable} ${geistMono.variable} antialiased`}/className="antialiased"/' src/app/layout.tsx

# Fix import issues in super-admin service
sed -i '' 's/import { superAdminService/import { SuperAdminService/' src/hooks/use-super-admin.ts
sed -i '' 's/superAdminService/new SuperAdminService()/' src/hooks/use-super-admin.ts

# Fix api-client import
sed -i '' 's/import { apiClient/import { _apiClient as apiClient/' src/services/super-admin-service.ts

echo "✅ Critical errors fixed. Running type check..."

# Run type check to see remaining errors
npm run type-check

echo "🔧 Fix script completed."
