'use client';

import React from "react"

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';
import { StaffBottomNav } from '@/components/navigation/bottom-nav';
import { LoadingPage } from '@/components/ui/loading-states';

export default function StaffLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      // Staff pages are accessible to staff and owners only
      if (!user) {
        router.replace('/login');
      } else if (user.role !== 'staff' && user.role !== 'restaurant_owner') {
        router.replace('/');
      }
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return <LoadingPage message="Loading..." />;
  }

  if (!user || (user.role !== 'staff' && user.role !== 'restaurant_owner')) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {children}
      <StaffBottomNav />
    </div>
  );
}
