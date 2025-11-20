"""Pydantic models for WebSocket protocol"""

from enum import Enum
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, field_validator


# Enums
class JobOperation(str, Enum):
    """Supported FFmpeg operations"""

    SPEED = "speed"
    COMPRESS = "compress"
    EXTRACT_AUDIO = "extract_audio"
    REMOVE_AUDIO = "remove_audio"
    CONVERT = "convert"
    THUMBNAIL = "thumbnail"
    TRIM = "trim"
    CONCAT = "concat"
    GIF = "gif"
    FILTER = "filter"
    EXTRACT_SUBTITLES = "extract_subtitles"
    BURN_SUBTITLES = "burn_subtitles"


class CompressionPreset(str, Enum):
    """Video compression quality presets"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CUSTOM = "custom"


class FilterType(str, Enum):
    """Available filter types"""

    SCALE = "scale"
    ROTATE = "rotate"
    CROP = "crop"
    FPS = "fps"
    VOLUME = "volume"
    NORMALIZE = "normalize"


class AudioFormat(str, Enum):
    """Supported audio formats"""

    MP3 = "mp3"
    AAC = "aac"
    WAV = "wav"
    OPUS = "opus"
    M4A = "m4a"
    FLAC = "flac"
    OGG = "ogg"


class VideoFormat(str, Enum):
    """Supported video formats"""

    MP4 = "mp4"
    MOV = "mov"
    MKV = "mkv"
    WEBM = "webm"
    AVI = "avi"
    FLV = "flv"


class ImageFormat(str, Enum):
    """Supported image formats"""

    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


# Input Source Models
class UploadSource(BaseModel):
    """Upload source for binary data"""

    source: Literal["upload"] = "upload"


class UrlSource(BaseModel):
    """URL source for downloading"""

    source: Literal["url"] = "url"
    url: HttpUrl


InputSource = Union[UploadSource, UrlSource]


# Operation-Specific Options
class SpeedOptions(BaseModel):
    """Options for speed conversion"""

    speed_factor: float = Field(gt=0.25, le=10.0, description="Speed multiplier (0.25x - 10x)")
    maintain_pitch: bool = Field(default=False, description="Maintain audio pitch when changing speed")


class CompressionOptions(BaseModel):
    """Options for compression/size reduction"""

    preset: CompressionPreset = Field(default=CompressionPreset.MEDIUM)
    video_bitrate_kbps: Optional[int] = Field(default=None, gt=0, description="Video bitrate in kbps")
    audio_bitrate_kbps: Optional[int] = Field(default=None, gt=0, description="Audio bitrate in kbps")
    crf: Optional[int] = Field(default=None, ge=0, le=51, description="Constant Rate Factor (0-51)")
    max_width: Optional[int] = Field(default=None, gt=0, description="Maximum width in pixels")
    max_height: Optional[int] = Field(default=None, gt=0, description="Maximum height in pixels")
    target_format: Optional[VideoFormat] = Field(default=None, description="Target container format")


class ExtractAudioOptions(BaseModel):
    """Options for audio extraction"""

    format: AudioFormat = Field(default=AudioFormat.MP3, description="Output audio format")
    bitrate_kbps: Optional[int] = Field(default=None, gt=0, description="Audio bitrate in kbps")
    sample_rate: Optional[int] = Field(
        default=None, description="Sample rate (e.g., 44100, 48000)"
    )

    @field_validator("sample_rate")
    @classmethod
    def validate_sample_rate(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v not in [8000, 16000, 22050, 44100, 48000, 96000]:
            raise ValueError("Invalid sample rate")
        return v


class RemoveAudioOptions(BaseModel):
    """Options for removing audio"""

    keep_video_quality: bool = Field(default=True, description="Copy video stream without re-encoding")


class ConvertOptions(BaseModel):
    """Options for format conversion"""

    target_format: str = Field(description="Target format (mp4, mkv, webm, mp3, wav, etc.)")
    stream_copy: bool = Field(
        default=True, description="Copy streams without re-encoding when possible"
    )
    video_codec: Optional[str] = Field(default=None, description="Video codec (e.g., h264, vp9)")
    audio_codec: Optional[str] = Field(default=None, description="Audio codec (e.g., aac, opus)")


class ThumbnailOptions(BaseModel):
    """Options for thumbnail generation"""

    timestamp: Optional[float] = Field(
        default=None, ge=0, description="Timestamp in seconds for single thumbnail"
    )
    count: Optional[int] = Field(
        default=None, ge=1, le=20, description="Number of evenly spaced thumbnails"
    )
    format: ImageFormat = Field(default=ImageFormat.PNG, description="Output image format")
    width: Optional[int] = Field(default=None, gt=0, description="Thumbnail width")
    height: Optional[int] = Field(default=None, gt=0, description="Thumbnail height")

    @field_validator("count")
    @classmethod
    def validate_count_or_timestamp(cls, v: Optional[int], info: Any) -> Optional[int]:
        """Ensure either count or timestamp is provided, not both"""
        if v is not None and info.data.get("timestamp") is not None:
            raise ValueError("Specify either timestamp or count, not both")
        return v


class TrimOptions(BaseModel):
    """Options for trimming/clipping"""

    start_time: float = Field(ge=0, description="Start time in seconds")
    end_time: float = Field(gt=0, description="End time in seconds")

    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v: float, info: Any) -> float:
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be greater than start_time")
        return v


class ConcatOptions(BaseModel):
    """Options for concatenation"""

    file_count: int = Field(ge=2, le=50, description="Number of files to concatenate")


class GifOptions(BaseModel):
    """Options for GIF creation"""

    start_time: float = Field(ge=0, description="Start time in seconds")
    duration: float = Field(gt=0, le=30, description="Duration in seconds (max 30)")
    fps: int = Field(default=10, ge=1, le=30, description="Frames per second")
    width: Optional[int] = Field(default=None, gt=0, description="GIF width (maintains aspect ratio)")
    optimize: bool = Field(default=True, description="Optimize GIF for smaller size")


class FilterOptions(BaseModel):
    """Options for applying filters"""

    filters: list[dict[str, Any]] = Field(description="List of filters to apply")

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate filter structure"""
        for f in v:
            if "type" not in f:
                raise ValueError("Each filter must have a 'type' field")
        return v


