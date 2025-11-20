"use client";
import Link from 'next/link'
import { ArrowRight, Zap, Lock, Video, Wand2, Sparkles, ImageIcon, Minimize2, Music, RefreshCw, Scissors, Film, Sliders, Box } from 'lucide-react'
import { Button } from '@/components/ui/moving-border'
import { Feature } from '@/types'
import { HeroHighlight, Highlight } from '@/components/ui/hero-highlight'
import { BentoGrid, BentoGridItem } from '@/components/ui/bento-grid'
import { Spotlight } from '@/components/ui/spotlight'
import { motion } from 'framer-motion'

const features: Feature[] = [
  {
    id: 'speed',
    title: 'Speed Conversion',
    description: 'Transform playback speed from 0.25x to 10x with intelligent pitch correction',
    icon: 'zap',
    href: '/tools/speed',
    operation: 'speed',
  },
  {
    id: 'compress',
    title: 'Smart Compression',
    description: 'Reduce file size dramatically while preserving visual quality',
    icon: 'minimize',
    href: '/tools/compress',
    operation: 'compress',
  },
  {
    id: 'extract-audio',
    title: 'Audio Extraction',
    description: 'Extract pristine audio to MP3, AAC, WAV, OPUS, FLAC, and more',
    icon: 'music',
    href: '/tools/extract-audio',
    operation: 'extract_audio',
  },
  {
    id: 'convert',
    title: 'Format Conversion',
    description: 'Seamlessly convert between MP4, MKV, WEBM, MOV, and AVI',
    icon: 'repeat',
    href: '/tools/convert',
    operation: 'convert',
  },
  {
    id: 'thumbnail',
    title: 'Thumbnail Generation',
    description: 'Create stunning thumbnails at any moment in your video',
    icon: 'image',
    href: '/tools/thumbnail',
    operation: 'thumbnail',
  },
  {
    id: 'trim',
    title: 'Precision Trim',
    description: 'Extract perfect clips with frame-accurate timing',
    icon: 'scissors',
    href: '/tools/trim',
    operation: 'trim',
  },
  {
    id: 'gif',
    title: 'GIF Creation',
    description: 'Convert video moments into optimized, shareable GIFs',
    icon: 'film',
    href: '/tools/gif',
    operation: 'gif',
  },
  {
    id: 'filters',
    title: 'Advanced Filters',
    description: 'Apply professional filters: scale, rotate, crop, FPS, and more',
    icon: 'sliders',
    href: '/tools/filters',
    operation: 'filter',
  },
]

