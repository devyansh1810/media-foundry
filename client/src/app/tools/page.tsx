import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ArrowRight, Zap, Minimize2, Music, RefreshCw, Image, Scissors, Film, Sliders } from 'lucide-react'

const tools = [
  {
    id: 'speed',
    title: 'Speed Conversion',
    description: 'Change video playback speed (0.25x - 10x) with pitch correction',
    icon: Zap,
    href: '/tools/speed',
  },
  {
    id: 'compress',
    title: 'Video Compression',
    description: 'Reduce file size with quality presets',
    icon: Minimize2,
    href: '/tools/compress',
  },
  {
    id: 'extract-audio',
    title: 'Audio Extraction',
    description: 'Extract audio to MP3, AAC, WAV, OPUS, and more',
    icon: Music,
    href: '/tools/extract-audio',
  },
  {
    id: 'convert',
    title: 'Format Conversion',
    description: 'Convert between video formats',
    icon: RefreshCw,
    href: '/tools/convert',
  },
  {
    id: 'thumbnail',
    title: 'Thumbnail Generation',
    description: 'Create thumbnails from videos',
    icon: Image,
    href: '/tools/thumbnail',
  },
  {
    id: 'trim',
    title: 'Trim & Clip',
    description: 'Extract clips with precise timing',
    icon: Scissors,
    href: '/tools/trim',
  },
  {
    id: 'gif',
    title: 'GIF Creation',
    description: 'Convert video segments to GIFs',
    icon: Film,
    href: '/tools/gif',
  },
  {
    id: 'filters',
    title: 'Video Filters',
    description: 'Apply filters and transformations',
    icon: Sliders,
    href: '/tools/filters',
  },
]

export default function ToolsPage() {
  return (
    <div className="container px-4 py-20">
      <div className="mx-auto max-w-6xl">
        {/* Header Section */}
        <div className="mb-16 space-y-4 text-center">
          <div className="inline-block rounded-lg border bg-muted px-3 py-1 text-sm font-medium">
            All Tools
          </div>
          <h1 className="text-5xl font-bold tracking-tight">
            Media Processing Tools
          </h1>
          <p className="mx-auto max-w-2xl text-xl text-muted-foreground">
            Professional FFmpeg-powered tools for video, audio, and image processing
          </p>
        </div>

        {/* Tools Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {tools.map((tool) => (
            <Link key={tool.id} href={tool.href} className="group">
              <Card className="h-full border-2 transition-all duration-300 hover:border-foreground hover:shadow-lg">
                <CardHeader className="space-y-4 pb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg border-2 bg-background transition-all duration-300 group-hover:scale-110 group-hover:border-foreground">
                    <tool.icon className="h-6 w-6" />
                  </div>
                  <div className="space-y-2">
                    <CardTitle className="text-xl font-semibold leading-tight">
                      {tool.title}
                    </CardTitle>
                    <CardDescription className="text-sm leading-relaxed">
                      {tool.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2 text-sm font-medium transition-all group-hover:gap-3">
                    <span>Open Tool</span>
                    <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        {/* Footer Info */}
        <div className="mt-16 rounded-lg border bg-muted/50 p-6 text-center">
          <p className="text-sm text-muted-foreground">
            All processing happens securely via WebSocket connection to your local FFmpeg service
          </p>
        </div>
      </div>
    </div>
  )
}
