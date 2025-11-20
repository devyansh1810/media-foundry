'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, ExtractAudioOptions, AudioFormat } from '@/types'
import { ArrowLeft, Music } from 'lucide-react'
import Link from 'next/link'

export default function ExtractAudioPage() {
  const [file, setFile] = useState<File | null>(null)
  const [format, setFormat] = useState<AudioFormat>('mp3')
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return
    const options: ExtractAudioOptions = { format, bitrate_kbps: 192 }
    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })
    const service = new MediaProcessingService()
    try {
      await service.processJob('extract_audio', file, options, setProgress, (res) => {
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
    a.download = `audio.${format}`
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
            <CardTitle className="flex items-center gap-2"><Music className="h-6 w-6" />Audio Extraction</CardTitle>
            <CardDescription>Extract audio from video in various formats</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <FileUpload onFileSelect={setFile} accept="video/*" currentFile={file} />
            {file && !processing && !result && (
              <>
                <div>
                  <Label>Audio Format</Label>
                  <Select value={format} onValueChange={(v) => setFormat(v as AudioFormat)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="mp3">MP3</SelectItem>
                      <SelectItem value="aac">AAC</SelectItem>
                      <SelectItem value="wav">WAV</SelectItem>
                      <SelectItem value="opus">OPUS</SelectItem>
                      <SelectItem value="m4a">M4A</SelectItem>
                      <SelectItem value="flac">FLAC</SelectItem>
                      <SelectItem value="ogg">OGG</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleProcess} className="w-full" size="lg">Extract Audio</Button>
              </>
            )}
            {(processing || result) && <ProcessingStatus progress={progress} result={result} onCancel={handleReset} onDownload={handleDownload} onReset={handleReset} />}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