export default function HomePage() {
  return (
    <div className="flex flex-col relative overflow-hidden">
      {/* Hero Section with Spotlight */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
        <Spotlight
          className="-top-40 left-0 md:left-60 md:-top-20"
          fill="white"
        />
        <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />

        <HeroHighlight>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="container px-4 mx-auto text-center relative z-10"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-border bg-background/50 backdrop-blur-xl mb-8"
            >
              <Sparkles className="h-4 w-4" />
              <span className="text-sm font-medium">Professional Media Processing</span>
            </motion.div>

            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold leading-tight mb-6">
              Transform Your Media
              <br />
              Like Never Before
            </h1>

            <p className="max-w-3xl mx-auto text-lg md:text-xl text-muted-foreground mb-12">
              Experience next-generation media processing. Lightning-fast conversions, pristine quality,
              and professional-grade tools at your fingertips.
            </p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-6"
            >
              <Link href="/tools">
                <Button
                  duration={3000}
                  className="gap-2 px-8"
                >
                  Start Creating <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
            </motion.div>

            {/* Floating Icons Animation */}
            <div className="absolute inset-0 pointer-events-none">
              <motion.div
                animate={{
                  y: [0, -20, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute top-20 left-10 opacity-20"
              >
                <Video className="h-12 w-12" />
              </motion.div>
              <motion.div
                animate={{
                  y: [0, 20, 0],
                }}
                transition={{
                  duration: 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute bottom-20 right-10 opacity-20"
              >
                <ImageIcon className="h-16 w-16" />
              </motion.div>
              <motion.div
                animate={{
                  y: [0, -15, 0],
                }}
                transition={{
                  duration: 3.5,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute top-1/2 right-20 opacity-20"
              >
                <Wand2 className="h-10 w-10" />
              </motion.div>
            </div>
          </motion.div>
        </HeroHighlight>
      </section>

      {/* Features Section with Glassmorphism */}
      <section className="py-24 relative">
        <div className="container px-4 mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Powerful <span className="bg-clip-text text-transparent bg-gradient-to-r from-foreground to-foreground/60">Media Tools</span>
            </h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Everything you need to create, transform, and optimize your media files
            </p>
          </motion.div>

          <BentoGrid>
            {features.map((feature, idx) => (
              <BentoGridItem
                key={feature.id}
                title={feature.title}
                description={feature.description}
                header={
                  <div className="flex items-center justify-center h-full min-h-[6rem] w-full rounded-xl bg-gradient-to-br from-neutral-200 dark:from-neutral-900 via-neutral-100 dark:via-neutral-800 to-neutral-50 dark:to-neutral-900">
                    <motion.div
                      initial={{ scale: 0 }}
                      whileInView={{ scale: 1 }}
                      transition={{ duration: 0.3, delay: idx * 0.1 }}
                      viewport={{ once: true }}
                    >
                      <div className="text-foreground">{getIcon(feature.icon)}</div>
                    </motion.div>
                  </div>
                }
                icon={<ArrowRight className="h-4 w-4 text-neutral-500" />}
                href={feature.href}
                className={idx === 3 || idx === 6 ? "md:col-span-2" : ""}
              />
            ))}
          </BentoGrid>
        </div>
      </section>

      {/* Why Choose Section with Glass Cards */}
      <section className="py-24 relative">
        <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:50px_50px]" />
        <div className="container px-4 mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Why Choose Media Foundry?
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                icon: <Zap className="h-8 w-8" />,
                title: 'Lightning Fast',
                description: 'Optimized processing engine with concurrent job handling for maximum speed',
              },
              {
                icon: <Lock className="h-8 w-8" />,
                title: 'Secure & Private',
                description: 'Your files are processed securely with automatic cleanup. No data retention.',
              },
              {
                icon: <Wand2 className="h-8 w-8" />,
                title: 'Professional Grade',
                description: 'Production-ready tools with comprehensive error handling and type safety',
              },
            ].map((item, idx) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ y: -10, scale: 1.02 }}
                className="group relative"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-primary/5 rounded-2xl blur-xl group-hover:blur-2xl transition-all duration-300" />
                <div className="relative p-8 rounded-2xl border border-border bg-background/50 backdrop-blur-xl h-full">
                  <div className="mb-4 inline-flex p-3 rounded-xl bg-primary/10 text-foreground">
                    {item.icon}
                  </div>
                  <h3 className="text-2xl font-semibold mb-3">{item.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary/5" />
        <Spotlight
          className="top-0 right-0"
          fill="white"
        />
        <div className="container px-4 mx-auto relative z-10">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            viewport={{ once: true }}
            className="max-w-4xl mx-auto text-center"
          >
            <div className="p-12 rounded-3xl border border-border bg-background/30 backdrop-blur-2xl">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">
                Ready to Transform Your Media?
              </h2>
              <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
                Join thousands of creators using professional-grade tools to process their media files
              </p>
              <Link href="/tools">
                <Button
                  duration={3000}
                  className="gap-2 px-8"
                >
                  Get Started Now <ArrowRight className="h-5 w-5" />
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}

function getIcon(icon: string) {
  const iconMap: Record<string, React.ReactNode> = {
    zap: <Zap className="h-12 w-12" />,
    minimize: <Minimize2 className="h-12 w-12" />,
    music: <Music className="h-12 w-12" />,
    repeat: <RefreshCw className="h-12 w-12" />,
    image: <ImageIcon className="h-12 w-12" />,
    scissors: <Scissors className="h-12 w-12" />,
    film: <Film className="h-12 w-12" />,
    sliders: <Sliders className="h-12 w-12" />,
  }
  return iconMap[icon] || <Box className="h-12 w-12" />
}
