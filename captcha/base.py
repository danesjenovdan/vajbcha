import abc
import os
import random
import string
import threading
import time
import uuid


class BaseCaptcha(abc.ABC):
    """Abstract base class for captcha implementations.

    Subclasses must implement _create_image(captcha_id, answer, image_dir).
    Swap implementations by changing the instantiated class in app.py.
    """

    ANSWER_LENGTH = 4
    ANSWER_CHARS = string.ascii_uppercase
    EXPIRY_SECONDS = 60 * 30  # 30 minutes

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()

    def generate(self, image_dir: str, base_url: str) -> dict:
        """Generate a new captcha, save its image, and return the metadata.

        Args:
            image_dir: Absolute path to the directory where the image will be saved.
            base_url: The base URL of the server (e.g. "http://localhost:5000/").

        Returns:
            {"captcha_id": str, "image_url": str}
        """
        captcha_id = str(uuid.uuid4())
        answer = self._generate_answer()
        self._create_image(captcha_id, answer, image_dir)

        expires_at = time.time() + self.EXPIRY_SECONDS
        with self._lock:
            self._store[captcha_id] = {"answer": answer, "expires_at": expires_at}

        image_url = f"{base_url.rstrip('/')}/static/captcha_images/{captcha_id}.png"
        return {"captcha_id": captcha_id, "image_url": image_url}

    def verify(self, captcha_id: str, answer: str) -> bool:
        """Verify a captcha answer.

        The captcha is consumed on first call (prevents replay attacks).

        Args:
            captcha_id: The ID returned by generate().
            answer: The user-supplied answer string.

        Returns:
            True if the answer is correct and the captcha has not expired.
        """
        with self._lock:
            entry = self._store.pop(captcha_id, None)

        if entry is None:
            return False
        if time.time() > entry["expires_at"]:
            return False
        return answer.strip().upper() == entry["answer"].upper()

    def _generate_answer(self) -> str:
        """Return a random alphanumeric answer string. Override to customise."""
        return "".join(random.choices(self.ANSWER_CHARS, k=self.ANSWER_LENGTH))

    @abc.abstractmethod
    def _create_image(self, captcha_id: str, answer: str, image_dir: str) -> None:
        """Render the captcha answer into an image and save it.

        The image must be saved as:
            {image_dir}/{captcha_id}.png

        Args:
            captcha_id: Unique identifier for this captcha (use as filename).
            answer: The text that should appear in the image.
            image_dir: Directory in which to save the image file.
        """
