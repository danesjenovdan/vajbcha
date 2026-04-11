import os
import random
import uuid

from flask import Flask, Response, jsonify, request

from captcha import AudioCaptcha, ImageCaptcha

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ANSWER_LENGTH = 4
ANSWER_CHARS = "ABCDEFGHIJKLMNOPRSTUVWXYZ"

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Captcha providers
# ---------------------------------------------------------------------------
image_captcha = ImageCaptcha()
audio_captcha = AudioCaptcha()


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------


def _generate_answer() -> str:
    return "".join(random.choices(ANSWER_CHARS, k=ANSWER_LENGTH))


@app.get("/api/captcha")
def api_get_captcha() -> tuple[Response, int]:
    """Generate a captcha pair (image + audio) sharing the same ID and answer."""
    captcha_id = str(uuid.uuid4()).replace("-", "")
    answer = _generate_answer()
    image_data = image_captcha.generate(captcha_id, answer)
    audio_data = audio_captcha.generate(captcha_id, answer)
    return (
        jsonify(
            {
                "captcha_id": captcha_id,
                "image_src": image_data["media_src"],
                "audio_src": audio_data["media_src"],
            }
        ),
        200,
    )


@app.post("/api/captcha/verify")
def api_verify_captcha() -> tuple[Response, int]:
    """
    Verify a captcha answer.

    Request body (JSON):
        captcha_id: str
        answer:     str

    Response body (JSON):
        success: bool
        message: str
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"success": False, "message": "Request body must be JSON."}), 400

    captcha_id = body.get("captcha_id", "").strip()
    answer = body.get("answer", "").strip()

    if not captcha_id:
        return jsonify({"success": False, "message": "captcha_id is required."}), 400
    if not answer:
        return jsonify({"success": False, "message": "answer is required."}), 400

    image_correct = image_captcha.verify(captcha_id, answer)
    audio_correct = audio_captcha.verify(captcha_id, answer)
    correct = image_correct or audio_correct
    if correct:
        return (
            jsonify({"success": True, "message": "Captcha verified successfully."}),
            200,
        )
    return (
        jsonify(
            {
                "success": False,
                "message": "Incorrect or expired captcha. Please try again.",
            }
        ),
        200,
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0")
