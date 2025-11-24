/* ---------------- CONFIG ---------------- */
// CHANGED: Leave empty to use the current server (fixes localhost/port issues)
const API_BASE = ""; 

/* ---------------- HELPERS ---------------- */
const qs = s => document.querySelector(s);
const qsa = s => document.querySelectorAll(s);

let stateDistrictMap = {}; // state → district list mapping

/* ---------------- TAB SWITCHING ---------------- */
// (Kept as is, though mostly used if you merge pages back together)
if(qsa(".tab").length > 0) {
    qsa(".tab").forEach(btn => {
      btn.addEventListener("click", () => {
        qsa(".tab").forEach(t => t.classList.remove("active"));
        qsa(".tab-body").forEach(b => b.classList.remove("show"));

        btn.classList.add("active");
        qs(`#${btn.dataset.target}`).classList.add("show");
      });
    });
}

/* ---------------- LOAD META FOR FERTILIZER DROPDOWN ---------------- */
async function loadMeta() {
  // Only run if the fertilizer crop dropdown exists
  if(!qs("#f_crop")) return; 

  try {
    const res = await fetch(`${API_BASE}/meta`);
    const meta = await res.json();

    const cropSelect = qs("#f_crop");
    cropSelect.innerHTML = meta.fert_crop_classes
      .map(c => `<option>${c}</option>`)
      .join("");

  } catch {
    // Fallback if API fails
    qs("#f_crop").innerHTML = `
      <option>Maize</option>
      <option>Sugarcane</option>
      <option>Cotton</option>
      <option>Paddy</option>`;
  }
}

/* ---------------- LOAD STATES & DISTRICTS ---------------- */
async function loadStateDistricts() {
  // Only run if state dropdown exists (Crop Page)
  if(!qs("#state")) return;

  try {
    const res = await fetch(`${API_BASE}/states`);
    const data = await res.json();

    const stateSel = qs("#state");
    const districtSel = qs("#district");

    stateDistrictMap = data.mapping;

    // Fill states
    stateSel.innerHTML = `<option value="">Select State</option>`;
    data.states.forEach(s => {
      stateSel.innerHTML += `<option value="${s}">${s}</option>`;
    });

    // On state change → load districts
    stateSel.onchange = () => {
      const state = stateSel.value;
      districtSel.innerHTML = `<option value="">Select District</option>`;

      if (state && stateDistrictMap[state]) {
        stateDistrictMap[state].forEach(d => {
          districtSel.innerHTML += `<option value="${d}">${d}</option>`;
        });
      }
    };

  } catch (err) {
    console.error("Could not load states:", err);
  }
}

/* ---------------- CROP PREDICTION ---------------- */
if(qs("#predictCropBtn")) {
    qs("#predictCropBtn").onclick = async () => {
      const btn = qs("#predictCropBtn");
      const originalText = btn.innerText;
      btn.innerText = "Predicting...";
      btn.disabled = true;

      const payload = {
        state: qs("#state").value,
        district: qs("#district").value,
        N: Number(qs("#N").value),
        P: Number(qs("#P").value),
        K: Number(qs("#K").value),
        temperature: Number(qs("#temperature").value),
        humidity: Number(qs("#humidity").value),
        ph: Number(qs("#ph").value),
        rainfall: Number(qs("#rainfall").value)
      };

      try {
        // CHANGED: Updated URL to match app.py (/api/predict_crop)
        const res = await fetch(`${API_BASE}/api/predict_crop`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
            // CHANGED: data.crop -> data.recommended_crop (Matches backend)
            qs("#cropResult").innerHTML = `
            <div class="result-card" style="background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #c3e6cb;">
              🌾 Recommended Crop: <br>
              <strong style="font-size: 1.5rem; text-transform: uppercase;">${data.recommended_crop}</strong>
            </div>`;
        } else {
            qs("#cropResult").textContent = "Error: " + (data.error || "Prediction failed");
        }

      } catch {
        qs("#cropResult").textContent = "Server unreachable.";
      }
      
      btn.innerText = originalText;
      btn.disabled = false;
    };
}

/* ---------------- FERTILIZER PREDICTION ---------------- */
if(qs("#predictFertBtn")) {
    qs("#predictFertBtn").onclick = async () => {
      const btn = qs("#predictFertBtn");
      const originalText = btn.innerText;
      btn.innerText = "Predicting...";
      btn.disabled = true;

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
        // CHANGED: Matches app.py route
        const res = await fetch(`${API_BASE}/predict_fertilizer`, {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
          qs("#fertResult").innerHTML = `
            <div class="result-card" style="background: #d4edda; color: #155724; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #c3e6cb;">
              🧪 Recommended Fertilizer: <br>
              <strong style="font-size: 1.5rem; text-transform: uppercase;">${data.fertilizer}</strong>
            </div>`;
        } else {
          qs("#fertResult").textContent = "Error: " + (data.error || "Prediction failed");
        }

      } catch {
        qs("#fertResult").textContent = "Server unreachable.";
      }

      btn.innerText = originalText;
      btn.disabled = false;
    };
}

/* ---------------- SAMPLE AUTO-FILL ---------------- */
if(qs("#btnSamples")) {
    qs("#btnSamples").onclick = () => {
      // Only fill if elements exist
      if(qs("#N")) {
          qs("#N").value = 90;
          qs("#P").value = 42;
          qs("#K").value = 43;
          qs("#ph").value = 6.5;
          qs("#temperature").value = 28;
          qs("#humidity").value = 75;
          qs("#rainfall").value = 220;
      }

      if(qs("#f_crop")) {
          qs("#f_crop").value = "Maize";
          qs("#f_soil").value = "Loamy";
          qs("#f_N").value = 80;
          qs("#f_P").value = 30;
          qs("#f_K").value = 40;
          qs("#f_moisture").value = 35;
          qs("#f_temperature").value = 30;
          qs("#f_humidity").value = 60;
      }
    };
}

/* ---------------- INIT ---------------- */
// Load data only if we are on the correct pages
if(qs("#f_crop")) loadMeta();
if(qs("#state")) loadStateDistricts();