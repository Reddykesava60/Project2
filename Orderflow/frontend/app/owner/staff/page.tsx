'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { useAuthStore } from '@/lib/store';
import { staffApi } from '@/lib/api';
import type { StaffMember } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { SkeletonCard, LoadingSpinner } from '@/components/ui/loading-states';
import { ErrorState, EmptyState } from '@/components/ui/error-states';
import {
  Plus,
  Users,
  Banknote,
  KeyRound,
  AlertCircle,
  UserCheck,
  UserX,
  UtensilsCrossed,
} from 'lucide-react';

export default function OwnerStaffPage() {
  const user = useAuthStore((state) => state.user);
  const restaurantId = user?.restaurant_id;

  const [isCreating, setIsCreating] = useState(false);
  const [resetPasswordFor, setResetPasswordFor] = useState<StaffMember | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
  });

  const {
    data: staffData,
    error: fetchError,
    isLoading,
    mutate,
  } = useSWR(
    restaurantId ? `/staff/${restaurantId}` : null,
    () => staffApi.getAll(restaurantId!)
  );

  const staffDataResponse = staffData?.data;
  const staffMembers = (Array.isArray(staffDataResponse)
    ? staffDataResponse
    : (staffDataResponse as any)?.results || []) as StaffMember[];

  const handleCreate = async () => {
    if (!restaurantId || !form.name.trim() || !form.email.trim() || !form.password.trim()) return;
    setIsSubmitting(true);
    setError(null);

    const [firstName, ...lastNameParts] = form.name.trim().split(' ');
    const lastName = lastNameParts.join(' ') || '';

    const response = await staffApi.create(restaurantId, {
      first_name: firstName,
      last_name: lastName,
      email: form.email.trim(),
      password: form.password,
    });

    if (!response.success) {
      setError(response.error || 'Failed to create staff member');
      setIsSubmitting(false);
      return;
    }

    setForm({ name: '', email: '', password: '' });
    setIsCreating(false);
    setIsSubmitting(false);
    mutate();
  };

  const handleToggleActive = async (staff: StaffMember) => {
    const response = await staffApi.toggleActive(staff.id, !staff.is_active);
    if (!response.success) {
      alert(response.error || 'Failed to update status');
      return;
    }
    mutate();
  };

  const handleToggleCashPermission = async (staff: StaffMember) => {
    const response = await staffApi.toggleCashPermission(staff.id, !staff.can_collect_cash);
    if (!response.success) {
      alert(response.error || 'Failed to update permission');
      return;
    }
    mutate();
  };

  const handleToggleStockPermission = async (staff: StaffMember) => {
    const response = await staffApi.toggleStockPermission(staff.id, !staff.can_manage_stock);
    if (!response.success) {
      alert(response.error || 'Failed to update permission');
      return;
    }
    mutate();
  };

  const handleResetPassword = async () => {
    if (!resetPasswordFor) return;
    setIsSubmitting(true);

    const response = await staffApi.resetPassword(resetPasswordFor.id);

    setIsSubmitting(false);
    setResetPasswordFor(null);

    if (!response.success) {
      alert(response.error || 'Failed to reset password');
      return;
    }

    alert('Password reset email has been sent.');
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
        <div className="flex items-center justify-between px-4 py-4 lg:px-6">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Staff Management</h1>
            <p className="text-sm text-muted-foreground">
              {staffMembers.filter((s) => s.is_active).length} active staff members
            </p>
          </div>
          <Button onClick={() => setIsCreating(true)} className="min-h-[44px]">
            <Plus className="h-4 w-4 mr-2" />
            Add Staff
          </Button>
        </div>
      </header>

      <div className="p-4 lg:p-6">
        {isLoading ? (
          <div className="space-y-4">
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : fetchError || !staffData?.success ? (
          <ErrorState
            title="Failed to Load Staff"
            message="Unable to fetch staff data."
            onRetry={() => mutate()}
          />
        ) : staffMembers.length === 0 ? (
          <EmptyState
            icon={<Users className="h-8 w-8 text-muted-foreground" />}
            title="No Staff Members"
            message="Add your first staff member to get started."
            action={
              <Button onClick={() => setIsCreating(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Staff
              </Button>
            }
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {staffMembers.map((staff) => (
              <Card key={staff.id} className={!staff.is_active ? 'opacity-60' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-12 w-12 items-center justify-center rounded-full ${staff.is_active ? 'bg-primary/10' : 'bg-muted'
                          }`}
                      >
                        {staff.is_active ? (
                          <UserCheck className="h-6 w-6 text-primary" />
                        ) : (
                          <UserX className="h-6 w-6 text-muted-foreground" />
                        )}
                      </div>
                      <div>
                        <p className="font-semibold text-foreground">{staff.name}</p>
                        <p className="text-sm text-muted-foreground">{staff.email}</p>
                      </div>
                    </div>
                    <Badge variant={staff.is_active ? 'default' : 'secondary'}>
                      {staff.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>

                  {/* Permissions */}
                  <div className="space-y-3 rounded-lg bg-muted/50 p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Banknote className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Cash Collection</span>
                      </div>
                      <Switch
                        checked={staff.can_collect_cash}
                        onCheckedChange={() => handleToggleCashPermission(staff)}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {staff.can_collect_cash
                        ? 'Can collect cash and create cash orders'
                        : 'Cannot handle cash transactions'}
                    </p>

                    <div className="flex items-center justify-between pt-2 border-t border-border/50">
                      <div className="flex items-center gap-2">
                        <UtensilsCrossed className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Stock Control</span>
                      </div>
                      <Switch
                        checked={staff.can_manage_stock}
                        onCheckedChange={() => handleToggleStockPermission(staff)}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {staff.can_manage_stock
                        ? 'Can update menu stock & availability'
                        : 'Cannot modify menu items'}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="mt-4 flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleToggleActive(staff)}
                      className="flex-1 min-h-[44px]"
                    >
                      {staff.is_active ? 'Deactivate' : 'Activate'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setResetPasswordFor(staff)}
                      className="flex-1 min-h-[44px]"
                    >
                      <KeyRound className="h-4 w-4 mr-1" />
                      Reset Password
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Staff Dialog */}
      <Dialog
        open={isCreating}
        onOpenChange={(open) => {
          if (!open) {
            setIsCreating(false);
            setForm({ name: '', email: '', password: '' });
            setError(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Staff Member</DialogTitle>
            <DialogDescription>
              Create a new staff account for your restaurant
            </DialogDescription>
          </DialogHeader>

          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="staff-name">Name</Label>
              <Input
                id="staff-name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Full name"
                className="h-12"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="staff-email">Email</Label>
              <Input
                id="staff-email"
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="email@example.com"
                className="h-12"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="staff-password">Initial Password</Label>
              <Input
                id="staff-password"
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="Temporary password"
                className="h-12"
              />
              <p className="text-xs text-muted-foreground">
                The staff member should change this after their first login.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsCreating(false);
                setError(null);
              }}
              disabled={isSubmitting}
              className="min-h-[44px]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={
                isSubmitting ||
                !form.name.trim() ||
                !form.email.trim() ||
                !form.password.trim()
              }
              className="min-h-[44px]"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Creating...
                </>
              ) : (
                'Create Staff'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <AlertDialog
        open={!!resetPasswordFor}
        onOpenChange={(open) => !open && setResetPasswordFor(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reset Password</AlertDialogTitle>
            <AlertDialogDescription>
              This will send a password reset email to{' '}
              <strong>{resetPasswordFor?.email}</strong>. Are you sure?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isSubmitting} className="min-h-[44px]">
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleResetPassword}
              disabled={isSubmitting}
              className="min-h-[44px]"
            >
              {isSubmitting ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Sending...
                </>
              ) : (
                'Send Reset Email'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
}
