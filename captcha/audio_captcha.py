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

    MEDIA_EXT = "wav"
    MEDIA_URL_PATH = "captcha_audio"
    MEDIA_TYPE = "audio"

    SPEECH_RATE = 100  # WPM — slow and clear for accessibility
    NOISE_AMPLITUDE = 1500  # max per-sample noise (out of 32767)
    PAUSE_MS = 1000  # silence between letters in milliseconds

    def _create_media(self, captcha_id: str, answer: str, media_dir: str) -> None:
        out_path = os.path.join(media_dir, f"{captcha_id}.wav")

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
                        "sl",
                        "-s",
                        str(self.SPEECH_RATE),
                        letter,
                    ],
                    check=True,
                    capture_output=True,
                )

            # Merge letter WAVs with silence pauses into a single output file
            self._merge_with_pauses(tmp_files, out_path, self.PAUSE_MS)
        finally:
            for f in tmp_files:
                try:
                    os.remove(f)
                except OSError:
                    pass

        self._add_noise(out_path)

    def _merge_with_pauses(self, wav_paths: list, out_path: str, pause_ms: int) -> None:
        """Concatenate WAV files into out_path, inserting silence between each."""
        # Read params from the first file to determine output format
        with wave.open(wav_paths[0], "rb") as wf:
            params = wf.getparams()

        n_channels = params.nchannels
        sampwidth = params.sampwidth
        framerate = params.framerate

        pause_frames = int(framerate * pause_ms / 1000)
        silence = b"\x00" * pause_frames * n_channels * sampwidth

        with wave.open(out_path, "wb") as out_wf:
            out_wf.setnchannels(n_channels)
            out_wf.setsampwidth(sampwidth)
            out_wf.setframerate(framerate)

            for i, path in enumerate(wav_paths):
                with wave.open(path, "rb") as wf:
                    out_wf.writeframes(wf.readframes(wf.getnframes()))
                if i < len(wav_paths) - 1:
                    out_wf.writeframes(silence)

    def _add_noise(self, path: str) -> None:
        """Mix variable-amplitude random noise into a 16-bit PCM WAV file.

        The noise amplitude changes every chunk so different parts of the
        audio have different noise levels — some quiet, some louder.
        """
        with wave.open(path, "rb") as wf:
            params = wf.getparams()
            frames = wf.readframes(params.nframes)

        # Only process 16-bit PCM; leave other formats untouched
        if params.sampwidth != 2:
            return

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

        with wave.open(path, "wb") as wf:
            wf.setparams(params)
            wf.writeframes(noisy_frames)
