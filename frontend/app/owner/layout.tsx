'use client';

import React from "react"

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { OwnerSidebar } from '@/components/navigation/sidebar-nav';
import { OwnerMobileNav } from '@/components/navigation/bottom-nav';
import { LoadingPage } from '@/components/ui/loading-states';

export default function OwnerLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading, logout } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.replace('/login');
      } else if (user.role !== 'restaurant_owner') {
        router.replace('/');
      }
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return <LoadingPage message="Loading..." />;
  }

  if (!user || user.role !== 'restaurant_owner') {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <OwnerSidebar onLogout={logout} />

      {/* Main Content */}
      <div className="pb-20 lg:ml-64 lg:pb-0">
        {children}
      </div>

      {/* Mobile Bottom Nav */}
      <div className="lg:hidden">
        <OwnerMobileNav />
      </div>
    </div>
  );
}
