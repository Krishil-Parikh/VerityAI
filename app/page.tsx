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
  Database,
  Eye,
  Users,
  FileText,
  Lock,
  BarChart3,
  TrendingUp,
  Zap,
  CheckCircle,
  Award,
  ArrowRight,
} from 'lucide-react';
import { NavBar } from '@/components/ui/navbar';
import { ThemeToggle } from '@/components/toggle';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Footer } from '@/components/ui/footer';

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
        'Implemented log‑based scoring for every RTI interaction using LLM "judges" and statistical checks.',
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
            {/* Trust badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20">
              <ShieldCheck className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">Trusted by Government Agencies</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight">
              Put every government AI answer{' '}
              <span className="text-primary">under measurable oversight.</span>
            </h1>
            <p className="text-muted-foreground text-sm sm:text-base max-w-xl leading-relaxed">
              GovAudit AI gives your CTO and compliance teams a live command
              centre for RTI chatbots—tracking fairness, legal safety and data
              grounding for every response, without touching model internals.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4 pt-2">
              <Link href="/login">
                <Button size="lg" className="rounded-full shadow-lg hover:shadow-xl transition-all">
                  View Live Demo
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="rounded-full">
                Download Sample Report
              </Button>
            </div>

            {/* Feature highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
              <div className="rounded-2xl border bg-card p-5 shadow-sm hover:shadow-md transition-all">
                <div className="flex items-center gap-2 text-sm font-medium mb-2">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Scale className="h-5 w-5 text-primary" />
                  </div>
                  <span>Ethical Dimensions</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  8+ dimensions scored per answer – bias, drift, explainability,
                  legal compliance, robustness and more.
                </p>
              </div>
              <div className="rounded-2xl border bg-card p-5 shadow-sm hover:shadow-md transition-all">
                <div className="flex items-center gap-2 text-sm font-medium mb-2">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <ShieldCheck className="h-5 w-5 text-primary" />
                  </div>
                  <span>Zero‑trust Friendly</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Works from logs, prompts and responses only, ready to slot
                  into existing government cloud deployments.
                </p>
              </div>
            </div>

            {/* Trust indicators */}
            <div className="flex items-center gap-6 pt-4 border-t border-border">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-xs text-muted-foreground">GDPR Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-xs text-muted-foreground">Zero-Trust Ready</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-xs text-muted-foreground">AWS Native</span>
              </div>
            </div>
          </div>

          {/* Right: orbital timeline hero visual */}
          <div className="w-full lg:w-1/2">
            <RadialOrbitalTimeline timelineData={timelineData} />
          </div>
        </section>

        {/* Stats Section */}
        <section className="border-t bg-muted/20 py-12">
          <div className="max-w-7xl mx-auto px-4 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div className="space-y-2">
                <div className="text-3xl font-bold text-primary">100%</div>
                <div className="text-sm text-muted-foreground">Evidence-Based</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold text-primary">8</div>
                <div className="text-sm text-muted-foreground">Ethical Dimensions</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold text-primary">24/7</div>
                <div className="text-sm text-muted-foreground">Monitoring</div>
              </div>
              <div className="space-y-2">
                <div className="text-3xl font-bold text-primary">0</div>
                <div className="text-sm text-muted-foreground">Model Access Needed</div>
              </div>
            </div>
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

        {/* RTI / FOI specific value prop */}
        <section
          id="about"
          className="border-t bg-background py-16"
        >
          <div className="max-w-7xl mx-auto px-4 lg:px-8">
            {/* Section header */}
            <div className="mb-12">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-4">
                <Award className="w-4 h-4" />
                Purpose-Built Solution
              </div>
              <h2 className="text-3xl lg:text-4xl font-bold mb-4">
                Built for RTI and FOI desks
              </h2>
              <p className="text-lg text-muted-foreground max-w-3xl leading-relaxed">
                Public information officers cannot rely on gut feeling to
                validate AI answers. GovAudit AI scores every RTI or FOI reply
                on fairness, legal safety and data grounding using only prompts,
                responses and retrieved context.
              </p>
            </div>

            {/* Feature grid */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-2xl border bg-card p-6 shadow-sm hover:shadow-lg transition-all group">
                <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-sm font-semibold mb-2">
                  Closed‑data only
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Metrics assume no open‑internet access. We validate that
                  answers stay within approved circulars, manuals and past
                  decisions.
                </p>
              </div>

              <div className="rounded-2xl border bg-card p-6 shadow-sm hover:shadow-lg transition-all group">
                <div className="w-12 h-12 rounded-lg bg-green-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Eye className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-sm font-semibold mb-2">
                  Output‑level observability
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  No model weights or logits required – just logs: prompts,
                  responses, RAG snippets, latency, token usage and safety
                  flags.
                </p>
              </div>

              <div className="rounded-2xl border bg-card p-6 shadow-sm hover:shadow-lg transition-all group">
                <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-sm font-semibold mb-2">
                  Department‑agnostic
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  One metric library, configurable weights. Finance can
                  emphasise accuracy and legality, HR can emphasise privacy
                  and harm prevention.
                </p>
              </div>

              <div className="rounded-2xl border bg-card p-6 shadow-sm hover:shadow-lg transition-all group">
                <div className="w-12 h-12 rounded-lg bg-orange-500/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <FileText className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                </div>
                <h3 className="text-sm font-semibold mb-2">
                  Evidence, not opinion
                </h3>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Every score is backed by a calculation – from statistical
                  parity and PSI to lawfulness checks and adversarial refusal
                  rates.
                </p>
              </div>
            </div>

            {/* Additional info paragraph */}
            <div className="mt-10 max-w-3xl">
              <p className="text-muted-foreground leading-relaxed">
                Our metrics library is designed for ministries that use
                conversational AI on closed datasets – finance, procurement,
                HR and citizen services – and need evidence that answers are
                accurate, explainable and compliant with RTI guidelines and
                privacy law.
              </p>
            </div>
          </div>
        </section>

        {/* Ethical dimensions overview */}
        <section
          id="services"
          className="border-t bg-muted/10 py-16"
        >
          <div className="max-w-7xl mx-auto px-4 lg:px-8">
            <div className="text-center max-w-3xl mx-auto mb-12">
              <h2 className="text-3xl lg:text-4xl font-bold mb-4">
                Ethical dimensions we score
              </h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                GovAudit AI turns abstract principles from guidelines like the
                RTI Act, GDPR and OECD AI standards into normalised scores across
                eight core dimensions. Each dimension combines 3–5 concrete,
                log‑derived metrics.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  icon: Scale,
                  title: 'Bias & Fairness',
                  description: 'Tracks statistical parity, refusal‑rate gaps and tone neutrality across demographic variants to surface hidden bias in AI‑assisted replies.',
                  color: 'blue'
                },
                {
                  icon: Database,
                  title: 'Data Grounding & Drift',
                  description: 'Measures how tightly answers stick to retrieved RTI documents, and whether topics drift away from the approved knowledge base over time.',
                  color: 'green'
                },
                {
                  icon: Eye,
                  title: 'Explainability & Transparency',
                  description: 'Scores citation coverage, source diversity and confidence proxies so officers can see why an answer was generated.',
                  color: 'purple'
                },
                {
                  icon: ShieldCheck,
                  title: 'Legal & Regulatory Compliance',
                  description: 'Lawfulness assessments, PII disclosure rates and exemption checks aligned with RTI disclosure rules and privacy law.',
                  color: 'red'
                },
                {
                  icon: Lock,
                  title: 'Security & Adversarial Robustness',
                  description: 'Stress‑tests responses to jailbreaks and harmful prompts, monitoring adversarial refusal rate and leakage risk.',
                  color: 'orange'
                },
                {
                  icon: BarChart3,
                  title: 'Response Quality & Performance',
                  description: 'Evaluates accuracy, task completion, timeliness and consistency so departments know if AI is actually helping citizens.',
                  color: 'indigo'
                },
                {
                  icon: Users,
                  title: 'Human Control & Oversight',
                  description: 'Tracks manual overrides, escalation coverage and review activity to keep humans in the loop for sensitive answers.',
                  color: 'pink'
                },
                {
                  icon: TrendingUp,
                  title: 'Monitoring & Cost',
                  description: 'Brings latency, error rates, inference cost and uptime into the same view as ethics, for a complete operational picture.',
                  color: 'teal'
                }
              ].map((dimension, i) => {
                const Icon = dimension.icon;
                const colorMap = {
                  blue: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
                  green: 'bg-green-500/10 text-green-600 dark:text-green-400',
                  purple: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
                  red: 'bg-red-500/10 text-red-600 dark:text-red-400',
                  orange: 'bg-orange-500/10 text-orange-600 dark:text-orange-400',
                  indigo: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400',
                  pink: 'bg-pink-500/10 text-pink-600 dark:text-pink-400',
                  teal: 'bg-teal-500/10 text-teal-600 dark:text-teal-400'
                };

                return (
                  <div key={i} className="rounded-2xl border bg-card p-6 hover:shadow-lg transition-all group">
                    <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-semibold mb-2">
                      {dimension.title}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {dimension.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* How it works with existing systems */}
        <section className="border-t bg-background py-16">
          <div className="max-w-7xl mx-auto px-4 lg:px-8">
            <div className="grid lg:grid-cols-[1.2fr,1fr] gap-12 items-center">
              <div className="space-y-8">
                <div>
                  <h2 className="text-3xl lg:text-4xl font-bold mb-4">
                    A plug‑in metrics layer for your RTI bot
                  </h2>
                  <p className="text-lg text-muted-foreground leading-relaxed">
                    We don&apos;t replace your existing RTI chatbot. Instead, GovAudit
                    AI sits alongside it and consumes logs – prompts, answers,
                    retrieved snippets, latency and safety flags – to compute
                    normalised ethical scores.
                  </p>
                </div>

                <div className="space-y-6">
                  {[
                    {
                      step: '1',
                      title: 'Collect',
                      description: 'Ingest conversation logs and RAG context from your existing Azure OpenAI, AWS SageMaker or similar deployment.',
                      icon: Database
                    },
                    {
                      step: '2',
                      title: 'Score',
                      description: 'Apply our metric library with LLM judges and statistical checks to generate per‑dimension scores from 0–100.',
                      icon: BarChart3
                    },
                    {
                      step: '3',
                      title: 'Surface',
                      description: 'Stream results into your oversight dashboard with traffic‑light indicators, audit trails and downloadable reports.',
                      icon: Eye
                    }
                  ].map((step, i) => {
                    const Icon = step.icon;
                    return (
                      <div key={i} className="flex gap-4">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-lg">
                            {step.step}
                          </div>
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                            <Icon className="w-5 h-5 text-primary" />
                            {step.title}
                          </h3>
                          <p className="text-muted-foreground leading-relaxed">
                            {step.description}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="rounded-2xl border bg-card p-8 shadow-xl">
                <div className="space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-orange-500/10 flex items-center justify-center">
                      <Zap className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                    </div>
                    <h3 className="text-lg font-semibold">
                      AWS‑ready deployment
                    </h3>
                  </div>

                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Designed to run as lightweight services on AWS Lambda, with
                    metrics and audit trails stored in S3 and DynamoDB or
                    PostgreSQL. Alerts can be wired into CloudWatch when scores
                    fall below agreed thresholds.
                  </p>

                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      Because everything is driven from observables and telemetry,
                      GovAudit AI can be adopted even in strict, zero‑trust
                      government environments where model internals are off‑limits.
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2 pt-2">
                    <span className="px-3 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                      AWS Lambda
                    </span>
                    <span className="px-3 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                      S3
                    </span>
                    <span className="px-3 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                      DynamoDB
                    </span>
                    <span className="px-3 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                      CloudWatch
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Contact / CTA */}
        <section
          id="contact"
          className="border-t bg-muted/10 py-16"
        >
          <div className="max-w-4xl mx-auto px-4 lg:px-8 text-center">
            <h2 className="text-3xl lg:text-4xl font-bold mb-4">
              Ready to put your RTI AI under audit?
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
              Book a walkthrough of the citizen chat and oversight dashboard.
              We&apos;ll show how a single RTI question becomes a transparent,
              scored and reviewable decision trail for your department.
            </p>

            <div className="flex flex-wrap justify-center gap-4">
              <Link href="/login">
                <Button size="lg" className="rounded-full shadow-lg hover:shadow-xl transition-all">
                  View Live Demo
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <Button
                size="lg"
                variant="outline"
                className="rounded-full"
              >
                Download Sample Report
              </Button>
            </div>
          </div>
        </section>

        <Footer />
      </main>
    </>
  );
}