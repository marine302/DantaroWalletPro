'use client';

import { BasePage } from '@/components/ui/BasePage';
import { Button, Section, FormField } from '@/components/ui/DarkThemeComponents';

export default function SettingsPage() {
  const headerActions = (
    <Button variant="secondary">
      Save Settings
    </Button>
  );

  return (
    <BasePage 
      title="System Settings"
      description="Configure global system settings, security policies, and platform parameters."
      headerActions={headerActions}
    >
      <div className="space-y-6">
        <Section title="Platform Configuration">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FormField
              label="Platform Name"
              value="DantaroWallet"
              onChange={() => {}}
            />
            <FormField
              label="Platform Version"
              value="1.0.0"
              onChange={() => {}}
            />
            <FormField
              label="Max Transaction Amount"
              type="number"
              value={1000000}
              onChange={() => {}}
            />
            <FormField
              label="Energy Auto-Purchase Threshold"
              type="number"
              value={5000}
              onChange={() => {}}
            />
          </div>
        </Section>

        <Section title="Security Settings">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FormField
              label="Session Timeout (minutes)"
              type="number"
              value={30}
              onChange={() => {}}
            />
            <FormField
              label="Max Login Attempts"
              type="number"
              value={5}
              onChange={() => {}}
            />
            <FormField
              label="Password Min Length"
              type="number"
              value={8}
              onChange={() => {}}
            />
            <FormField
              label="Two-Factor Authentication"
              value="Enabled"
              onChange={() => {}}
            />
          </div>
        </Section>

        <Section title="Notification Settings">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FormField
              label="Email Notifications"
              value="Enabled"
              onChange={() => {}}
            />
            <FormField
              label="SMS Notifications"
              value="Disabled"
              onChange={() => {}}
            />
            <FormField
              label="System Alerts"
              value="Enabled"
              onChange={() => {}}
            />
            <FormField
              label="Transaction Alerts"
              value="Enabled"
              onChange={() => {}}
            />
          </div>
        </Section>
      </div>
    </BasePage>
  );
}
