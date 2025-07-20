import { ReactNode } from 'react';
import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, StatCard } from '@/components/ui/DarkThemeComponents';

interface PageTemplateProps {
  title: string;
  description?: string;
  headerActions?: ReactNode;
  children: ReactNode;
}

export function PageTemplate({ title, description, headerActions, children }: PageTemplateProps) {
  return (
    <BasePage 
      title={title}
      description={description}
      headerActions={headerActions}
    >
      {children}
    </BasePage>
  );
}

interface StatsGridProps {
  stats: Array<{
    title: string;
    value: string | number;
    icon?: string;
    trend?: 'up' | 'down' | 'neutral';
    description?: string;
  }>;
}

export function StatsGrid({ stats }: StatsGridProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6 mb-6">
      {stats.map((stat, index) => (
        <StatCard
          key={index}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          trend={stat.trend}
          description={stat.description}
        />
      ))}
    </div>
  );
}

interface ActionBarProps {
  children: ReactNode;
}

export function ActionBar({ children }: ActionBarProps) {
  return (
    <div className="flex flex-wrap gap-4 mb-6">
      {children}
    </div>
  );
}

interface ContentGridProps {
  children: ReactNode;
  columns?: 1 | 2 | 3 | 4;
}

export function ContentGrid({ children, columns = 2 }: ContentGridProps) {
  const gridClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 lg:grid-cols-2',
    3: 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-3',
    4: 'grid-cols-1 lg:grid-cols-2 xl:grid-cols-4'
  };

  return (
    <div className={`grid ${gridClass[columns]} gap-6`}>
      {children}
    </div>
  );
}
