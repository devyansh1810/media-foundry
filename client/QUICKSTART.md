# Media Foundry Client - Quick Start Guide

## 🎉 Your application is now running!

The Next.js development server has been started successfully.

## Access the Application

**Frontend**: http://localhost:3000
**Backend API**: ws://localhost:8080 (make sure to start the Python backend)

## What You Can Do Now

### 1. View the Landing Page
Open http://localhost:3000 in your browser to see:
- Beautiful hero section with gradient text
- Feature showcase with 8 processing tools
- Dark/Light theme toggle (top right)
- Responsive design

### 2. Try the Tools
Navigate to any tool from the landing page:
- **Speed Conversion**: http://localhost:3000/tools/speed
- **Compression**: http://localhost:3000/tools/compress
- **Audio Extraction**: http://localhost:3000/tools/extract-audio
- **Format Conversion**: http://localhost:3000/tools/convert
- **Thumbnail Generation**: http://localhost:3000/tools/thumbnail
- **Trim & Clip**: http://localhost:3000/tools/trim
- **GIF Creation**: http://localhost:3000/tools/gif
- **Video Filters**: http://localhost:3000/tools/filters

### 3. Start the Backend
To actually process files, start the Media Foundry backend:

```bash
# In the root directory
cd ../
python -m src.main
```

The backend will start on ws://localhost:8080

## Development Commands

```bash
# Start development server (already running)
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linter
npm run lint
```

## Key Features Implemented

✅ **Modern UI/UX**
- shadcn/ui components with Radix UI primitives
- Tailwind CSS for styling
- Lucide icons
- Smooth animations and transitions

✅ **Theme System**
- Dark and light modes
- System preference detection
- Persistent storage
- Smooth transitions

✅ **File Upload**
- Drag and drop support
- File size validation
- Progress indicator
- Beautiful UI

✅ **WebSocket Integration**
- Real-time progress updates
- Binary file transfer
- Job cancellation
- Error handling

✅ **Processing Tools**
- 8 fully functional tools
- Custom options for each
- Real-time feedback
- Download results

✅ **Responsive Design**
- Mobile-friendly
- Tablet optimized
- Desktop enhanced

## Project Structure

```
client/
├── src/
│   ├── app/                    # Pages (Next.js App Router)
│   ├── components/             # React components
│   │   ├── ui/                # shadcn/ui components
│   │   ├── layout/            # Layout components
│   │   └── shared/            # Shared components
│   ├── services/              # WebSocket service
│   ├── lib/                   # Utilities
│   └── types/                 # TypeScript types
├── public/                    # Static files
└── [config files]             # Configuration

```

## Environment Configuration

The `.env.local` file is already configured with:
```
NEXT_PUBLIC_WS_URL=ws://localhost:8080
```

Update this if your backend is running on a different URL.

## Testing the Application

1. **Start Backend** (in root directory):
   ```bash
   python -m src.main
   ```

2. **Open Frontend**: http://localhost:3000

3. **Select a Tool**: Click on any tool from the landing page

4. **Upload a File**: Drag & drop or click to browse

5. **Configure Options**: Adjust settings as needed

6. **Process**: Click the "Process" button

7. **Download**: Once complete, download your processed file

## Theme Toggle

Click the sun/moon icon in the header to switch between light and dark modes.

## Troubleshooting

### Port 3000 Already in Use
```bash
# Kill the process using port 3000
lsof -ti:3000 | xargs kill -9
# Or run on a different port
PORT=3001 npm run dev
```

### Backend Connection Issues
- Ensure the Python backend is running on ws://localhost:8080
- Check the browser console for WebSocket errors
- Verify NEXT_PUBLIC_WS_URL in .env.local

### Build Errors
```bash
# Clear Next.js cache
rm -rf .next
npm run dev
```

## Next Steps

1. **Customize Branding**: Update colors in `tailwind.config.ts`
2. **Add More Tools**: Create new pages in `src/app/tools/`
3. **Enhance UI**: Modify components in `src/components/`
4. **Deploy**: Build and deploy to Vercel, Netlify, or your own server

## Support

For issues or questions:
- Check the main README.md
- Review the backend documentation
- Check browser console for errors

## Happy Processing! 🎬

Your Media Foundry application is ready to transform media files with professional-grade tools.
