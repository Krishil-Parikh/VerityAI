'use client';

import React from "react"

import { useState, useEffect } from 'react';
import { useAuth } from '@/store/authContext';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { AlertCircle, Loader2 } from 'lucide-react';
import Image from "next/image";

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login, user, isAuthenticated, loading } = useAuth();
  const router = useRouter();

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && isAuthenticated && user) {
      const redirectPath = user.role === 'admin' ? '/admin' : '/citizen';
      router.push(redirectPath);
    }
  }, [loading, isAuthenticated, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      // Redirect based on role after login
      const isAdmin = email === 'admin@example.com';
      router.push(isAdmin ? '/admin' : '/citizen');
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Invalid email or password'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md border shadow-lg">
        <div className="p-8">
          <div className="mb-8 flex justify-center">
            <Image
              src="/icon.png"
              alt="VerityAI Logo"
              width={200}
              height={60}
              className="h-24 w-auto object-contain"
              priority
            />
            {/* <h1 className="text-3xl font-bold text-foreground mb-2">
              VerityAI
            </h1> */}
            {/* <p className="text-muted-foreground">RTI Information Portal</p> */}
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium mb-2"
              >
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-destructive">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                <p className="text-sm">{error}</p>
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
