'use client';

import React from "react"

import { useAuth } from '@/store/authContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { UserRole } from '@/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { user, isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Don't redirect while still loading from localStorage
    if (loading) return;

    if (!isAuthenticated) {
      router.push('/login');
    } else if (user && !allowedRoles.includes(user.role)) {
      router.push('/access-denied');
    }
  }, [isAuthenticated, user, allowedRoles, router, loading]);

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated || !user || !allowedRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}
