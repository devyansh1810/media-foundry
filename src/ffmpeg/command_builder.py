"""FFmpeg command builder for all operations"""

from pathlib import Path
from typing import Any, Union

from src.config import get_settings
from src.websocket.models import (
    CompressionOptions,
    CompressionPreset,
    ConcatOptions,
    ConvertOptions,
    ExtractAudioOptions,
    FilterOptions,
    GifOptions,
    JobOperation,
    RemoveAudioOptions,
    SpeedOptions,
    SubtitleOptions,
    ThumbnailOptions,
    TrimOptions,
)


class FFmpegCommandBuilder:
    """Build FFmpeg commands for various operations"""

    def __init__(self) -> None:
        self.settings = get_settings()

    def build_command(
        self,
        operation: JobOperation,
        input_path: Path,
        output_path: Path,
        options: Any,
    ) -> list[str]:
        """Build FFmpeg command based on operation"""
        builders = {
            JobOperation.SPEED: self._build_speed_command,
            JobOperation.COMPRESS: self._build_compress_command,
            JobOperation.EXTRACT_AUDIO: self._build_extract_audio_command,
            JobOperation.REMOVE_AUDIO: self._build_remove_audio_command,
            JobOperation.CONVERT: self._build_convert_command,
            JobOperation.THUMBNAIL: self._build_thumbnail_command,
            JobOperation.TRIM: self._build_trim_command,
            JobOperation.CONCAT: self._build_concat_command,
            JobOperation.GIF: self._build_gif_command,
            JobOperation.FILTER: self._build_filter_command,
            JobOperation.EXTRACT_SUBTITLES: self._build_extract_subtitles_command,
            JobOperation.BURN_SUBTITLES: self._build_burn_subtitles_command,
        }

        builder = builders.get(operation)
        if not builder:
            raise ValueError(f"Unsupported operation: {operation}")

        return builder(input_path, output_path, options)

    def _base_command(self) -> list[str]:
        """Get base FFmpeg command with common flags"""
        cmd = ["ffmpeg", "-hide_banner", "-nostats"]
        if self.settings.ffmpeg_threads > 0:
            cmd.extend(["-threads", str(self.settings.ffmpeg_threads)])
        return cmd

    def _build_speed_command(
        self, input_path: Path, output_path: Path, options: SpeedOptions
    ) -> list[str]:
        """Build command for speed conversion"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])

        # Video speed filter
        video_filter = f"setpts={1/options.speed_factor}*PTS"
        cmd.extend(["-filter:v", video_filter])

        # Check if video has audio (set by job manager)
        has_audio = getattr(options, 'has_audio', True)

        if has_audio:
            # Audio speed filter
            if options.maintain_pitch:
                audio_filter = f"atempo={options.speed_factor}"
                # atempo only supports 0.5-2.0, so chain for larger factors
                if options.speed_factor > 2.0:
                    count = 0
                    temp_factor = options.speed_factor
                    audio_filter = ""
                    while temp_factor > 2.0:
                        audio_filter += "atempo=2.0,"
                        temp_factor /= 2.0
                        count += 1
                    if temp_factor > 1.0:
                        audio_filter += f"atempo={temp_factor}"
                    audio_filter = audio_filter.rstrip(",")
                elif options.speed_factor < 0.5:
                    count = 0
                    temp_factor = options.speed_factor
                    audio_filter = ""
                    while temp_factor < 0.5:
                        audio_filter += "atempo=0.5,"
                        temp_factor /= 0.5
                        count += 1
                    if temp_factor < 1.0:
                        audio_filter += f"atempo={temp_factor}"
                    audio_filter = audio_filter.rstrip(",")

                cmd.extend(["-filter:a", audio_filter])
            else:
                # No pitch correction - just change speed
                audio_filter = f"atempo={options.speed_factor}"
                cmd.extend(["-filter:a", audio_filter])

            # Re-encode both video and audio
            cmd.extend(["-c:v", "libx264", "-c:a", "aac"])
        else:
            # Video only - no audio filters
            cmd.extend(["-c:v", "libx264", "-an"])

        cmd.extend(["-y", str(output_path)])

        return cmd

    def _build_compress_command(
        self, input_path: Path, output_path: Path, options: CompressionOptions
    ) -> list[str]:
        """Build command for compression"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])

        # Apply preset defaults
        if options.preset == CompressionPreset.LOW:
            crf = options.crf or 32
            audio_br = options.audio_bitrate_kbps or 96
        elif options.preset == CompressionPreset.MEDIUM:
            crf = options.crf or 28
            audio_br = options.audio_bitrate_kbps or 128
        elif options.preset == CompressionPreset.HIGH:
            crf = options.crf or 23
            audio_br = options.audio_bitrate_kbps or 192
        else:  # CUSTOM
            crf = options.crf or 23
            audio_br = options.audio_bitrate_kbps or 128

        # Video encoding
        cmd.extend(["-c:v", "libx264", "-crf", str(crf), "-preset", "medium"])

        if options.video_bitrate_kbps:
            cmd.extend(["-b:v", f"{options.video_bitrate_kbps}k"])

        # Scale if needed
        if options.max_width or options.max_height:
            scale_filter = self._build_scale_filter(options.max_width, options.max_height)
            cmd.extend(["-vf", scale_filter])

        # Audio encoding
        cmd.extend(["-c:a", "aac", "-b:a", f"{audio_br}k"])

        # Output format
        if options.target_format:
            cmd.extend(["-f", options.target_format.value])

        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_extract_audio_command(
        self, input_path: Path, output_path: Path, options: ExtractAudioOptions
    ) -> list[str]:
        """Build command for audio extraction"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])

        # No video
        cmd.append("-vn")

        # Audio codec based on format
        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "wav": "pcm_s16le",
            "opus": "libopus",
            "m4a": "aac",
            "flac": "flac",
            "ogg": "libvorbis",
        }
        codec = codec_map.get(options.format.value, "copy")
        cmd.extend(["-c:a", codec])

        if options.bitrate_kbps:
            cmd.extend(["-b:a", f"{options.bitrate_kbps}k"])

        if options.sample_rate:
            cmd.extend(["-ar", str(options.sample_rate)])

        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_remove_audio_command(
        self, input_path: Path, output_path: Path, options: RemoveAudioOptions
    ) -> list[str]:
        """Build command for removing audio"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])

        # No audio
        cmd.append("-an")

        # Copy video or re-encode
        if options.keep_video_quality:
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend(["-c:v", "libx264", "-crf", "23"])

        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_convert_command(
        self, input_path: Path, output_path: Path, options: ConvertOptions
    ) -> list[str]:
        """Build command for format conversion"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])

        if options.stream_copy:
            cmd.extend(["-c", "copy"])
        else:
            if options.video_codec:
                cmd.extend(["-c:v", options.video_codec])
            if options.audio_codec:
                cmd.extend(["-c:a", options.audio_codec])

        cmd.extend(["-f", options.target_format])
        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_thumbnail_command(
        self, input_path: Path, output_path: Path, options: ThumbnailOptions
    ) -> list[str]:
        """Build command for thumbnail generation"""
        cmd = self._base_command()

        if options.timestamp is not None:
            # Single thumbnail at timestamp
            cmd.extend(["-ss", str(options.timestamp)])

        cmd.extend(["-i", str(input_path)])

        if options.count is not None:
            # Multiple thumbnails - use select filter
            cmd.extend(["-vf", f"select='not(mod(n\\,{options.count}))'", "-vsync", "vfr"])

        # Scale if specified
        if options.width or options.height:
            scale_filter = self._build_scale_filter(options.width, options.height)
            if "-vf" in cmd:
                # Append to existing filter
                idx = cmd.index("-vf")
                cmd[idx + 1] += f",{scale_filter}"
            else:
                cmd.extend(["-vf", scale_filter])

        # Single frame for single thumbnail
        if options.timestamp is not None:
            cmd.extend(["-frames:v", "1"])

        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_trim_command(
        self, input_path: Path, output_path: Path, options: TrimOptions
    ) -> list[str]:
        """Build command for trimming"""
        cmd = self._base_command()

        # Use -ss before -i for faster seeking
        cmd.extend(["-ss", str(options.start_time)])
        cmd.extend(["-i", str(input_path)])

        # Duration instead of end time
        duration = options.end_time - options.start_time
        cmd.extend(["-t", str(duration)])

        # Copy streams for speed
        cmd.extend(["-c", "copy"])
        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_concat_command(
        self, input_path: Path, output_path: Path, options: ConcatOptions
    ) -> list[str]:
        """Build command for concatenation"""
        # Note: input_path should be a concat file list
        cmd = self._base_command()
        cmd.extend(["-f", "concat", "-safe", "0"])
        cmd.extend(["-i", str(input_path)])
        cmd.extend(["-c", "copy"])
        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_gif_command(
        self, input_path: Path, output_path: Path, options: GifOptions
    ) -> list[str]:
        """Build command for GIF creation"""
        cmd = self._base_command()
        cmd.extend(["-ss", str(options.start_time)])
        cmd.extend(["-t", str(options.duration)])
        cmd.extend(["-i", str(input_path)])

        # Build palette filter for better quality
        filters = f"fps={options.fps}"

        if options.width:
            filters += f",scale={options.width}:-1:flags=lanczos"

        if options.optimize:
            # Two-pass with palette
            palette_filter = filters + ",palettegen"
            gif_filter = filters + "[x];[x][1:v]paletteuse"
            cmd.extend(["-vf", palette_filter, "-y", "/tmp/palette.png"])
            # This is simplified; actual implementation would need two passes
        else:
            cmd.extend(["-vf", filters])

        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_filter_command(
        self, input_path: Path, output_path: Path, options: FilterOptions
    ) -> list[str]:
        """Build command for applying filters"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])

        # Build filter chain
        video_filters = []
        audio_filters = []

        for f in options.filters:
            filter_type = f.get("type")

            if filter_type == "scale":
                width = f.get("width", -1)
                height = f.get("height", -1)
                video_filters.append(f"scale={width}:{height}")

            elif filter_type == "rotate":
                angle = f.get("angle", 0)
                video_filters.append(f"rotate={angle}*PI/180")

            elif filter_type == "crop":
                w = f.get("width")
                h = f.get("height")
                x = f.get("x", 0)
                y = f.get("y", 0)
                video_filters.append(f"crop={w}:{h}:{x}:{y}")

            elif filter_type == "fps":
                fps = f.get("fps", 30)
                video_filters.append(f"fps={fps}")

            elif filter_type == "volume":
                volume = f.get("volume", 1.0)
                audio_filters.append(f"volume={volume}")

            elif filter_type == "normalize":
                audio_filters.append("loudnorm")

        if video_filters:
            cmd.extend(["-vf", ",".join(video_filters)])
        if audio_filters:
            cmd.extend(["-af", ",".join(audio_filters)])

        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_extract_subtitles_command(
        self, input_path: Path, output_path: Path, options: SubtitleOptions
    ) -> list[str]:
        """Build command for extracting subtitles"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])
        cmd.extend(["-map", f"0:s:{options.subtitle_index}"])
        cmd.extend(["-c:s", options.format or "srt"])
        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_burn_subtitles_command(
        self, input_path: Path, output_path: Path, options: SubtitleOptions
    ) -> list[str]:
        """Build command for burning subtitles"""
        cmd = self._base_command()
        cmd.extend(["-i", str(input_path)])
        # This is simplified - would need subtitle file path
        cmd.extend(["-vf", f"subtitles={input_path}:si={options.subtitle_index}"])
        cmd.extend(["-c:a", "copy"])
        cmd.extend(["-y", str(output_path)])
        return cmd

    def _build_scale_filter(
        self, width: Union[int, None], height: Union[int, None]
    ) -> str:
        """Build scale filter maintaining aspect ratio"""
        if width and height:
            return f"scale='min({width},iw)':'min({height},ih)':force_original_aspect_ratio=decrease"
        elif width:
            return f"scale={width}:-1"
        elif height:
            return f"scale=-1:{height}"
        return "scale=iw:ih"  # No scaling
