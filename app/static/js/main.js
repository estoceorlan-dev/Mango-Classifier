document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  const imageInput = document.getElementById("imageInput");
  const previewCard = document.getElementById("previewCard");
  const previewImage = document.getElementById("previewImage");
  const previewEmpty = document.getElementById("previewEmpty");
  const previewLabel = document.getElementById("previewLabel");
  const fileName = document.getElementById("fileName");
  const fileType = document.getElementById("fileType");
  const fileSize = document.getElementById("fileSize");
  const validationMessage = document.getElementById("validationMessage");
  const validationAlert = document.getElementById("validationAlert");
  const submitButton = document.getElementById("submitButton");
  const buttonText = submitButton?.querySelector(".button-text");
  const loadingSpinner = document.getElementById("loadingSpinner");
  const dropzone = document.getElementById("dropzone");
  const dropzoneHint = document.getElementById("dropzoneHint");
  const actionHelper = document.getElementById("actionHelper");
  const resultModal = document.getElementById("resultModal");
  const openCameraBtn = document.getElementById("openCameraBtn");
  const stopCameraBtn = document.getElementById("stopCameraBtn");
  const cameraVideo = document.getElementById("cameraVideo");
  const captureBtn = document.getElementById("captureBtn");
  const cancelCaptureBtn = document.getElementById("cancelCaptureBtn");
  const cameraButtonRow = document.getElementById("cameraButtonRow");

  const allowedExtensions = ["png", "jpg", "jpeg", "webp"];
  const maxFileSizeBytes = 10 * 1024 * 1024;
  let mediaStream = null;
  let previewObjectUrl = null;
  let isCameraActive = false;

  function showValidation(message) {
    if (!validationMessage) {
      return;
    }

    validationMessage.textContent = message;
    validationMessage.classList.remove("d-none");
  }

  function clearValidation() {
    if (!validationMessage) {
      return;
    }

    validationMessage.textContent = "";
    validationMessage.classList.add("d-none");
    validationAlert?.classList.add("d-none");
  }

  function resetPreview() {
    if (!previewImage || !fileName || !previewCard) {
      return;
    }

    if (previewObjectUrl) {
      URL.revokeObjectURL(previewObjectUrl);
      previewObjectUrl = null;
    }

    previewImage.removeAttribute("src");
    previewImage.classList.add("d-none");
    cameraVideo?.classList.add("d-none");
    previewEmpty?.classList.remove("d-none");
    if (previewLabel) {
      previewLabel.textContent = "Your photo";
    }
    fileName.textContent = "Waiting for a mango photo or camera capture";
    if (fileType) {
      fileType.textContent = "No photo chosen";
    }
    if (fileSize) {
      fileSize.textContent = "0 MB";
    }
  }

  function validateFile(file) {
    if (!file) {
      return "Please choose an image file.";
    }

    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!extension || !allowedExtensions.includes(extension)) {
      return "Only PNG, JPG, JPEG, and WEBP files are allowed.";
    }

    if (!file.type.startsWith("image/")) {
      return "The selected file is not a valid image.";
    }

    if (file.size > maxFileSizeBytes) {
      return "The selected image is too large. Please use an image smaller than 10 MB.";
    }

    return "";
  }

  function formatFileSize(size) {
    if (!size) {
      return "0 MB";
    }

    return `${(size / (1024 * 1024)).toFixed(2)} MB`;
  }

  function updateSelectionState(hasSelection) {
    if (submitButton) {
      submitButton.disabled = !hasSelection;
    }

    if (actionHelper) {
      actionHelper.textContent = hasSelection
        ? "Your photo is ready. If it looks clear, continue to see the closest mango match."
        : "Choose a mango photo first to continue.";
    }

    if (dropzoneHint) {
      dropzoneHint.textContent = hasSelection
        ? "You can keep this photo, replace it, or switch to the camera."
        : "Drag a photo here or click to choose one from your files.";
    }
  }

  function renderPreview(file, previewSrc) {
    if (!previewCard || !previewImage || !fileName) {
      return;
    }

    fileName.textContent = file.name;
    previewImage.src = previewSrc;
    previewImage.classList.remove("d-none");
    previewEmpty?.classList.add("d-none");

    if (fileType) {
      fileType.textContent = (file.type || "Unknown type").replace("image/", "").toUpperCase();
    }

    if (fileSize) {
      fileSize.textContent = formatFileSize(file.size);
    }

    updateSelectionState(true);
  }

  function showCameraState() {
    isCameraActive = true;
    clearValidation();
    previewImage?.classList.add("d-none");
    previewEmpty?.classList.add("d-none");
    cameraVideo?.classList.remove("d-none");
    cameraButtonRow?.classList.remove("d-none");
    openCameraBtn?.classList.add("d-none");
    stopCameraBtn?.classList.remove("d-none");

    if (previewLabel) {
      previewLabel.textContent = "Camera view";
    }

    if (fileName) {
      fileName.textContent = "Position the mango clearly, then take the photo";
    }

    if (fileType) {
      fileType.textContent = "Camera ready";
    }

    if (fileSize) {
      fileSize.textContent = "Waiting";
    }

    if (actionHelper) {
      actionHelper.textContent = "Take a photo when the mango is clear and easy to see.";
    }
  }

  function handleValidFile(file) {
    clearValidation();
    stopCamera(true);

    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result;
      if (typeof result === "string") {
        renderPreview(file, result);
      }
    };
    reader.readAsDataURL(file);
  }

  function clearSelection() {
    imageInput.value = "";
    clearValidation();
    stopCamera(true);
    resetPreview();
    updateSelectionState(false);
  }

  imageInput?.addEventListener("change", (event) => {
    const selectedFile = event.target.files?.[0];
    const validationError = validateFile(selectedFile);

    if (validationError) {
      showValidation(validationError);
      imageInput.value = "";
      clearSelection();
      return;
    }

    handleValidFile(selectedFile);
  });

  form?.addEventListener("submit", (event) => {
    const selectedFile = imageInput?.files?.[0];
    const validationError = validateFile(selectedFile);

    if (validationError) {
      event.preventDefault();
      showValidation(validationError);
      return;
    }

    clearValidation();

    if (submitButton) {
      submitButton.disabled = true;
    }

    if (buttonText) {
      buttonText.textContent = "Analyzing...";
    }

    loadingSpinner?.classList.remove("d-none");
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone?.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.add("is-active");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropzone?.addEventListener(eventName, (event) => {
      event.preventDefault();
      dropzone.classList.remove("is-active");
    });
  });

  dropzone?.addEventListener("drop", (event) => {
    const droppedFile = event.dataTransfer?.files?.[0];
    const validationError = validateFile(droppedFile);

    if (validationError) {
      showValidation(validationError);
      clearSelection();
      return;
    }

    if (event.dataTransfer?.files?.length && imageInput) {
      imageInput.files = event.dataTransfer.files;
    }

    if (droppedFile) {
      handleValidFile(droppedFile);
    }
  });

  async function startCamera() {
    try {
      clearValidation();
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      cameraVideo.srcObject = mediaStream;
      showCameraState();
    } catch (err) {
      showValidation("Unable to access the camera. Allow camera permission or upload an image instead.");
    }
  }

  function stopCamera(keepPreview = false) {
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
      mediaStream = null;
    }

    isCameraActive = false;
    if (cameraVideo) {
      cameraVideo.srcObject = null;
      cameraVideo.classList.add("d-none");
    }

    cameraButtonRow?.classList.add("d-none");
    openCameraBtn?.classList.remove("d-none");
    stopCameraBtn?.classList.add("d-none");

    if (!keepPreview && !previewImage?.getAttribute("src")) {
      resetPreview();
      updateSelectionState(false);
    } else if (!keepPreview && previewImage?.getAttribute("src")) {
      if (previewLabel) {
        previewLabel.textContent = "Your photo";
      }
      previewImage.classList.remove("d-none");
      if (actionHelper) {
        actionHelper.textContent = "Your photo is ready. If it looks clear, continue to see the closest mango match.";
      }
    }
  }

  openCameraBtn?.addEventListener("click", () => {
    startCamera();
  });

  stopCameraBtn?.addEventListener("click", () => {
    stopCamera();
  });

  cancelCaptureBtn?.addEventListener("click", () => {
    stopCamera();
  });

  captureBtn?.addEventListener("click", async () => {
    if (!cameraVideo) {
      return;
    }

    if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) {
      showValidation("The camera is not ready yet. Give it a moment, then try again.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = cameraVideo.videoWidth || 640;
    canvas.height = cameraVideo.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      showValidation("Unable to process the camera frame. Please try again.");
      return;
    }

    ctx.drawImage(cameraVideo, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) {
        showValidation("Unable to capture the image. Please try again.");
        return;
      }

      const capturedFile = new File([blob], "capture.png", { type: "image/png" });
      previewObjectUrl = URL.createObjectURL(blob);
      renderPreview(capturedFile, previewObjectUrl);
      if (previewLabel) {
        previewLabel.textContent = "Camera photo";
      }
      clearValidation();

      const fd = new FormData();
      fd.append("image", blob, "capture.png");

      if (submitButton) {
        submitButton.disabled = true;
      }

      if (buttonText) {
        buttonText.textContent = "Analyzing...";
      }

      loadingSpinner?.classList.remove("d-none");

      try {
        const resp = await fetch(window.location.pathname, { method: "POST", body: fd });
        const html = await resp.text();
        document.open();
        document.write(html);
        document.close();
      } catch (err) {
        showValidation("Capture upload failed. Please try again.");
        updateSelectionState(true);
        if (previewLabel) {
          previewLabel.textContent = "Camera photo";
        }
        if (buttonText) {
          buttonText.textContent = "See Mango Match";
        }
        loadingSpinner?.classList.add("d-none");
      } finally {
        stopCamera(true);
      }
    }, "image/png");
  });

  resetPreview();
  updateSelectionState(Boolean(imageInput?.files?.[0]));

  if (resultModal?.dataset.showOnLoad === "true" && window.bootstrap?.Modal) {
    window.requestAnimationFrame(() => {
      const modal = new window.bootstrap.Modal(resultModal);
      modal.show();
    });
  }
});
