'use client'

import React from 'react'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Download, X } from 'lucide-react'
import { JobProgress, JobResult } from '@/types'
import { formatBytes } from '@/lib/utils'

interface ProcessingStatusProps {
  progress: JobProgress | null
  result: JobResult | null
  onCancel: () => void
  onDownload?: () => void
  onReset: () => void
}

export function ProcessingStatus({
  progress,
  result,
  onCancel,
  onDownload,
  onReset,
}: ProcessingStatusProps) {
  if (result) {
    if (result.success) {
      return (
        <div className="space-y-4 rounded-lg border border-border bg-card p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-green-600 dark:text-green-400">
              ✓ Processing Complete
            </h3>
            <Button variant="ghost" size="icon" onClick={onReset}>
              <X className="h-4 w-4" />
            </Button>
          </div>

          {result.metadata && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Format:</span>
                <span className="font-medium">{result.metadata.format}</span>
              </div>
              {result.metadata.duration && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Duration:</span>
                  <span className="font-medium">
                    {result.metadata.duration.toFixed(2)}s
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Size:</span>
                <span className="font-medium">
                  {formatBytes(result.metadata.size_bytes)}
                </span>
              </div>
              {result.metadata.width && result.metadata.height && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Resolution:</span>
                  <span className="font-medium">
                    {result.metadata.width}×{result.metadata.height}
                  </span>
                </div>
              )}
            </div>
          )}

          {onDownload && (
            <Button onClick={onDownload} className="w-full gap-2">
              <Download className="h-4 w-4" />
              Download Result
            </Button>
          )}
        </div>
      )
    } else {
      return (
        <div className="space-y-4 rounded-lg border border-destructive bg-destructive/10 p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-destructive">
              ✗ Processing Failed
            </h3>
            <Button variant="ghost" size="icon" onClick={onReset}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">{result.error}</p>
          <Button onClick={onReset} variant="outline" className="w-full">
            Try Again
          </Button>
        </div>
      )
    }
  }

  if (progress) {
    return (
      <div className="space-y-4 rounded-lg border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Processing...</h3>
          <Button variant="ghost" size="icon" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground capitalize">
              {progress.stage}
            </span>
            <span className="font-medium">{progress.percentage.toFixed(1)}%</span>
          </div>
          <Progress value={progress.percentage} />
        </div>

        {progress.message && (
          <p className="text-xs text-muted-foreground">{progress.message}</p>
        )}
      </div>
    )
  }

  return null
}
