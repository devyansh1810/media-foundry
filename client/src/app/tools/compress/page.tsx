'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, CompressionOptions, CompressionPreset } from '@/types'
import { ArrowLeft, Minimize2 } from 'lucide-react'
import Link from 'next/link'

export default function CompressionPage() {
  const [file, setFile] = useState<File | null>(null)
  const [preset, setPreset] = useState<CompressionPreset>('medium')
  const [maxWidth, setMaxWidth] = useState<string>('')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return

    const options: CompressionOptions = {
      preset,
      max_width: maxWidth ? parseInt(maxWidth) : undefined,
    }

    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })

    const service = new MediaProcessingService()

    try {
      await service.processJob('compress', file, options, setProgress, (res) => {
        setResult(res)
        setProcessing(false)
      })
    } catch (error) {
      setResult({ success: false, error: (error as Error).message })
      setProcessing(false)
    }
  }

  const handleDownload = () => {
    if (!result?.outputFile) return
    const url = URL.createObjectURL(result.outputFile)
    const a = document.createElement('a')
    a.href = url
    a.download = `compressed-${file?.name || 'output.mp4'}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleReset = () => {
    setFile(null)
    setProgress(null)
    setResult(null)
    setProcessing(false)
  }

  return (
    <div className="container px-4 py-16">
      <div className="mx-auto max-w-2xl">
        <Link href="/tools" className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" />Back to Tools
        </Link>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Minimize2 className="h-6 w-6" />Video Compression</CardTitle>
            <CardDescription>Reduce file size with quality presets</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload onFileSelect={setFile} accept="video/*" currentFile={file} />
            {file && !processing && !result && (
              <>
                <div className="space-y-4">
                  <div>
                    <Label>Quality Preset</Label>
                    <Select value={preset} onValueChange={(v) => setPreset(v as CompressionPreset)}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low (Smallest file)</SelectItem>
                        <SelectItem value="medium">Medium (Balanced)</SelectItem>
                        <SelectItem value="high">High (Best quality)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Max Width (optional)</Label>
                    <Input type="number" placeholder="e.g. 1280" value={maxWidth} onChange={(e) => setMaxWidth(e.target.value)} />
                  </div>
                </div>
                <Button onClick={handleProcess} className="w-full" size="lg">Compress Video</Button>
              </>
            )}
            {(processing || result) && <ProcessingStatus progress={progress} result={result} onCancel={handleReset} onDownload={handleDownload} onReset={handleReset} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
