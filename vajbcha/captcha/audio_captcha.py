import io
import os
import random
import struct
import subprocess
import tempfile
import wave

from .base import BaseCaptcha


class AudioCaptcha(BaseCaptcha):
    """
    Captcha implementation that speaks the answer aloud as a WAV file.

    Uses espeak-ng directly via subprocess for offline TTS — no pyttsx3
    driver initialisation issues in headless/container environments.
    Low-amplitude random noise is mixed in after generation to harden the
    audio against simple automated transcription.
    """

    MEDIA_MIME = "audio/wav"

    SPEECH_RATE = 100  # WPM — slow and clear for accessibility
    NOISE_AMPLITUDE = 1500  # max per-sample noise (out of 32767)
    PAUSE_MS = 1000  # silence between letters in milliseconds

    def _create_media(self, answer: str, locale: str) -> bytes:
        tmp_files = []
        try:
            # Generate one WAV per letter using espeak-ng
            for letter in answer:
                fd, tmp_path = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
                tmp_files.append(tmp_path)
                subprocess.run(
                    [
                        "espeak-ng",
                        "-w",
                        tmp_path,
                        "-v",
                        locale,
                        "-s",
                        str(self.SPEECH_RATE),
                        letter,
                    ],
                    check=True,
                    capture_output=True,
                )

            # Merge letter WAVs with silence pauses into a single output file
            merged = self._merge_with_pauses(tmp_files, self.PAUSE_MS)
        finally:
            for f in tmp_files:
                try:
                    os.remove(f)
                except OSError:
                    pass

        return self._add_noise(merged)

    def _merge_with_pauses(self, wav_paths: list[str], pause_ms: int) -> bytes:
        """Concatenate WAV files into a bytes buffer, inserting silence between each."""
        # Read params from the first file to determine output format
        with wave.open(wav_paths[0], "rb") as wf:
            params = wf.getparams()

        n_channels = params.nchannels
        sampwidth = params.sampwidth
        framerate = params.framerate

        pause_frames = int(framerate * pause_ms / 1000)
        silence = b"\x00" * pause_frames * n_channels * sampwidth

        buf = io.BytesIO()
        with wave.open(buf, "wb") as out_wf:
            out_wf.setnchannels(n_channels)
            out_wf.setsampwidth(sampwidth)
            out_wf.setframerate(framerate)

            for i, path in enumerate(wav_paths):
                with wave.open(path, "rb") as wf:
                    out_wf.writeframes(wf.readframes(wf.getnframes()))
                if i < len(wav_paths) - 1:
                    out_wf.writeframes(silence)

        return buf.getvalue()

    def _add_noise(self, wav_bytes: bytes) -> bytes:
        """
        Mix variable-amplitude random noise into a 16-bit PCM WAV file.

        The noise amplitude changes every chunk so different parts of the
        audio have different noise levels — some quiet, some louder.
        """
        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            params = wf.getparams()
            frames = wf.readframes(params.nframes)

        # Only process 16-bit PCM; leave other formats untouched
        if params.sampwidth != 2:
            return wav_bytes

        n = params.nframes * params.nchannels
        samples = list(struct.unpack(f"{n}h", frames))

        # Vary amplitude in chunks of ~0.1 s worth of samples
        chunk_size = max(1, params.framerate * params.nchannels // 10)
        result = []
        i = 0
        while i < n:
            amp = random.randint(0, self.NOISE_AMPLITUDE)
            chunk = samples[i : i + chunk_size]
            for s in chunk:
                result.append(max(-32768, min(32767, s + random.randint(-amp, amp))))
            i += chunk_size

        noisy_frames = struct.pack(f"{n}h", *result)

        out_buf = io.BytesIO()
        with wave.open(out_buf, "wb") as wf:
            wf.setparams(params)
            wf.writeframes(noisy_frames)
        return out_buf.getvalue()
