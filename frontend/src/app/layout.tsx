import './globals.css';
import React from 'react';
import Link from 'next/link';
import { NavigationRail } from '@/components/NavigationRail';

export const metadata = {
  title: 'Retrieval Lens — Google Photos Discovery Engine',
  description: 'AI Analysis of public user feedback on photo retrieval failures in Google Photos',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body className="bg-surface-bg font-body text-on-surface antialiased selection:bg-google-blue-tint selection:text-primary-container">
        {/* Fixed Top Shell */}
        <div className="fixed top-0 left-0 right-0 z-50 flex flex-col">
          {/* Main Top Bar */}
          <header className="h-16 w-full bg-surface-card border-b border-border-subtle flex items-center justify-between px-6 shadow-sm">
            {/* Logo */}
            <div className="flex items-center gap-3">
              {/* Google Photos Pinwheel Logo SVG */}
              <svg className="h-8 w-8" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 20C20 14.477 15.523 10 10 10C4.477 10 0 14.477 0 20C0 20 20 20 20 20Z" fill="#4285F4"/>
                <path d="M20 20C25.523 20 30 15.523 30 10C30 4.477 25.523 0 20 0C20 0 20 20 20 20Z" fill="#EA4335"/>
                <path d="M20 20C20 25.523 24.477 30 30 30C35.523 30 40 25.523 40 20C40 20 20 20 20 20Z" fill="#FBBC04"/>
                <path d="M20 20C14.477 20 10 24.477 10 30C10 35.523 14.477 40 20 40C20 40 20 20 20 20Z" fill="#34A853"/>
              </svg>
              <span className="font-headline text-xl text-on-surface tracking-tight font-semibold">Retrieval Lens</span>
              <span className="ml-1 px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant text-[11px] font-medium uppercase tracking-wider">
                Research View
              </span>
            </div>

            {/* Header Right Actions */}
            <div className="flex items-center gap-4">
              <a
                href="http://localhost:8000/api/export"
                download="retrieval_lens_analysis_bundle.json"
                className="h-9 px-4 rounded-full border border-border-subtle bg-surface-card text-on-surface text-sm font-medium flex items-center gap-2 hover:bg-surface-container transition-colors shadow-sm"
              >
                <span className="material-symbols-outlined text-[18px] text-on-surface-variant">download</span>
                <span>Download full analysis</span>
              </a>
            </div>
          </header>
        </div>

        {/* Left Navigation Rail */}
        <NavigationRail />

        {/* Main View Area */}
        <div className="pl-60">
          <main className="pt-20 min-h-screen bg-surface-bg p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
