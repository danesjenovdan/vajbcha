(() => {
  let currentCaptchaId = null;
  let captchaType = "image"; // "image" | "audio"

  const captchaImg = document.getElementById("captcha-img");
  const captchaAudio = document.getElementById("captcha-audio");
  const captchaInput = document.getElementById("captcha-input");
  const refreshBtn = document.getElementById("refresh-btn");
  const captchaForm = document.getElementById("captcha-form");
  const errorMsg = document.getElementById("error-msg");
  const subtitle = document.getElementById("captcha-subtitle");
  const toggleBtn = document.getElementById("toggle-mode-btn");

  function showError(message) {
    errorMsg.textContent = message;
    errorMsg.hidden = false;
  }

  function clearError() {
    errorMsg.textContent = "";
    errorMsg.hidden = true;
  }

  function applyMode() {
    if (captchaType === "image") {
      subtitle.textContent = "Type the characters shown in the image below.";
      toggleBtn.textContent = "Can't see the image? Try audio captcha";
      captchaImg.hidden = false;
      captchaAudio.hidden = true;
      captchaAudio.src = "";
    } else {
      subtitle.textContent = "Listen to the audio and type the characters below.";
      toggleBtn.textContent = "Switch back to image captcha";
      captchaImg.hidden = true;
      captchaImg.src = "";
      captchaAudio.hidden = false;
    }
  }

  async function loadCaptcha() {
    clearError();
    captchaInput.value = "";

    const endpoint = captchaType === "audio" ? "/api/captcha/audio" : "/api/captcha";

    try {
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }
      const data = await response.json();
      currentCaptchaId = data.captcha_id;

      if (data.media_type === "audio") {
        // Bust cache so the browser fetches the new WAV
        captchaAudio.src = data.media_url + "?t=" + Date.now();
      } else {
        captchaImg.src = data.media_url + "?t=" + Date.now();
        captchaImg.alt = "Captcha image";
      }
    } catch (err) {
      showError("Failed to load captcha. Please refresh the page.");
      console.error("loadCaptcha error:", err);
    }
  }

  async function submitForm(event) {
    event.preventDefault();
    clearError();

    const answer = captchaInput.value.trim();
    if (!answer) {
      showError("Please enter the captcha characters.");
      captchaInput.focus();
      return;
    }

    if (!currentCaptchaId) {
      showError("No active captcha. Please wait for it to load.");
      return;
    }

    try {
      const response = await fetch("/api/captcha/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ captcha_id: currentCaptchaId, answer }),
      });

      const data = await response.json();

      if (data.success) {
        window.location.href = "/success";
      } else {
        showError(data.message || "Incorrect captcha. Please try again.");
        await loadCaptcha();
      }
    } catch (err) {
      showError("Network error. Please try again.");
      console.error("submitForm error:", err);
    }
  }

  toggleBtn.addEventListener("click", () => {
    captchaType = captchaType === "image" ? "audio" : "image";
    applyMode();
    loadCaptcha();
  });

  refreshBtn.addEventListener("click", loadCaptcha);
  captchaForm.addEventListener("submit", submitForm);

  // Load the first captcha when the page is ready
  applyMode();
  loadCaptcha();
})();
