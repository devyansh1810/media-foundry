'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { FileUpload } from '@/components/shared/file-upload'
import { ProcessingStatus } from '@/components/shared/processing-status'
import { MediaProcessingService } from '@/services/websocket'
import { JobProgress, JobResult, SpeedOptions } from '@/types'
import { ArrowLeft, Zap } from 'lucide-react'
import Link from 'next/link'

export default function SpeedConversionPage() {
  const [file, setFile] = useState<File | null>(null)
  const [speedFactor, setSpeedFactor] = useState<number>(2.0)
  const [maintainPitch, setMaintainPitch] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<JobProgress | null>(null)
  const [result, setResult] = useState<JobResult | null>(null)

  const handleProcess = async () => {
    if (!file) return

    const options: SpeedOptions = {
      speed_factor: speedFactor,
      maintain_pitch: maintainPitch,
    }

    setProcessing(true)
    setProgress({ percentage: 0, stage: 'starting' })

    const service = new MediaProcessingService()

    try {
      await service.processJob(
        'speed',
        file,
        options,
        (prog) => setProgress(prog),
        (res) => {
          setResult(res)
          setProcessing(false)
        }
      )
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Processing failed',
      })
      setProcessing(false)
    }
  }

  const handleDownload = () => {
    if (!result?.outputFile) return

    const url = URL.createObjectURL(result.outputFile)
    const a = document.createElement('a')
    a.href = url
    a.download = `speed-${speedFactor}x-${file?.name || 'output.mp4'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
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
        <Link
          href="/tools"
          className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Tools
        </Link>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-6 w-6" />
              Speed Conversion
            </CardTitle>
            <CardDescription>
              Change video playback speed from 0.25x to 10x with optional pitch correction
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label>Upload Video</Label>
              <div className="mt-2">
                <FileUpload
                  onFileSelect={setFile}
                  accept="video/*"
                  currentFile={file}
                />
              </div>
            </div>

            {file && !processing && !result && (
              <>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <Label>Speed Factor: {speedFactor}x</Label>
                      <span className="text-sm text-muted-foreground">
                        {speedFactor < 1 ? 'Slower' : speedFactor > 1 ? 'Faster' : 'Normal'}
                      </span>
                    </div>
                    <Slider
                      value={[speedFactor]}
                      onValueChange={([value]) => setSpeedFactor(value)}
                      min={0.25}
                      max={10}
                      step={0.25}
                      className="w-full"
                    />
                    <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                      <span>0.25x</span>
                      <span>10x</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <Label htmlFor="maintain-pitch">Maintain Pitch</Label>
                      <p className="text-sm text-muted-foreground">
                        Preserve audio pitch when changing speed
                      </p>
                    </div>
                    <Switch
                      id="maintain-pitch"
                      checked={maintainPitch}
                      onCheckedChange={setMaintainPitch}
                    />
                  </div>
                </div>

                <Button onClick={handleProcess} className="w-full" size="lg">
                  Process Video
                </Button>
              </>
            )}

            {(processing || result) && (
              <ProcessingStatus
                progress={progress}
                result={result}
                onCancel={handleReset}
                onDownload={handleDownload}
                onReset={handleReset}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
