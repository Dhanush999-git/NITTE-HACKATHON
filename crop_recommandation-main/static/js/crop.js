// static/js/crop.js

// 1. Load States on Page Load
window.onload = function() {
    fetch('/states')
        .then(response => response.json())
        .then(data => {
            const stateSelect = document.getElementById('state');
            if(data.states) {
                data.states.forEach(state => {
                    const option = document.createElement('option');
                    option.value = state;
                    option.textContent = state;
                    stateSelect.appendChild(option);
                });
            }
        })
        .catch(error => console.error('Error loading states:', error));
};

// 2. Load Districts when State Changes
function loadDistricts() {
    const state = document.getElementById('state').value;
    const districtSelect = document.getElementById('district');
    
    // Clear existing districts
    districtSelect.innerHTML = '<option value="" disabled selected>Select District</option>';

    if(state) {
        fetch(`/districts/${state}`)
            .then(response => response.json())
            .then(data => {
                if(data.districts) {
                    data.districts.forEach(dist => {
                        const option = document.createElement('option');
                        option.value = dist;
                        option.textContent = dist;
                        districtSelect.appendChild(option);
                    });
                }
            })
            .catch(error => console.error('Error loading districts:', error));
    }
}

// 3. Handle Prediction Form Submission
document.getElementById('cropForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Stop page reload

    const btn = document.getElementById('predictCropBtn');
    btn.innerText = "Processing...";
    btn.disabled = true;

    // Collect Data
    const payload = {
        N: document.getElementById('N').value,
        P: document.getElementById('P').value,
        K: document.getElementById('K').value,
        temperature: document.getElementById('temperature').value,
        humidity: document.getElementById('humidity').value,
        ph: document.getElementById('ph').value,
        rainfall: document.getElementById('rainfall').value
    };

    // Send to Backend
    fetch('/api/predict_crop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        const resultDiv = document.getElementById('cropResult');
        
        if (data.recommended_crop) {
            resultDiv.innerHTML = `
                <div class="result-box success">
                    Recommended Crop: <br>
                    <span style="font-size: 1.5rem; text-transform: uppercase;">${data.recommended_crop}</span>
                </div>`;
        } else if (data.error) {
            resultDiv.innerHTML = `<div class="result-box error">Error: ${data.error}</div>`;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('cropResult').innerHTML = `<div class="result-box error">Failed to connect to server.</div>`;
    })
    .finally(() => {
        btn.innerText = "Predict Crop";
        btn.disabled = false;
    });
});