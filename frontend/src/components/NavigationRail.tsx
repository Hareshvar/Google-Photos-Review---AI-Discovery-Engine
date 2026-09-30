'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function NavigationRail() {
  const pathname = usePathname();

  const navItems = [
    { href: '/overview', label: 'Overview', icon: 'explore' },
    { href: '/themes', label: 'Themes', icon: 'bubble_chart' },
    { href: '/situations', label: 'Situations', icon: 'table_chart' },
    { href: '/insights', label: 'Key Insights', icon: 'lightbulb' },
    { href: '/ask-data', label: 'Ask the data', icon: 'chat' },
    { href: '/method', label: 'Method and limits', icon: 'tune' },
    { href: '/quality', label: 'Quality Audit', icon: 'fact_check' },
  ];

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-60 bg-surface-card border-r border-border-subtle z-40 flex flex-col py-4 px-3 shadow-sm">
      <nav className="flex flex-col gap-1 w-full">
        {navItems.map((item) => {
          const isActive = pathname === item.href || (pathname === '/' && item.href === '/overview');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-full text-sm font-medium transition-all ${
                isActive
                  ? 'bg-google-blue-tint text-primary-container font-semibold shadow-sm border border-[#d2e3fc]'
                  : 'text-on-secondary-container hover:bg-surface-container hover:text-on-surface'
              }`}
            >
              <span className={`material-symbols-outlined text-[20px] ${isActive ? 'text-primary-container font-bold' : ''}`}>
                {item.icon}
              </span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Dataset Status Box at Bottom */}
      <div className="mt-auto p-3 bg-surface-bg rounded-xl border border-border-subtle">
        <div className="flex items-center gap-2 mb-1">
          <span className="material-symbols-outlined text-tertiary text-[16px]">verified</span>
          <span className="text-xs font-semibold text-on-surface">Corpus v2.0 Active</span>
        </div>
        <p className="text-xs text-on-surface-variant leading-snug">
          Code-verified tags • N=9,737 relevant
        </p>
      </div>
    </aside>
  );
}
