'use client';

import React from "react"

import { useAuth } from '@/store/authContext';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MessageSquare, BarChart3, Settings, History } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const citizenNav: NavItem[] = [
  {
    label: 'Chat',
    href: '/citizen',
    icon: <MessageSquare className="h-4 w-4" />,
  },
  {
    label: 'History',
    href: '/citizen/history',
    icon: <History className="h-4 w-4" />,
  },
];

const adminNav: NavItem[] = [
  {
    label: 'Overview',
    href: '/admin',
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    label: 'Conversations',
    href: '/admin/conversations',
    icon: <MessageSquare className="h-4 w-4" />,
  },
  {
    label: 'Settings',
    href: '/admin/settings',
    icon: <Settings className="h-4 w-4" />,
  },
];

export function AppSidebar() {
  const { user } = useAuth();
  const pathname = usePathname();

  if (!user) return null;

  const navItems = user.role === 'citizen' ? citizenNav : adminNav;

  return (
    <aside className="h-[calc(100vh-64px)] w-64 border-r border-border/40 bg-background/50 backdrop-blur-xl p-4 flex flex-col gap-4">
      <nav className="space-y-1 flex-1">
        <div className="text-xs font-semibold text-muted-foreground/50 uppercase tracking-wider mb-4 px-2">Menu</div>
        {navItems.map((item) => (
          <Link key={item.href} href={item.href}>
            <div
              className={cn(
                'group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-300 ease-in-out',
                pathname === item.href
                  ? 'bg-primary/10 text-primary shadow-[0_0_20px_rgba(0,0,0,0.05)] dark:shadow-[0_0_20px_rgba(255,255,255,0.05)]'
                  : 'text-muted-foreground hover:bg-secondary/80 hover:text-foreground hover:translate-x-1'
              )}
            >
              <span className={cn(
                "transition-transform duration-300",
                pathname === item.href ? "scale-110" : "group-hover:scale-110"
              )}>
                {item.icon}
              </span>
              {item.label}
              {pathname === item.href && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary" />
              )}
            </div>
          </Link>
        ))}
      </nav>

      <div className="mt-auto">
        <div className="rounded-2xl bg-gradient-to-br from-primary/10 to-blue-500/10 p-4 border border-primary/20">
          <h4 className="font-semibold text-sm text-foreground mb-1">GovAudit Pro</h4>
          <p className="text-xs text-muted-foreground mb-3">
            Upgrade for advanced analytics and export features.
          </p>
          <div className="text-xs font-medium text-primary cursor-pointer hover:underline">
            Learn more &rarr;
          </div>
        </div>
      </div>
    </aside>
  );
}
