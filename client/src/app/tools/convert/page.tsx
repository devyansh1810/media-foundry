'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, ConvertOptions } from '@/types'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import Link from 'next/link'

export default function ConvertPage() {
  const [file, setFile] = useState<File | null>(null)
  const [targetFormat, setTargetFormat] = useState('mp4')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return
    const options: ConvertOptions = { target_format: targetFormat, stream_copy: true }
    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })
    const service = new MediaProcessingService()
    try {
      await service.processJob('convert', file, options, setProgress, (res) => {
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
    a.download = `converted.${targetFormat}`
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
            <CardTitle className="flex items-center gap-2"><RefreshCw className="h-6 w-6" />Format Conversion</CardTitle>
            <CardDescription>Convert between video formats</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload onFileSelect={setFile} accept="video/*" currentFile={file} />
            {file && !processing && !result && (
              <>
                <div>
                  <Label>Target Format</Label>
                  <Select value={targetFormat} onValueChange={setTargetFormat}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mp4">MP4</SelectItem>
                      <SelectItem value="mkv">MKV</SelectItem>
                      <SelectItem value="webm">WEBM</SelectItem>
                      <SelectItem value="mov">MOV</SelectItem>
                      <SelectItem value="avi">AVI</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleProcess} className="w-full" size="lg">Convert Video</Button>
              </>
            )}
            {(processing || result) && <ProcessingStatus progress={progress} result={result} onCancel={handleReset} onDownload={handleDownload} onReset={handleReset} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
