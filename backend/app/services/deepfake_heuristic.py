"""
Feature 9 — Video / Audio Deepfake Heuristic Check

Uses simple, training-free heuristics rather than a trained model.
Two analysis paths:
  VIDEO: OpenCV frame-consistency check (sudden cuts, uniform background, low motion variance)
  AUDIO: librosa spectral analysis (anomalous frequency patterns, flat spectral rolloff)

MVP-DEPTH: Production would use:
  - Video: FaceForensics++ / EfficientNet-based detection model
  - Audio: Wav2Vec2-based voice synthesis detection
  - Combined: Multi-modal ensemble with temporal analysis
  - Real-time: Stream analysis, not file upload
"""
from __future__ import annotations

import io
import logging
import tempfile
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Supported MIME types
VIDEO_TYPES = {"video/mp4", "video/mpeg", "video/webm", "video/quicktime"}
AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/flac", "audio/x-wav"}


def _analyse_video(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    OpenCV heuristic for video deepfake detection.
    Checks: frame variance (frozen frames = deepfake signal),
            brightness uniformity (studio-lit fake backgrounds),
            compression artifact level.
    """
    try:
        import cv2
        import numpy as np

        # Write to temp file (OpenCV needs a path)
        suffix = Path(filename).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                return _video_error_result("Could not open video file")

            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30

            # Sample up to 30 frames evenly
            sample_count = min(30, frame_count)
            step = max(1, frame_count // sample_count)

            grays = []
            prev_gray = None
            motion_diffs = []

            for i in range(0, frame_count, step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                grays.append(gray)
                if prev_gray is not None:
                    diff = np.mean(np.abs(gray.astype(float) - prev_gray.astype(float)))
                    motion_diffs.append(diff)
                prev_gray = gray

            cap.release()
        finally:
            os.unlink(tmp_path)

        if len(grays) < 2:
            return _video_error_result("Too few frames to analyse")

        # ── Heuristics ─────────────────────────────────────────────────────────
        motion_arr = __import__("numpy").array(motion_diffs)
        mean_motion = float(motion_arr.mean())
        std_motion = float(motion_arr.std())

        # Frozen-face signal: very low motion variance (real video calls have natural movement)
        low_motion_variance = std_motion < 1.5

        # Brightness uniformity (uniform backgrounds used in deepfake overlays)
        brightness_vals = [float(g.mean()) for g in grays]
        brightness_std = float(__import__("numpy").std(brightness_vals))
        uniform_brightness = brightness_std < 5.0

        # Compression artifacts (very low quality = repurposed/re-encoded deepfake)
        laplacian_vars = [float(cv2.Laplacian(g, cv2.CV_64F).var()) for g in grays]
        mean_sharpness = float(__import__("numpy").mean(laplacian_vars))
        very_low_sharpness = mean_sharpness < 20.0

        signals = {
            "low_motion_variance": low_motion_variance,
            "uniform_brightness": uniform_brightness,
            "very_low_sharpness": very_low_sharpness,
        }
        positive_signals = sum(signals.values())
        confidence = min(0.95, 0.3 * positive_signals + 0.1)
        likely_deepfake = positive_signals >= 2

        heuristics_used = [
            "opencv_frame_motion_variance",
            "opencv_brightness_uniformity",
            "opencv_laplacian_sharpness",
        ]
        notes = (
            f"Analysed {len(grays)} frames. "
            f"Motion variance: {std_motion:.2f} (low<1.5), "
            f"Brightness std: {brightness_std:.2f} (uniform<5.0), "
            f"Sharpness: {mean_sharpness:.2f} (low<20). "
            f"Signals triggered: {positive_signals}/3."
        )

        return {
            "likely_deepfake": likely_deepfake,
            "confidence": confidence,
            "media_type": "video",
            "notes": notes,
            "heuristics_used": heuristics_used,
        }

    except ImportError:
        logger.error("OpenCV not installed — skipping video analysis")
        return _video_error_result("OpenCV not available; install opencv-python-headless")
    except Exception as exc:
        logger.exception("Video analysis error: %s", exc)
        return _video_error_result(f"Analysis failed: {exc}")


def _analyse_audio(file_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    librosa heuristic for voice-spoofing detection.
    Checks: spectral flatness (synthesised voice = flatter spectrum),
            zero-crossing rate variance, harmonic-to-noise ratio.
    """
    try:
        import librosa
        import numpy as np
        import soundfile as sf

        audio_io = io.BytesIO(file_bytes)

        try:
            y, sr = librosa.load(audio_io, sr=None, mono=True, duration=60)
        except Exception:
            # Fallback with soundfile
            audio_io.seek(0)
            data, sr = sf.read(audio_io)
            if data.ndim > 1:
                data = data.mean(axis=1)
            y = data.astype("float32")

        # ── Heuristics ─────────────────────────────────────────────────────────
        # Spectral flatness (1.0 = white noise / TTS; 0 = tonal natural voice)
        flatness = librosa.feature.spectral_flatness(y=y)
        mean_flatness = float(flatness.mean())
        high_flatness = mean_flatness > 0.15

        # Zero crossing rate (synthesised speech often abnormally low or high)
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_std = float(zcr.std())
        low_zcr_variance = zcr_std < 0.005

        # Spectral rolloff — TTS voices often miss natural high-frequency tail
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        mean_rolloff = float(rolloff.mean())
        low_rolloff = mean_rolloff < sr * 0.25

        signals = {
            "high_spectral_flatness": high_flatness,
            "low_zcr_variance": low_zcr_variance,
            "low_spectral_rolloff": low_rolloff,
        }
        positive_signals = sum(signals.values())
        confidence = min(0.90, 0.25 * positive_signals + 0.15)
        likely_deepfake = positive_signals >= 2

        notes = (
            f"Spectral flatness: {mean_flatness:.4f} (high>{0.15}), "
            f"ZCR std: {zcr_std:.5f} (low<0.005), "
            f"Rolloff: {mean_rolloff:.0f}Hz. "
            f"Signals triggered: {positive_signals}/3."
        )

        return {
            "likely_deepfake": likely_deepfake,
            "confidence": confidence,
            "media_type": "audio",
            "notes": notes,
            "heuristics_used": [
                "librosa_spectral_flatness",
                "librosa_zero_crossing_rate",
                "librosa_spectral_rolloff",
            ],
        }

    except ImportError:
        logger.error("librosa not installed — skipping audio analysis")
        return _audio_error_result("librosa not available; install librosa")
    except Exception as exc:
        logger.exception("Audio analysis error: %s", exc)
        return _audio_error_result(f"Analysis failed: {exc}")


def _video_error_result(notes: str) -> dict[str, Any]:
    return {
        "likely_deepfake": False,
        "confidence": 0.0,
        "media_type": "video",
        "notes": notes,
        "heuristics_used": [],
    }


def _audio_error_result(notes: str) -> dict[str, Any]:
    return {
        "likely_deepfake": False,
        "confidence": 0.0,
        "media_type": "audio",
        "notes": notes,
        "heuristics_used": [],
    }


async def analyse_media(file_bytes: bytes, content_type: str, filename: str) -> dict[str, Any]:
    """
    Main entry point. Routes to video or audio analyser based on content type.
    """
    ct = content_type.lower().split(";")[0].strip()

    if ct in VIDEO_TYPES:
        return _analyse_video(file_bytes, filename)
    elif ct in AUDIO_TYPES:
        return _analyse_audio(file_bytes, filename)
    else:
        # Try to infer from extension
        ext = Path(filename).suffix.lower()
        if ext in {".mp4", ".webm", ".mov", ".avi", ".mkv"}:
            return _analyse_video(file_bytes, filename)
        elif ext in {".wav", ".mp3", ".ogg", ".flac", ".m4a"}:
            return _analyse_audio(file_bytes, filename)
        else:
            return {
                "likely_deepfake": False,
                "confidence": 0.0,
                "media_type": "unknown",
                "notes": f"Unsupported media type: {content_type}. Supported: video/mp4, audio/wav, etc.",
                "heuristics_used": [],
            }
