import os

from flask import Flask, jsonify, request, send_from_directory

from captcha import TextCaptcha
from generate_test_image import generate_test_image

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CAPTCHA_IMAGE_DIR = os.path.join(STATIC_DIR, "captcha_images")

# Ensure the captcha image directory exists at startup
os.makedirs(CAPTCHA_IMAGE_DIR, exist_ok=True)

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")

# ---------------------------------------------------------------------------
# Captcha provider — swap this one line to use a different implementation
# ---------------------------------------------------------------------------
captcha_provider = TextCaptcha(dot_size=4, dot_gap=2, char_gap=8)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/success")
def success():
    return send_from_directory(STATIC_DIR, "success.html")


@app.route("/test")
def test():
    return send_from_directory(STATIC_DIR, "test.html")


@app.route("/static/test.png")
def test_image():
    path = os.path.join(STATIC_DIR, "test.png")
    generate_test_image(path)
    return send_from_directory(STATIC_DIR, "test.png")


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------


@app.get("/api/captcha")
def api_get_captcha():
    """Generate a new captcha and return its ID and image URL."""
    base_url = request.host_url
    data = captcha_provider.generate(CAPTCHA_IMAGE_DIR, base_url)
    return jsonify(data), 200


@app.post("/api/captcha/verify")
def api_verify_captcha():
    """Verify a captcha answer.

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

    correct = captcha_provider.verify(captcha_id, answer)
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
