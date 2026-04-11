import abc
import base64
import threading
import time
from typing import TypedDict


class _StoreEntry(TypedDict):
    answers: list[str]
    expires_at: float


class BaseCaptcha(abc.ABC):
    """
    Abstract base class for captcha implementations.

    Subclasses must implement _create_media(captcha_id, answer, media_dir).
    Swap implementations by changing the instantiated class in app.py.
    """

    EXPIRY_SECONDS = 60 * 30  # 30 minutes

    MEDIA_MIME = "image/png"

    def __init__(self) -> None:
        self._store: dict[str, _StoreEntry] = {}
        self._lock = threading.Lock()

    def generate(self, captcha_id: str, answer: str, locale: str) -> dict[str, str]:
        """
        Generate a new captcha and return its base64-encoded media.

        Args:
            captcha_id: Shared identifier for this captcha pair.
            answer: The answer to encode in the media.
            locale: The locale for the captcha (e.g., "en", "sl").

        Returns:
            {"captcha_id": str, "media_src": str}
        """
        media_bytes = self._create_media(answer, locale)
        media_src = (
            f"data:{self.MEDIA_MIME};base64," + base64.b64encode(media_bytes).decode()
        )
        expires_at = time.time() + self.EXPIRY_SECONDS
        with self._lock:
            self._store[captcha_id] = {
                "answers": [answer],
                "expires_at": expires_at,
            }
        return {
            "captcha_id": captcha_id,
            "media_src": media_src,
        }

    def verify(self, captcha_id: str, answer: str) -> bool:
        """
        Verify a captcha answer.

        The captcha is consumed on first call (prevents replay attacks).

        Args:
            captcha_id: The ID returned by generate().
            answer: The user-supplied answer string.

        Returns:
            True if the answer is correct and the captcha has not expired.
        """
        self._cleanup()
        with self._lock:
            entry = self._store.pop(captcha_id, None)
        if entry is None:
            return False
        if time.time() > entry["expires_at"]:
            return False
        return answer.strip().upper() in {a.upper() for a in entry["answers"]}

    def _cleanup(self) -> None:
        """Remove expired entries from the store."""
        now = time.time()
        with self._lock:
            expired = [
                cid for cid, entry in self._store.items() if now > entry["expires_at"]
            ]
            for cid in expired:
                del self._store[cid]

    @abc.abstractmethod
    def _create_media(self, answer: str, locale: str) -> bytes:
        """
        Render the captcha answer into media and return its raw bytes.

        Args:
            answer: The answer that should be encoded in the media.
            locale: The locale for the captcha (e.g., "en", "sl").

        Returns:
            Raw bytes of the media file (PNG, WAV, etc.).
        """
