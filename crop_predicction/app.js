/* ---------------- CONFIG ---------------- */
const API_BASE = "http://127.0.0.1:5000";

/* ---------------- HELPERS ---------------- */
const qs = s => document.querySelector(s);
const qsa = s => document.querySelectorAll(s);

/* State → District Mapping */
let stateDistrictMap = {};

/* ---------------- TAB SWITCHING ---------------- */
qsa(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    qsa(".tab").forEach(t => t.classList.remove("active"));
    qsa(".tab-body").forEach(b => b.classList.remove("show"));
    btn.classList.add("active");
    qs(`#${btn.dataset.target}`).classList.add("show");
  });
});

/* ---------------- LOAD META (FERTILIZER CROPS) ---------------- */
async function loadMeta() {
  try {
    const res = await fetch(`${API_BASE}/meta`);
    if (!res.ok) throw new Error();

    const meta = await res.json();
    const cropSelect = qs("#f_crop");

    cropSelect.innerHTML = "";
    meta.fert_crop_classes.forEach(c => {
      cropSelect.innerHTML += `<option>${c}</option>`;
    });

  } catch {
    const fallback = ["Maize","Sugarcane","Cotton","Tobacco","Paddy","Barley","Wheat","Millets","Oil seeds","Pulses","Ground Nuts"];
    qs("#f_crop").innerHTML = fallback.map(c => `<option>${c}</option>`).join("");
  }
}

/* ---------------- LOAD STATES & DISTRICTS ---------------- */
async function loadStateDistricts() {
  try {
    const res = await fetch(`${API_BASE}/states`);
    if (!res.ok) throw new Error("State loading failed");

    const data = await res.json();
    stateDistrictMap = data.mapping;

    const stateSel = qs("#state");
    const distSel = qs("#district");

    stateSel.innerHTML = `<option value="">Select State</option>`;
    data.states.forEach(s => {
      stateSel.innerHTML += `<option value="${s}">${s}</option>`;
    });

    stateSel.addEventListener("change", () => {
      const selected = stateSel.value;
      distSel.innerHTML = `<option value="">Select District</option>`;

      if (selected && stateDistrictMap[selected]) {
        stateDistrictMap[selected].forEach(d => {
          distSel.innerHTML += `<option value="${d}">${d}</option>`;
        });
      }
    });

  } catch (err) {
    console.error("Failed to load states/districts:", err);
  }
}

/* ---------------- CROP PREDICTION ---------------- */
qs("#predictCropBtn").addEventListener("click", async () => {
  const payload = {
    state: qs("#state").value || "",
    district: qs("#district").value || "",
    N: Number(qs("#N").value),
    P: Number(qs("#P").value),
    K: Number(qs("#K").value),
    temperature: Number(qs("#temperature").value),
    humidity: Number(qs("#humidity").value),
    ph: Number(qs("#ph").value),
    rainfall: Number(qs("#rainfall").value)
  };

  try {
    const res = await fetch(`${API_BASE}/predict_crop`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok) {
      qs("#cropResult").innerHTML = `
        <div class="result-card">
          🌾 Recommended Crop: <strong>${data.crop}</strong>
        </div>
      `;
    } else {
      qs("#cropResult").textContent = "Error predicting crop.";
    }

  } catch {
    qs("#cropResult").textContent = "Server unreachable.";
  }
});

/* ---------------- FERTILIZER PREDICTION ---------------- */
qs("#predictFertBtn").addEventListener("click", async () => {
  const payload = {
    crop: qs("#f_crop").value,
    soil_type: qs("#f_soil").value,
    N: Number(qs("#f_N").value),
    P: Number(qs("#f_P").value),
    K: Number(qs("#f_K").value),
    moisture: Number(qs("#f_moisture").value),
    temperature: Number(qs("#f_temperature").value),
    humidity: Number(qs("#f_humidity").value)
  };

  try {
    const res = await fetch(`${API_BASE}/predict_fertilizer`, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    if (res.ok) {
      qs("#fertResult").innerHTML = `
        <div class="result-card">
          🧪 Recommended Fertilizer: <strong>${data.fertilizer}</strong>
        </div>
      `;
    } else {
      qs("#fertResult").textContent = "Error predicting fertilizer.";
    }

  } catch {
    qs("#fertResult").textContent = "Server unreachable.";
  }
});

/* ---------------- SAMPLE AUTO FILL ---------------- */
qs("#btnSamples").addEventListener("click", () => {
  qs("#N").value = 90;
  qs("#P").value = 42;
  qs("#K").value = 43;
  qs("#ph").value = 6.5;
  qs("#temperature").value = 28;
  qs("#humidity").value = 75;
  qs("#rainfall").value = 220;

  qs("#f_crop").value = "Maize";
  qs("#f_soil").value = "Loamy";
  qs("#f_N").value = 80;
  qs("#f_P").value = 30;
  qs("#f_K").value = 40;
  qs("#f_moisture").value = 35;
  qs("#f_temperature").value = 30;
  qs("#f_humidity").value = 60;
});

/* ---------------- INIT ---------------- */
loadMeta();
loadStateDistricts();
