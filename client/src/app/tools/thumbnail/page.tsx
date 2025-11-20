'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, ThumbnailOptions } from '@/types'
import { ArrowLeft, Image } from 'lucide-react'
import Link from 'next/link'

export default function ThumbnailPage() {
  const [file, setFile] = useState<File | null>(null)
  const [timestamp, setTimestamp] = useState('5')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return
    const options: ThumbnailOptions = { timestamp: parseFloat(timestamp), format: 'png', width: 640 }
    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })
    const service = new MediaProcessingService()
    try {
      await service.processJob('thumbnail', file, options, setProgress, (res) => {
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
    a.download = 'thumbnail.png'
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
            <CardTitle className="flex items-center gap-2"><Image className="h-6 w-6" />Thumbnail Generation</CardTitle>
            <CardDescription>Create a thumbnail from your video</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload onFileSelect={setFile} accept="video/*" currentFile={file} />
            {file && !processing && !result && (
              <>
                <div>
                  <Label>Timestamp (seconds)</Label>
                  <Input type="number" placeholder="e.g. 5" value={timestamp} onChange={(e) => setTimestamp(e.target.value)} step="0.1" />
                </div>
                <Button onClick={handleProcess} className="w-full" size="lg">Generate Thumbnail</Button>
              </>
            )}
            {(processing || result) && <ProcessingStatus progress={progress} result={result} onCancel={handleReset} onDownload={handleDownload} onReset={handleReset} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
