/* ---------------- CONFIG ---------------- */
const API_BASE = "http://127.0.0.1:5000";
const qs = s => document.querySelector(s);

/* ---------------- LOAD META (crop dropdown) ---------------- */
async function loadMeta() {
  try {
    const res = await fetch(`${API_BASE}/meta`);
    const meta = await res.json();

    const cropSel = qs("#f_crop");
    cropSel.innerHTML = "";

    meta.fert_crop_classes.forEach(c => {
      cropSel.innerHTML += `<option value="${c}">${c}</option>`;
    });

  } catch (err) {
    console.error("Crop dropdown failed:", err);
  }
}

/* ---------------- FERTILIZER PREDICTION ---------------- */
qs("#predictFertBtn").onclick = async () => {

  const payload = {
    crop: qs("#f_crop").value,
    soil_type: qs("#f_soil").value,
    N: qs("#f_N").value,
    P: qs("#f_P").value,
    K: qs("#f_K").value,
    moisture: qs("#f_moisture").value,
    temperature: qs("#f_temperature").value,
    humidity: qs("#f_humidity").value
  };

  const res = await fetch(`${API_BASE}/predict_fertilizer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const data = await res.json();

  qs("#fertResult").innerHTML =
    `<div class="result-card">🧪 Recommended Fertilizer: <strong>${data.fertilizer}</strong></div>`;
};

/* ---------------- INIT ---------------- */
loadMeta();
