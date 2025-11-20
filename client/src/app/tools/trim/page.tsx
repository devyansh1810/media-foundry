'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, TrimOptions } from '@/types'
import { ArrowLeft, Scissors } from 'lucide-react'
import Link from 'next/link'

export default function TrimPage() {
  const [file, setFile] = useState<File | null>(null)
  const [startTime, setStartTime] = useState('0')
  const [endTime, setEndTime] = useState('10')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return
    const options: TrimOptions = { start_time: parseFloat(startTime), end_time: parseFloat(endTime) }
    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })
    const service = new MediaProcessingService()
    try {
      await service.processJob('trim', file, options, setProgress, (res) => {
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
    a.download = `trimmed-${file?.name || 'output.mp4'}`
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
            <CardTitle className="flex items-center gap-2"><Scissors className="h-6 w-6" />Trim & Clip</CardTitle>
            <CardDescription>Extract a clip from your video with precise timing</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload onFileSelect={setFile} accept="video/*" currentFile={file} />
            {file && !processing && !result && (
              <>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label>Start Time (seconds)</Label>
                    <Input type="number" value={startTime} onChange={(e) => setStartTime(e.target.value)} step="0.1" />
                  </div>
                  <div>
                    <Label>End Time (seconds)</Label>
                    <Input type="number" value={endTime} onChange={(e) => setEndTime(e.target.value)} step="0.1" />
                  </div>
                </div>
                <Button onClick={handleProcess} className="w-full" size="lg">Trim Video</Button>
              </>
            )}
            {(processing || result) && <ProcessingStatus progress={progress} result={result} onCancel={handleReset} onDownload={handleDownload} onReset={handleReset} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
