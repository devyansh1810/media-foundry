export type JobOperation =
  | 'speed'
  | 'compress'
  | 'extract_audio'
  | 'remove_audio'
  | 'convert'
  | 'thumbnail'
  | 'trim'
  | 'concat'
  | 'gif'
  | 'filter'

export type AudioFormat = 'mp3' | 'aac' | 'wav' | 'opus' | 'm4a' | 'flac' | 'ogg'
export type VideoFormat = 'mp4' | 'mov' | 'mkv' | 'webm' | 'avi' | 'flv'
export type ImageFormat = 'png' | 'jpeg' | 'jpg'
export type CompressionPreset = 'low' | 'medium' | 'high' | 'custom'

export interface OutputMetadata {
  format: string
  duration?: number
  size_bytes: number
  video_codec?: string
  audio_codec?: string
  width?: number
  height?: number
  bitrate?: number
  fps?: number
}

export interface ServerMessage {
  type: 'ack' | 'progress' | 'completed' | 'error' | 'pong'
  job_id?: string
  message?: string
  percentage?: number
  stage?: string
  processing_log?: string
  output_metadata?: OutputMetadata
  delivery_method?: 'binary'
  code?: string
  details?: string
}

export interface JobProgress {
  percentage: number
  stage: string
  message?: string
}

export interface JobResult {
  success: boolean
  metadata?: OutputMetadata
  outputFile?: Blob
  error?: string
}

// Feature interfaces
export interface SpeedOptions {
  speed_factor: number
  maintain_pitch: boolean
}

export interface CompressionOptions {
  preset: CompressionPreset
  video_bitrate_kbps?: number
  audio_bitrate_kbps?: number
  crf?: number
  max_width?: number
  max_height?: number
  target_format?: VideoFormat
}

export interface ExtractAudioOptions {
  format: AudioFormat
  bitrate_kbps?: number
  sample_rate?: number
}

export interface RemoveAudioOptions {
  keep_video_quality: boolean
}

export interface ConvertOptions {
  target_format: string
  stream_copy: boolean
  video_codec?: string
  audio_codec?: string
}

export interface ThumbnailOptions {
  timestamp?: number
  count?: number
  format: ImageFormat
  width?: number
  height?: number
}

export interface TrimOptions {
  start_time: number
  end_time: number
}

export interface GifOptions {
  start_time: number
  duration: number
  fps: number
  width?: number
  optimize: boolean
}

export interface FilterOptions {
  filters: Array<{
    type: 'scale' | 'rotate' | 'crop' | 'fps' | 'volume' | 'normalize'
    [key: string]: any
  }>
}

export interface Feature {
  id: string
  title: string
  description: string
  icon: string
  href: string
  operation: JobOperation
}
