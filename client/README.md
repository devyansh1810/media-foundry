# Media Foundry - Client

Modern, responsive Next.js frontend for the Media Foundry media processing service.

## Features

- ✅ **Beautiful Landing Page** with hero section and feature showcase
- ✅ **Dark/Light Theme Toggle** with system preference detection
- ✅ **8 Processing Tools**:
  - Speed Conversion (0.25x - 10x with pitch correction)
  - Video Compression (quality presets)
  - Audio Extraction (MP3, AAC, WAV, OPUS, M4A, FLAC, OGG)
  - Format Conversion (MP4, MKV, WEBM, MOV, AVI)
  - Thumbnail Generation
  - Trim & Clip
  - GIF Creation
  - Video Filters
- ✅ **Real-time Progress Tracking** via WebSocket
- ✅ **File Upload with Drag & Drop**
- ✅ **Responsive Design** - works on desktop and mobile
- ✅ **Type-safe** with TypeScript
- ✅ **Modern UI** with shadcn/ui and Radix UI components

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui + Radix UI
- **Icons**: Lucide React
- **Theme**: next-themes

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Media Foundry backend running on `ws://localhost:8080`

### Installation

1. **Install dependencies**:

```bash
cd client
npm install
# or
bun install
```

2. **Configure environment**:

```bash
# .env.local is already created with default settings
# Update NEXT_PUBLIC_WS_URL if your backend is on a different URL
```

3. **Run development server**:

```bash
npm run dev
# or
bun dev
```

4. **Open in browser**:

```
http://localhost:3000
```

## Project Structure

```
client/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── layout.tsx            # Root layout with theme provider
│   │   ├── page.tsx              # Landing page
│   │   ├── globals.css           # Global styles
│   │   └── tools/                # Tool pages
│   │       ├── page.tsx          # Tools index
│   │       ├── speed/            # Speed conversion
│   │       ├── compress/         # Compression
│   │       ├── extract-audio/    # Audio extraction
│   │       ├── convert/          # Format conversion
│   │       ├── thumbnail/        # Thumbnail generation
│   │       ├── trim/             # Trim & clip
│   │       ├── gif/              # GIF creation
│   │       └── filters/          # Video filters
│   │
│   ├── components/
│   │   ├── ui/                   # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   ├── progress.tsx
│   │   │   ├── select.tsx
│   │   │   ├── slider.tsx
│   │   │   ├── switch.tsx
│   │   │   └── tabs.tsx
│   │   ├── layout/               # Layout components
│   │   │   ├── header.tsx
│   │   │   ├── footer.tsx
│   │   │   ├── theme-provider.tsx
│   │   │   └── theme-toggle.tsx
│   │   └── shared/               # Shared components
│   │       ├── file-upload.tsx
│   │       └── processing-status.tsx
│   │
│   ├── services/
│   │   └── websocket.ts          # WebSocket service for backend communication
│   │
│   ├── lib/
│   │   └── utils.ts              # Utility functions
│   │
│   └── types/
│       └── index.ts              # TypeScript type definitions
│
├── public/                        # Static assets
├── package.json                   # Dependencies
├── tsconfig.json                  # TypeScript config
├── tailwind.config.ts             # Tailwind CSS config
├── next.config.js                 # Next.js config
└── postcss.config.js              # PostCSS config
```

## Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

## Features Breakdown

### Landing Page
- Hero section with gradient text
- Feature showcase with 8 tools
- "Why Choose" section highlighting benefits
- Technical features list
- Call-to-action sections
- Responsive design

### Tool Pages
Each tool page includes:
- File upload with drag & drop
- Tool-specific options
- Real-time progress tracking
- Result preview with metadata
- Download functionality
- Error handling
- Reset/retry capability

### Theme System
- Light and dark modes
- System preference detection
- Smooth transitions
- Persistent preference storage

### WebSocket Integration
- Real-time communication with backend
- Progress updates
- Binary file transfer
- Error handling
- Job cancellation

## Environment Variables

```env
NEXT_PUBLIC_WS_URL=ws://localhost:8080
```

## Building for Production

```bash
npm run build
npm run start
```

Or with Docker:

```bash
docker build -t media-foundry-client .
docker run -p 3000:3000 media-foundry-client
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT

## Credits

Built with:
- [Next.js](https://nextjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Radix UI](https://www.radix-ui.com/)
- [Lucide Icons](https://lucide.dev/)
