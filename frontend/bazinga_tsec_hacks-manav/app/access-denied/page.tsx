'use client';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useAuth } from '@/store/authContext';
import { useRouter } from 'next/navigation';
import { AlertTriangle } from 'lucide-react';

export default function AccessDeniedPage() {
  const { logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 to-slate-100 px-4">
      <Card className="w-full max-w-md border-0 shadow-lg">
        <div className="p-8 text-center">
          <AlertTriangle className="h-12 w-12 text-red-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-slate-900 mb-2">
            Access Denied
          </h1>
          <p className="text-slate-600 mb-6">
            You do not have permission to access this page. Please contact an
            administrator if you believe this is an error.
          </p>
          <Button
            onClick={handleLogout}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
          >
            Return to Login
          </Button>
        </div>
      </Card>
    </div>
  );
}
