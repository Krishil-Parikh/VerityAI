'use client';

import { useAuth } from '@/store/authContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { ContainerScroll } from '@/components/containerScroll';
import RadialOrbitalTimeline from '@/components/orbitalTimeline';
import {
  ShieldCheck,
  Scale,
  Server,
  Rocket,
  Home as HomeIcon,
  User,
  Settings,
  Mail,
} from 'lucide-react';
import { NavBar } from '@/components/ui/navbar';
import { ThemeToggle } from '@/components/toggle';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function Home() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();

  const navItems = [
    { name: 'Home', url: '/', icon: HomeIcon },
    { name: 'About', url: '#about', icon: User },
    { name: 'Services', url: '#services', icon: Settings },
    { name: 'Contact', url: '#contact', icon: Mail },
  ];

  // Realistic milestones for GovAudit / RTI ethics project
  const timelineData = [
    {
      id: 1,
      title: 'Ethical Metrics Blueprint',
      date: '2026-02-01',
      content:
        'Defined cross‑department metric library for RTI chatbots – bias, legality, grounding, and security scores.',
      category: 'Design',
      icon: Scale,
      relatedIds: [2],
      status: 'completed' as const,
      energy: 90,
    },
    {
      id: 2,
      title: 'GovAudit Scoring Engine',
      date: '2026-02-02',
      content:
        'Implemented log‑based scoring for every RTI interaction using LLM “judges” and statistical checks.',
      category: 'Scoring Engine',
      icon: Server,
      relatedIds: [1, 3],
      status: 'in-progress' as const,
      energy: 95,
    },
    {
      id: 3,
      title: 'Live Oversight Dashboard',
      date: '2026-02-03',
      content:
        'Launched real‑time admin console with traffic‑light alerts, audit trails, and department‑specific thresholds.',
      category: 'Launch',
      icon: Rocket,
      relatedIds: [2],
      status: 'pending' as const,
      energy: 80,
    },
  ];

  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.role === 'citizen') {
        router.push('/citizen');
      } else if (user.role === 'admin') {
        router.push('/admin');
      }
    } else {
      // stay on landing for unauthenticated users
      // remove router.push('/') to avoid redirect loop on home
    }
  }, [isAuthenticated, user, router]);

  return (
    <>
      {/* Top nav + theme toggle */}
      <div className="fixed top-0 left-0 right-0 z-50 flex justify-center items-center pointer-events-none">
        <div className="w-full max-w-7xl px-4 flex justify-between items-center pointer-events-auto">
          <div className="pt-6">
            <ThemeToggle />
          </div>
          <NavBar items={navItems} className="static translate-x-0 mb-0 pt-6" />
          <div className="pt-6 flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="rounded-full">
                Login
              </Button>
            </Link>
            <Link href="/login">
              <Button size="sm" className="rounded-full">
                Sign up
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Hero section: left header + right orbital timeline */}
      <main className="min-h-screen bg-background pt-15">
        <section className="max-w-7xl mx-auto px-4 lg:px-8 flex flex-col lg:flex-row items-center gap-10 lg:gap-16">
          {/* Left: hero copy / CTO pitch */}
          <div className="w-full lg:w-1/2 space-y-6">
            
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight">
              Put every government AI answer{' '}
              <span className="text-primary">under measurable oversight.</span>
            </h1>
            <p className="text-muted-foreground text-sm sm:text-base max-w-xl">
              GovAudit AI gives your CTO and compliance teams a live command
              centre for RTI chatbots—tracking fairness, legal safety and data
              grounding for every response, without touching model internals.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="rounded-2xl border bg-card p-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <Scale className="h-4 w-4 text-primary" />
                  Ethical Dimensions
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  8+ dimensions scored per answer – bias, drift, explainability,
                  legal compliance, robustness and more.
                </p>
              </div>
              <div className="rounded-2xl border bg-card p-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <ShieldCheck className="h-4 w-4 text-primary" />
                  Zero‑trust Friendly
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Works from logs, prompts and responses only, ready to slot
                  into existing government cloud deployments.
                </p>
              </div>
            </div>
          </div>

          {/* Right: orbital timeline hero visual */}
          <div className="w-full lg:w-1/2">
            <RadialOrbitalTimeline timelineData={timelineData} />
          </div>
        </section>

        {/* Below‑the‑fold sections driven by ContainerScroll */}
        <section className="mt-0 -top-20 relative">
          <ContainerScroll titleComponent="Home">
            <div className="max-w-4xl mx-auto py-10">
              <h2 className="text-2xl font-semibold mb-4">Why GovAudit AI</h2>
              <p className="text-muted-foreground text-sm">
                Standardised ethical scoring for RTI and FOI chatbots, designed
                for public‑sector governance teams. Plug our metrics into your
                existing monitoring stack and give leadership a single,
                defensible score for every AI answer.
              </p>
            </div>
          </ContainerScroll>
        </section>
      </main>
    </>
  );
}
