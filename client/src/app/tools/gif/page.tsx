'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, GifOptions } from '@/types'
import { ArrowLeft, Film } from 'lucide-react'
import Link from 'next/link'

export default function GifPage() {
  const [file, setFile] = useState<File | null>(null)
  const [startTime, setStartTime] = useState('0')
  const [duration, setDuration] = useState('5')
  const [fps, setFps] = useState(10)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return
    const options: GifOptions = { start_time: parseFloat(startTime), duration: parseFloat(duration), fps, optimize: true }
    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })
    const service = new MediaProcessingService()
    try {
      await service.processJob('gif', file, options, setProgress, (res) => {
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
    a.download = 'output.gif'
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
            <CardTitle className="flex items-center gap-2"><Film className="h-6 w-6" />GIF Creation</CardTitle>
            <CardDescription>Convert video segments to optimized GIFs</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload onFileSelect={setFile} accept="video/*" currentFile={file} />
            {file && !processing && !result && (
              <>
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label>Start Time (seconds)</Label>
                      <Input type="number" value={startTime} onChange={(e) => setStartTime(e.target.value)} step="0.1" />
                    </div>
                    <div>
                      <Label>Duration (seconds)</Label>
                      <Input type="number" value={duration} onChange={(e) => setDuration(e.target.value)} step="0.1" max="30" />
                    </div>
                  </div>
                  <div>
                    <Label>FPS: {fps}</Label>
                    <Slider value={[fps]} onValueChange={([v]) => setFps(v)} min={1} max={30} step={1} />
                  </div>
                </div>
                <Button onClick={handleProcess} className="w-full" size="lg">Create GIF</Button>
              </>
            )}
            {(processing || result) && <ProcessingStatus progress={progress} result={result} onCancel={handleReset} onDownload={handleDownload} onReset={handleReset} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
