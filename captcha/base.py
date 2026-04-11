import abc
import os
import random
import string
import threading
import time
import uuid


class BaseCaptcha(abc.ABC):
    """Abstract base class for captcha implementations.

    Subclasses must implement _create_media(captcha_id, answer, media_dir).
    Swap implementations by changing the instantiated class in app.py.
    """

    ANSWER_LENGTH = 4
    ANSWER_CHARS = "ABCDEFGHIJKLMNOPRSTUVWXYZ"
    EXPIRY_SECONDS = 60 * 30  # 30 minutes

    MEDIA_EXT = "png"
    MEDIA_URL_PATH = "captcha_images"
    MEDIA_TYPE = "image"

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def generate(self, media_dir: str, base_url: str) -> dict:
        """Generate a new captcha, save its media file, and return the metadata.

        Args:
            media_dir: Absolute path to the directory where the file will be saved.
            base_url: The base URL of the server (e.g. "http://localhost:5000/").

        Returns:
            {"captcha_id": str, "media_url": str, "media_type": str}
        """
        captcha_id = str(uuid.uuid4())
        answer = self._generate_answer()
        self._create_media(captcha_id, answer, media_dir)

        file_path = os.path.join(media_dir, f"{captcha_id}.{self.MEDIA_EXT}")
        expires_at = time.time() + self.EXPIRY_SECONDS
        with self._lock:
            self._store[captcha_id] = {
                "answer": answer,
                "expires_at": expires_at,
                "file_path": file_path,
            }

        media_url = (
            f"{base_url.rstrip('/')}/static/{self.MEDIA_URL_PATH}"
            f"/{captcha_id}.{self.MEDIA_EXT}"
        )
        return {
            "captcha_id": captcha_id,
            "media_url": media_url,
            "media_type": self.MEDIA_TYPE,
        }

    def verify(self, captcha_id: str, answer: str) -> bool:
        """Verify a captcha answer.

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
        return answer.strip().upper() == entry["answer"].upper()

    def _cleanup(self) -> None:
        """Remove expired entries from the store and delete their media files."""
        now = time.time()
        with self._lock:
            expired = [
                (cid, entry["file_path"])
                for cid, entry in self._store.items()
                if now > entry["expires_at"]
            ]
            for cid, _ in expired:
                del self._store[cid]
        for _, file_path in expired:
            try:
                os.remove(file_path)
            except OSError:
                pass

    def _generate_answer(self) -> str:
        """Return a random alphanumeric answer string. Override to customise."""
        return "".join(random.choices(self.ANSWER_CHARS, k=self.ANSWER_LENGTH))

    @abc.abstractmethod
    def _create_media(self, captcha_id: str, answer: str, media_dir: str) -> None:
        """Render the captcha answer into a media file and save it.

        The file must be saved as:
            {media_dir}/{captcha_id}.{MEDIA_EXT}

        Args:
            captcha_id: Unique identifier for this captcha (use as filename).
            answer: The answer that should be encoded in the media.
            media_dir: Directory in which to save the file.
        """