class SubtitleOptions(BaseModel):
    """Options for subtitle operations"""

    subtitle_index: int = Field(default=0, ge=0, description="Subtitle stream index")
    format: Optional[str] = Field(default="srt", description="Subtitle format")


# Client Messages
class StartJobMessage(BaseModel):
    """Client message to start a new job"""

    type: Literal["start_job"] = "start_job"
    job_id: str = Field(description="Client-generated UUID for the job")
    operation: JobOperation
    input: InputSource
    options: Union[
        SpeedOptions,
        CompressionOptions,
        ExtractAudioOptions,
        RemoveAudioOptions,
        ConvertOptions,
        ThumbnailOptions,
        TrimOptions,
        ConcatOptions,
        GifOptions,
        FilterOptions,
        SubtitleOptions,
    ]


class CancelJobMessage(BaseModel):
    """Client message to cancel a job"""

    type: Literal["cancel_job"] = "cancel_job"
    job_id: str


class PingMessage(BaseModel):
    """Client ping message"""

    type: Literal["ping"] = "ping"


ClientMessage = Union[StartJobMessage, CancelJobMessage, PingMessage]


# Server Messages
class AckMessage(BaseModel):
    """Server acknowledgment message"""

    type: Literal["ack"] = "ack"
    job_id: str
    message: str = "Job accepted"


class ProgressMessage(BaseModel):
    """Server progress update message"""

    type: Literal["progress"] = "progress"
    job_id: str
    percentage: Optional[float] = Field(default=None, ge=0, le=100)
    stage: str
    ffmpeg_log: Optional[str] = None


class OutputMetadata(BaseModel):
    """Metadata about output file"""

    format: str
    duration: Optional[float] = None
    size_bytes: int
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    fps: Optional[float] = None


class CompletedMessage(BaseModel):
    """Server job completion message"""

    type: Literal["completed"] = "completed"
    job_id: str
    output_metadata: OutputMetadata
    delivery_method: Literal["binary"] = "binary"
    message: str = "Job completed successfully"


class ErrorMessage(BaseModel):
    """Server error message"""

    type: Literal["error"] = "error"
    job_id: Optional[str] = None
    code: str
    message: str
    details: Optional[str] = None


class PongMessage(BaseModel):
    """Server pong response"""

    type: Literal["pong"] = "pong"


ServerMessage = Union[AckMessage, ProgressMessage, CompletedMessage, ErrorMessage, PongMessage]
