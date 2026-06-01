const form = document.getElementById("generate-form");
const previewImage = document.getElementById("preview-image");
const emptyPreview = document.getElementById("empty-preview");
const resultJson = document.getElementById("result-json");
const statusPill = document.getElementById("status-pill");
const generateButton = document.getElementById("generate-button");
const downloadButton = document.getElementById("download-button");

let latestImageUrl = "";

function setStatus(text, state) {
  statusPill.textContent = text;
  statusPill.classList.remove("ok", "error");
  if (state) {
    statusPill.classList.add(state);
  }
}

function formPayload() {
  return {
    gender: document.getElementById("gender").value,
    age_group: document.getElementById("age_group").value,
    top: document.getElementById("top").value,
    bottom: document.getElementById("bottom").value,
    accessory: document.getElementById("accessory").value,
    output_filename: document.getElementById("output_filename").value || null,
  };
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  generateButton.disabled = true;
  downloadButton.disabled = true;
  latestImageUrl = "";
  setStatus("Generating", "");
  resultJson.textContent = "";

  try {
    const response = await fetch("/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formPayload()),
    });

    const data = await response.json();
    resultJson.textContent = JSON.stringify(data, null, 2);

    if (!response.ok || data.status !== "success") {
      throw new Error(data.message || "Generation failed.");
    }

    latestImageUrl = `${data.image_url}?t=${Date.now()}`;
    previewImage.src = latestImageUrl;
    previewImage.style.display = "block";
    emptyPreview.style.display = "none";
    downloadButton.disabled = false;
    setStatus("Ready", "ok");
  } catch (error) {
    setStatus("Error", "error");
    previewImage.style.display = "none";
    emptyPreview.style.display = "grid";
    emptyPreview.textContent = error.message;
  } finally {
    generateButton.disabled = false;
  }
});

downloadButton.addEventListener("click", () => {
  if (!latestImageUrl) {
    return;
  }

  const anchor = document.createElement("a");
  anchor.href = latestImageUrl;
  anchor.download = "outfit_visualization.png";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
});
