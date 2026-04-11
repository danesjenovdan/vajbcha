(() => {
  let currentCaptchaId = null;

  const captchaImg = document.getElementById("captcha-img");
  const captchaInput = document.getElementById("captcha-input");
  const refreshBtn = document.getElementById("refresh-btn");
  const captchaForm = document.getElementById("captcha-form");
  const errorMsg = document.getElementById("error-msg");

  function showError(message) {
    errorMsg.textContent = message;
    errorMsg.hidden = false;
  }

  function clearError() {
    errorMsg.textContent = "";
    errorMsg.hidden = true;
  }

  async function loadCaptcha() {
    clearError();
    captchaInput.value = "";
    captchaImg.src = "";
    captchaImg.alt = "Loading captcha…";

    try {
      const response = await fetch("/api/captcha");
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }
      const data = await response.json();
      currentCaptchaId = data.captcha_id;
      // Bust the browser cache so the new image always loads
      captchaImg.src = data.image_url + "?t=" + Date.now();
      captchaImg.alt = "Captcha image";
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
      showError("No active captcha. Please wait for the image to load.");
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

  refreshBtn.addEventListener("click", loadCaptcha);
  captchaForm.addEventListener("submit", submitForm);

  // Load the first captcha when the page is ready
  loadCaptcha();
})();
