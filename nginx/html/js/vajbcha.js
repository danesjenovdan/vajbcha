(function () {
  const MESSAGES = {
    en: {
      captchaLoading: "CAPTCHA challenge loading ...",
      captchaRefresh: "Refresh captcha",
      captchaAudio: "Play audio captcha",
      captchaStop: "Stop audio captcha",
      captchaType: "type the characters above",
    },
    sl: {
      captchaLoading: "Izziv CAPTCHA se nalaga ...",
      captchaRefresh: "Osveži izziv CAPTCHA",
      captchaAudio: "Predvajaj zvočni izziv CAPTCHA",
      captchaStop: "Ustavi zvočni izziv CAPTCHA",
      captchaType: "vnesi zgoraj prikazane znake",
    },
  };

  const me = document.currentScript;
  const inputName = me.dataset.inputName || "captcha-answer";
  const baseUrl = me.dataset.baseUrl || "https://vajbcha.danesjenovdan.si";
  const locale = me.dataset.locale || "en";
  const msgs = MESSAGES[locale] || MESSAGES["en"];

  let container = null;
  if (
    me.previousElementSibling &&
    me.previousElementSibling.tagName === "DIV" &&
    me.previousElementSibling.id === "vajbcha"
  ) {
    container = me.previousElementSibling;
  } else {
    container = document.createElement("div");
    container.id = "vajbcha";
    me.parentNode.insertBefore(container, me);
  }

  const hiddenInput = document.createElement("input");
  hiddenInput.type = "hidden";
  hiddenInput.name = inputName;
  hiddenInput.value = "";
  container.appendChild(hiddenInput);

  const iframe = document.createElement("iframe");
  iframe.style.display = "block";
  iframe.style.width = "280px";
  iframe.style.height = "140px";
  iframe.style.backgroundColor = "transparent";
  iframe.style.border = "0";

  iframe.addEventListener("load", () => {
    const doc = iframe.contentWindow.document;
    doc.body.style.margin = "0";

    const wrapper = doc.createElement("div");
    wrapper.style.boxSizing = "border-box";
    wrapper.style.display = "flex";
    wrapper.style.padding = "6px";
    wrapper.style.backgroundColor = "white";
    wrapper.style.border = "1px solid rgb(127 127 127 / 0.5)";
    wrapper.style.borderRadius = "4px";
    doc.body.appendChild(wrapper);

    const imgContainer = doc.createElement("div");
    imgContainer.style.flex = "0 0 220px";
    wrapper.appendChild(imgContainer);

    const buttonsContainer = doc.createElement("div");
    buttonsContainer.style.boxSizing = "border-box";
    buttonsContainer.style.flex = "0 0 50px";
    buttonsContainer.style.display = "flex";
    buttonsContainer.style.flexDirection = "column";
    buttonsContainer.style.justifyContent = "flex-start";
    buttonsContainer.style.gap = "4px";
    buttonsContainer.style.paddingLeft = "6px";
    wrapper.appendChild(buttonsContainer);

    const imgWrapper = doc.createElement("div");
    imgWrapper.style.boxSizing = "border-box";
    imgWrapper.style.position = "relative";
    imgWrapper.style.width = "220px";
    imgWrapper.style.height = "90px";
    imgWrapper.style.border = "1px solid rgb(127 127 127 / 0.5)";
    imgWrapper.style.borderRadius = "4px";
    imgWrapper.style.overflow = "hidden";
    imgContainer.appendChild(imgWrapper);

    const img = doc.createElement("img");
    img.style.margin = "-1px";
    img.style.width = "220px";
    img.style.height = "90px";
    img.src = "data:image/png;base64,";
    img.alt = msgs.captchaLoading;
    imgWrapper.appendChild(img);

    const inputForm = doc.createElement("form");
    inputForm.style.display = "flex";
    inputForm.style.margin = "4px 0 0 0";
    imgContainer.appendChild(inputForm);

    const input = doc.createElement("input");
    input.type = "text";
    input.value = "";
    input.placeholder = msgs.captchaType;
    input.style.boxSizing = "border-box";
    input.style.width = "100%";
    input.style.padding = "0 6px";
    input.style.backgroundColor = "white";
    input.style.border = "1px solid rgb(127 127 127 / 0.5)";
    input.style.borderRadius = "4px";
    input.style.fontFamily = "monospace";
    input.style.fontSize = "20px";
    input.style.fontWeight = "700";
    input.style.height = "32px";
    input.style.lineHeight = "32px";
    input.style.textTransform = "uppercase";
    inputForm.appendChild(input);

    function createButton(text, svg) {
      const button = doc.createElement("button");
      button.type = "button";
      button.style.boxSizing = "border-box";
      button.style.position = "relative";
      button.style.width = "40px";
      button.style.height = "40px";
      button.style.padding = "0";
      button.style.background = "transparent";
      button.style.border = "1px solid rgb(127 127 127 / 0.5)";
      button.style.borderRadius = "4px";
      button.style.cursor = "pointer";
      const span = doc.createElement("span");
      span.textContent = text;
      span.style.display = "block";
      span.style.textIndent = "-9999px";
      button.appendChild(span);
      const icon = doc.createElement("div");
      icon.classList.add("icon");
      icon.style.position = "absolute";
      icon.style.inset = "8px";
      icon.style.color = "#000";
      icon.innerHTML = svg;
      button.appendChild(icon);
      return button;
    }

    const refresh = createButton(
      "Refresh",
      `
        <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16">
          <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"/>
          <path fill-rule="evenodd" d="M8 3c-1.552 0-2.94.707-3.857 1.818a.5.5 0 1 1-.771-.636A6.002 6.002 0 0 1 13.917 7H12.9A5.002 5.002 0 0 0 8 3zM3.1 9a5.002 5.002 0 0 0 8.757 2.182.5.5 0 1 1 .771.636A6.002 6.002 0 0 1 2.083 9H3.1z"/>
        </svg>
      `,
    );
    refresh.title = msgs.captchaRefresh;
    refresh.disabled = true;
    refresh.style.opacity = "0.5";
    refresh.style.cursor = "not-allowed";
    buttonsContainer.appendChild(refresh);

    const audioIcon = `
      <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16">
        <path d="M8 3a5 5 0 0 0-5 5v1h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V8a6 6 0 1 1 12 0v5a1 1 0 0 1-1 1h-1a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1V8a5 5 0 0 0-5-5z"/>
      </svg>
    `;
    const stopIcon = `
      <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16">
        <path d="M5 3.5h6A1.5 1.5 0 0 1 12.5 5v6a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 11V5A1.5 1.5 0 0 1 5 3.5"/>
      </svg>
    `;

    const audio = createButton("Audio", audioIcon);
    audio.title = msgs.captchaAudio;
    audio.disabled = true;
    audio.style.opacity = "0.5";
    audio.style.cursor = "not-allowed";
    buttonsContainer.appendChild(audio);

    let captchaId = null;
    let captchaInput = "";
    let audioSrc = null;
    let audioCaptcha = null;

    function insertCaptchaImage(data) {
      captchaId = data.captchaId;
      img.src = data.media_src;
      img.alt = "CAPTCHA";
      input.value = "";
      captchaInput = "";
      hiddenInput.value = `${captchaId};`;
      refresh.disabled = false;
      refresh.style.opacity = "1";
      refresh.style.cursor = "pointer";
      audioSrc = `data:audio/wav;base64,${data.audioCaptcha}`;
      if (audioCaptcha) {
        audioCaptcha.pause();
        audioCaptcha = null;
        audio.title = msgs.captchaAudio;
        audio.querySelector(".icon").innerHTML = audioIcon;
      }
      audio.disabled = false;
      audio.style.opacity = "1";
      audio.style.cursor = "pointer";
    }

    function reloadCaptchaImage() {
      refresh.disabled = true;
      refresh.style.opacity = "0.5";
      const previousCaptchaId = captchaId;
      fetch(
        `${baseUrl}/api/captcha?locale=${locale}&previous=${previousCaptchaId}`,
      )
        .then((response) => response.json())
        .then((data) => {
          insertCaptchaImage(data);
        });
    }

    refresh.addEventListener("click", reloadCaptchaImage);

    audio.addEventListener("click", () => {
      if (audioCaptcha) {
        audioCaptcha.pause();
        audioCaptcha = null;
        audio.title = msgs.captchaAudio;
        audio.querySelector(".icon").innerHTML = audioIcon;
        return;
      }
      audio.title = msgs.captchaStop;
      audio.querySelector(".icon").innerHTML = stopIcon;
      audioCaptcha = new Audio(audioSrc);
      audioCaptcha.currentTime = 0;
      audioCaptcha.play();
      input.focus();
      audioCaptcha.addEventListener("ended", () => {
        audioCaptcha = null;
        audio.title = msgs.captchaAudio;
        audio.querySelector(".icon").innerHTML = audioIcon;
      });
    });

    inputForm.addEventListener("submit", (event) => {
      event.preventDefault();
    });

    input.addEventListener("input", (event) => {
      captchaInput = event.target.value;
      hiddenInput.value = `${captchaId};${captchaInput}`;
    });

    fetch(`${baseUrl}/api/captcha?locale=${locale}`)
      .then((response) => response.json())
      .then((data) => {
        insertCaptchaImage(data);
      });

    window.vajbcha = window.vajbcha || {};
    window.vajbcha[inputName] = {
      value: () => {
        return `${captchaId};${captchaInput}`;
      },
      reload: () => {
        reloadCaptchaImage();
      },
      remove: () => {
        if (container) {
          container.remove();
          container = null;
        }
        if (me.parentElement) {
          me.remove();
        }
        if (window.vajbcha[inputName]) {
          delete window.vajbcha[inputName];
        }
      },
    };
  });

  container.appendChild(iframe);
})();
