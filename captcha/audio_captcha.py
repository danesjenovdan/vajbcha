import os
import random
import struct
import subprocess
import wave

from .base import BaseCaptcha


class AudioCaptcha(BaseCaptcha):
    """Captcha implementation that speaks the answer aloud as a WAV file.

    Uses espeak-ng directly via subprocess for offline TTS — no pyttsx3
    driver initialisation issues in headless/container environments.
    Low-amplitude random noise is mixed in after generation to harden the
    audio against simple automated transcription.
    """

    MEDIA_EXT = "wav"
    MEDIA_URL_PATH = "captcha_audio"
    MEDIA_TYPE = "audio"

    SPEECH_RATE = 100  # WPM — slow and clear for accessibility
    NOISE_AMPLITUDE = 400  # max per-sample noise (out of 32767)

    def _create_media(self, captcha_id: str, answer: str, media_dir: str) -> None:
        out_path = os.path.join(media_dir, f"{captcha_id}.wav")

        # Spell out each letter separated by commas so espeak-ng inserts natural pauses
        spoken = ",  ".join(answer.upper())

        subprocess.run(
            [
                "espeak-ng",
                "-w", out_path,
                "-s", str(self.SPEECH_RATE),
                "-v", "sl",
                # spoken,
                "A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z",
            ],
            check=True,
            capture_output=True,
        )

        self._add_noise(out_path)

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
