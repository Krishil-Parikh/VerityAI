'use client';

import { useAuth } from '@/store/authContext';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { LogOut } from 'lucide-react';
import { ThemeToggle } from '@/components/toggle';
import Image from 'next/image';

export function AppTopbar() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/');
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-6">
        <div className="flex items-center cursor-pointer pl-5" onClick={() => router.push('/')}>
          <Image
            src="/icon.png"
            alt="VerityAI Logo"
            width={160}
            height={48}
            className="h-12 w-auto object-contain"
            priority
          />
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle className="scale-75 origin-right" />

          {user && (
            <>
              <div className="flex flex-col items-end">
                <p className="text-sm font-medium text-foreground">{user.email}</p>
                <p className="text-xs capitalize text-muted-foreground">{user.role}</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="gap-2 text-muted-foreground hover:text-foreground hover:bg-muted"
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
