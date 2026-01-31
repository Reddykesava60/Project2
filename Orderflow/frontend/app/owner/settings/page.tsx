'use client';

import { useState } from 'react';
import { useAuthStore } from '@/lib/store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { ErrorState } from '@/components/ui/error-states';
import { LoadingSpinner } from '@/components/ui/loading-states';
import { Shield, Bell, Smartphone, Lock, AlertCircle } from 'lucide-react';

export default function OwnerSettingsPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [settings, setSettings] = useState({
    twoFactorEnabled: false,
    orderNotifications: true,
    lowStockAlerts: true,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleToggle2FA = async () => {
    setIsSaving(true);
    setMessage(null);

    // Simulated API call
    await new Promise((resolve) => setTimeout(resolve, 1000));

    setSettings((s) => ({ ...s, twoFactorEnabled: !s.twoFactorEnabled }));
    setMessage({
      type: 'success',
      text: `Two-factor authentication ${!settings.twoFactorEnabled ? 'enabled' : 'disabled'}`,
    });
    setIsSaving(false);
  };

  if (!restaurantId) {
    return (
      <div className="p-4 lg:p-6">
        <ErrorState title="No Restaurant" message="You are not assigned to a restaurant." />
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="px-4 py-4 lg:px-6">
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
          <p className="text-sm text-muted-foreground">Manage your account and preferences</p>
        </div>
      </header>

      <div className="p-4 lg:p-6 max-w-2xl mx-auto space-y-6">
        {/* Message */}
        {message && (
          <div
            className={`flex items-center gap-2 rounded-lg p-3 text-sm ${
              message.type === 'success'
                ? 'bg-success/10 text-success'
                : 'bg-destructive/10 text-destructive'
            }`}
          >
            {message.type === 'error' && <AlertCircle className="h-4 w-4" />}
            <span>{message.text}</span>
          </div>
        )}

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Security
            </CardTitle>
            <CardDescription>Manage your account security settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Two-Factor Authentication */}
            <div className="flex items-center justify-between">
              <div className="flex items-start gap-3">
                <Lock className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div>
                  <Label className="text-base font-medium">Two-Factor Authentication</Label>
                  <p className="text-sm text-muted-foreground">
                    Add an extra layer of security to your account
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isSaving && <LoadingSpinner size="sm" />}
                <Switch
                  checked={settings.twoFactorEnabled}
                  onCheckedChange={handleToggle2FA}
                  disabled={isSaving}
                />
              </div>
            </div>

            <div className="rounded-lg bg-muted p-4 text-sm">
              <p className="font-medium text-foreground">
                {settings.twoFactorEnabled
                  ? '2FA is enabled'
                  : '2FA is not enabled'}
              </p>
              <p className="mt-1 text-muted-foreground">
                {settings.twoFactorEnabled
                  ? 'You will be asked for a verification code when logging in.'
                  : 'Enable 2FA to add extra security to your account.'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
            </CardTitle>
            <CardDescription>Configure how you receive updates</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="flex items-start gap-3">
                <Smartphone className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div>
                  <Label className="text-base font-medium">Order Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when new orders come in
                  </p>
                </div>
              </div>
              <Switch
                checked={settings.orderNotifications}
                onCheckedChange={(checked) =>
                  setSettings((s) => ({ ...s, orderNotifications: checked }))
                }
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-start gap-3">
                <Bell className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div>
                  <Label className="text-base font-medium">Low Stock Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified when menu items run low
                  </p>
                </div>
              </div>
              <Switch
                checked={settings.lowStockAlerts}
                onCheckedChange={(checked) =>
                  setSettings((s) => ({ ...s, lowStockAlerts: checked }))
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Account Info */}
        <Card>
          <CardHeader>
            <CardTitle>Account Information</CardTitle>
            <CardDescription>Your account details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label className="text-muted-foreground">Name</Label>
                <p className="font-medium text-foreground">{user?.name || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Email</Label>
                <p className="font-medium text-foreground">{user?.email || 'N/A'}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Role</Label>
                <p className="font-medium text-foreground capitalize">
                  {user?.role?.replace('_', ' ') || 'N/A'}
                </p>
              </div>
              <div>
                <Label className="text-muted-foreground">Restaurant ID</Label>
                <p className="font-mono text-sm text-foreground">{restaurantId}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
