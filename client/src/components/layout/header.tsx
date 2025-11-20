'use client'

import Link from 'next/link'
import { Film } from 'lucide-react'
import { ThemeToggle } from './theme-toggle'
import { Button } from '@/components/ui/button'

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center space-x-2">
          <Film className="h-6 w-6" />
          <span className="text-xl font-bold">Media Foundry</span>
        </Link>

        <nav className="hidden md:flex items-center space-x-6">
          <Link
            href="/#features"
            className="text-sm font-medium transition-colors hover:text-primary"
          >
            Features
          </Link>
          <Link
            href="/tools"
            className="text-sm font-medium transition-colors hover:text-primary"
          >
            Tools
          </Link>
          <Link
            href="/#about"
            className="text-sm font-medium transition-colors hover:text-primary"
          >
            About
          </Link>
        </nav>

        <div className="flex items-center space-x-2">
          <ThemeToggle />
          <Button asChild>
            <Link href="/tools">Get Started</Link>
          </Button>
        </div>
      </div>
    </header>
  )
}
