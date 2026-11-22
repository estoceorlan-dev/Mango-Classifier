const form = document.getElementById("uploadForm");

if (form) {
  const byId = id => document.getElementById(id);
  const input = byId("imageInput");
  const dropzone = byId("dropzone");
  const preview = byId("previewImage");
  const video = byId("cameraVideo");
  const submit = byId("submitButton");
  const camera = byId("openCameraBtn");
  const capture = byId("captureBtn");
  const message = byId("validationMessage");
  let stream = null;
  let photoUrl = "";

  function visible(element, show) {
    element.classList.toggle("d-none", !show);
  }

  function feedback(text = "") {
    message.textContent = text;
    visible(message, Boolean(text));
    byId("validationAlert")?.classList.add("d-none");
  }

  function showSelection() {
    visible(byId("previewCard"), Boolean(stream || photoUrl));
    visible(preview, Boolean(photoUrl && !stream));
    visible(video, Boolean(stream));
    visible(camera, !stream);
    visible(byId("stopCameraBtn"), Boolean(stream));
    visible(byId("cameraButtonRow"), Boolean(stream));
    byId("fileName").textContent = stream ? "Camera preview" : input.files[0]?.name || "";
    submit.disabled = Boolean(stream) || !input.files.length;
  }

  function stopCamera() {
    stream?.getTracks().forEach(track => track.stop());
    stream = null;
    video.srcObject = null;
    showSelection();
  }

  function selectPhoto() {
    stopCamera();
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    photoUrl = "";
    preview.removeAttribute("src");
    const file = input.files[0];
    let error = "";
    if (file && !/\.(png|jpe?g|webp)$/i.test(file.name)) {
      error = "Choose a JPG, PNG, or WebP image.";
    } else if (file && file.size > 10 * 1024 * 1024) {
      error = "Choose an image smaller than 10 MB.";
    }
    if (error) {
      input.value = "";
    } else if (file) {
      photoUrl = URL.createObjectURL(file);
      preview.src = photoUrl;
    }
    feedback(error);
    showSelection();
  }

  input.addEventListener("change", selectPhoto);
  for (const name of ["dragenter", "dragover", "dragleave", "drop"]) {
    dropzone.addEventListener(name, event => {
      event.preventDefault();
      dropzone.classList.toggle("is-active", name === "dragenter" || name === "dragover");
      if (name === "drop" && event.dataTransfer.files.length) {
        const files = new DataTransfer();
        files.items.add(event.dataTransfer.files[0]);
        input.files = files.files;
        selectPhoto();
      }
    });
  }

  camera.addEventListener("click", async () => {
    camera.disabled = true;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      video.srcObject = stream;
      feedback();
      showSelection();
    } catch {
      feedback("Camera unavailable. Allow camera access or choose a photo from your device.");
    } finally {
      camera.disabled = false;
    }
  });
  byId("stopCameraBtn").addEventListener("click", stopCamera);
  window.addEventListener("pagehide", stopCamera);

  capture.addEventListener("click", () => {
    if (!video.videoWidth) {
      feedback("The camera is starting. Try again in a moment.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    capture.disabled = true;
    canvas.toBlob(blob => {
      capture.disabled = false;
      if (!blob) {
        feedback("Could not capture a photo. Try again.");
        return;
      }
      const files = new DataTransfer();
      files.items.add(new File([blob], "capture.jpg", { type: blob.type }));
      input.files = files.files;
      selectPhoto();
    }, "image/jpeg", 0.92);
  });

  form.addEventListener("submit", event => {
    if (!input.files.length || stream) {
      event.preventDefault();
      feedback("Choose or capture a photo first.");
      return;
    }
    submit.disabled = true;
    submit.textContent = "Identifying…";
  });
  window.addEventListener("pageshow", () => {
    submit.textContent = "Identify variety";
    showSelection();
  });
}
