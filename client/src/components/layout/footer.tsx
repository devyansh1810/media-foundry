import Link from 'next/link'
import { Film, Github } from 'lucide-react'

export function Footer() {
  return (
    <footer className="w-full border-t bg-background">
      <div className="container py-8 md:py-12">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          <div className="space-y-3">
            <Link href="/" className="flex items-center space-x-2">
              <Film className="h-5 w-5" />
              <span className="font-bold">Media Foundry</span>
            </Link>
            <p className="text-sm text-muted-foreground">
              Professional media processing tools
            </p>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold">Features</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/tools/speed"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Speed Conversion
                </Link>
              </li>
              <li>
                <Link
                  href="/tools/compress"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Compression
                </Link>
              </li>
              <li>
                <Link
                  href="/tools/extract-audio"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Audio Extraction
                </Link>
              </li>
              <li>
                <Link
                  href="/tools/convert"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Format Conversion
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold">Resources</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/#about"
                  className="text-muted-foreground hover:text-foreground"
                >
                  About
                </Link>
              </li>
              <li>
                <Link
                  href="/#features"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Features
                </Link>
              </li>
              <li>
                <a
                  href="https://github.com"
                  className="text-muted-foreground hover:text-foreground"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Documentation
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold">Connect</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <a
                  href="https://github.com"
                  className="flex items-center space-x-2 text-muted-foreground hover:text-foreground"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <Github className="h-4 w-4" />
                  <span>GitHub</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t pt-8 text-center text-sm text-muted-foreground">
          <p>© 2024 Media Foundry. Built with cutting-edge technology.</p>
        </div>
      </div>
    </footer>
  )
}
