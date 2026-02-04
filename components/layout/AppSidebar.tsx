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
    <aside className="h-[calc(100vh-64px)] w-64 border-r border-slate-200 bg-slate-50 p-4">
      <nav className="space-y-2">
        {navItems.map((item) => (
          <Link key={item.href} href={item.href}>
            <div
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                pathname === item.href
                  ? 'bg-blue-100 text-blue-900'
                  : 'text-slate-700 hover:bg-slate-200'
              )}
            >
              {item.icon}
              {item.label}
            </div>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
