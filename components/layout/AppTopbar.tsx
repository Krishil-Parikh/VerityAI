'use client';

import { useAuth } from '@/store/authContext';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { LogOut } from 'lucide-react';

export function AppTopbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="text-2xl font-bold text-blue-600">GovAudit AI</div>
          <span className="text-sm text-slate-600">RTI Portal</span>
        </div>

        <div className="flex items-center gap-4">
          {user && (
            <>
              <div className="flex flex-col items-end">
                <p className="text-sm font-medium text-slate-900">{user.email}</p>
                <p className="text-xs capitalize text-slate-500">{user.role}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="gap-2"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
