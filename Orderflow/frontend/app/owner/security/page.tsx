'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { AppLayout } from '@/components/layout/app-layout'
import { withAuth } from '@/components/auth/with-auth'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { MobileSheet, MobileSheetContent, MobileSheetFooter } from '@/components/ui/mobile-sheet'
import { Shield, Smartphone, Lock, ChevronRight, Eye, EyeOff, CheckCircle } from 'lucide-react'

function SecurityPage() {
  const router = useRouter()
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false)
  const [showPasswordSheet, setShowPasswordSheet] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  })
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  const handlePasswordChange = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      return
    }
    
    setPasswordLoading(true)
    try {
      // API call to change password
      await new Promise(resolve => setTimeout(resolve, 1000))
      setPasswordSuccess(true)
      setTimeout(() => {
        setShowPasswordSheet(false)
        setPasswordSuccess(false)
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
      }, 1500)
    } finally {
      setPasswordLoading(false)
    }
  }

  const isPasswordValid = 
    passwordForm.currentPassword.length >= 1 &&
    passwordForm.newPassword.length >= 8 &&
    passwordForm.newPassword === passwordForm.confirmPassword

  return (
    <AppLayout title="Security">
      <div className="space-y-4">
        {/* 2FA Section */}
        <div className="surface-card p-4 rounded-xl">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Shield className="w-5 h-5 text-primary" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold">Two-Factor Authentication</h3>
              <p className="text-sm text-muted-foreground">Add extra security to your account</p>
            </div>
            <Switch
              checked={twoFactorEnabled}
              onCheckedChange={setTwoFactorEnabled}
            />
          </div>

          {twoFactorEnabled ? (
            <div className="space-y-3 pt-4 border-t">
              <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 dark:bg-green-950/30 p-3 rounded-lg">
                <Smartphone className="w-4 h-4" />
                <span>Authenticator app configured</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Button variant="outline" className="min-h-touch">
                  Backup Codes
                </Button>
                <Button variant="destructive" className="min-h-touch">
                  Disable 2FA
                </Button>
              </div>
            </div>
          ) : (
            <Button className="w-full min-h-touch mt-2">
              <Smartphone className="w-4 h-4 mr-2" />
              Set Up 2FA
            </Button>
          )}
        </div>

        {/* Password Section */}
        <button 
          className="w-full surface-card p-4 rounded-xl flex items-center gap-3 text-left active:scale-[0.98] transition-transform touch-action-manipulation"
          onClick={() => setShowPasswordSheet(true)}
        >
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Lock className="w-5 h-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold">Change Password</h3>
            <p className="text-sm text-muted-foreground">Update your password regularly for security</p>
          </div>
          <ChevronRight className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Security Tips */}
        <div className="surface-card p-4 rounded-xl">
          <h3 className="font-semibold mb-3">Security Tips</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Use a strong, unique password for your account</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Enable two-factor authentication for extra protection</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Only grant cash collection permission to trusted staff</span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Review cash audit logs regularly</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Change Password Sheet */}
      <MobileSheet
        open={showPasswordSheet}
        onOpenChange={setShowPasswordSheet}
        title="Change Password"
        description="Enter your current password and choose a new one"
      >
        <MobileSheetContent className="space-y-4">
          {passwordSuccess ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-950/30 flex items-center justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="font-semibold text-lg">Password Updated</h3>
              <p className="text-sm text-muted-foreground">Your password has been changed successfully</p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <Label htmlFor="current-password">Current Password</Label>
                <div className="relative">
                  <Input
                    id="current-password"
                    type={showPassword ? 'text' : 'password'}
                    value={passwordForm.currentPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                    className="pr-10 h-12"
                    placeholder="Enter current password"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-password">New Password</Label>
                <div className="relative">
                  <Input
                    id="new-password"
                    type={showNewPassword ? 'text' : 'password'}
                    value={passwordForm.newPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                    className="pr-10 h-12"
                    placeholder="Enter new password (min 8 characters)"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                    onClick={() => setShowNewPassword(!showNewPassword)}
                  >
                    {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {passwordForm.newPassword.length > 0 && passwordForm.newPassword.length < 8 && (
                  <p className="text-xs text-destructive">Password must be at least 8 characters</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm New Password</Label>
                <div className="relative">
                  <Input
                    id="confirm-password"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={passwordForm.confirmPassword}
                    onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                    className="pr-10 h-12"
                    placeholder="Confirm new password"
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
                {passwordForm.confirmPassword.length > 0 && passwordForm.newPassword !== passwordForm.confirmPassword && (
                  <p className="text-xs text-destructive">Passwords do not match</p>
                )}
              </div>
            </>
          )}
        </MobileSheetContent>

        {!passwordSuccess && (
          <MobileSheetFooter>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                className="min-h-touch"
                onClick={() => setShowPasswordSheet(false)}
              >
                Cancel
              </Button>
              <Button
                className="min-h-touch"
                onClick={handlePasswordChange}
                disabled={!isPasswordValid || passwordLoading}
              >
                {passwordLoading ? 'Updating...' : 'Update Password'}
              </Button>
            </div>
          </MobileSheetFooter>
        )}
      </MobileSheet>
    </AppLayout>
  )
}

export default withAuth(SecurityPage, ['restaurant_owner'])
