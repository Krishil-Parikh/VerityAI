'use client';

import React from "react"

import { AppTopbar } from '@/components/layout/AppTopbar';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function CitizenLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute allowedRoles={['citizen']}>
      <div className="flex flex-col h-screen">
        <AppTopbar />
        <div className="flex flex-1 overflow-hidden">
          <AppSidebar />
          <main className="flex-1 overflow-hidden">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}
