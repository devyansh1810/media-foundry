import { ServerMessage, JobProgress, JobResult, OutputMetadata } from '@/types'

export class MediaProcessingService {
  private ws: WebSocket | null = null
  private jobId: string | null = null

  constructor(private wsUrl: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080') {}

  async processJob(
    operation: string,
    inputFile: File | string,
    options: any,
    onProgress?: (progress: JobProgress) => void,
    onComplete?: (result: JobResult) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.wsUrl)
      this.jobId = `job-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

      this.ws.onopen = async () => {
        // Send start job message
        const message = {
          type: 'start_job',
          job_id: this.jobId,
          operation,
          input:
            typeof inputFile === 'string'
              ? { source: 'url', url: inputFile }
              : { source: 'upload' },
          options,
        }

        this.ws?.send(JSON.stringify(message))

        // If file upload, send binary data
        if (typeof inputFile !== 'string') {
          await this.sendBinaryFile(inputFile as File)
        }
      }

      this.ws.onmessage = async (event) => {
        if (event.data instanceof Blob) {
          // Binary message - output file
          const arrayBuffer = await event.data.arrayBuffer()
          const data = new Uint8Array(arrayBuffer)

          // Parse header
          const headerLength = new DataView(data.buffer, 0, 4).getUint32(0, false)
          const headerBytes = data.slice(4, 4 + headerLength)
          const header = JSON.parse(new TextDecoder().decode(headerBytes))
          const fileData = data.slice(4 + headerLength)

          const outputBlob = new Blob([fileData])

          if (onComplete) {
            onComplete({
              success: true,
              outputFile: outputBlob,
              metadata: header.output_metadata,
            })
          }

          resolve()
          this.disconnect()
        } else {
          // JSON message
          const message: ServerMessage = JSON.parse(event.data)

          switch (message.type) {
            case 'ack':
              console.log('Job accepted:', message.message)
              break

            case 'progress':
              if (onProgress && message.percentage !== undefined) {
                onProgress({
                  percentage: message.percentage,
                  stage: message.stage || 'processing',
                  message: message.processing_log,
                })
              }
              break

            case 'completed':
              console.log('Job completed:', message.message)
              // Output file will come as binary message next
              break

            case 'error':
              const error = new Error(message.message || 'Job failed')
              if (onComplete) {
                onComplete({
                  success: false,
                  error: message.message,
                })
              }
              reject(error)
              this.disconnect()
              break
          }
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        reject(new Error('WebSocket connection failed'))
        this.disconnect()
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed')
      }
    })
  }

  private async sendBinaryFile(file: File): Promise<void> {
    if (!this.ws || !this.jobId) return

    const arrayBuffer = await file.arrayBuffer()
    const fileData = new Uint8Array(arrayBuffer)

    // Create header
    const header = {
      job_id: this.jobId,
      filename: file.name,
    }
    const headerJSON = JSON.stringify(header)
    const headerBytes = new TextEncoder().encode(headerJSON)

    // Create binary message: [4 bytes: header length][header JSON][file data]
    const headerLength = headerBytes.length
    const message = new Uint8Array(4 + headerLength + fileData.length)

    // Write header length
    new DataView(message.buffer).setUint32(0, headerLength, false)
    // Write header
    message.set(headerBytes, 4)
    // Write file data
    message.set(fileData, 4 + headerLength)

    this.ws.send(message)
  }

  cancel(): void {
    if (this.ws && this.jobId) {
      const cancelMessage = {
        type: 'cancel_job',
        job_id: this.jobId,
      }
      this.ws.send(JSON.stringify(cancelMessage))
    }
    this.disconnect()
  }

  private disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.jobId = null
  }
}
