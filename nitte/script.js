document.getElementById("form").addEventListener("submit", function (e) {
    e.preventDefault();

    const crop = document.getElementById("crop").value;
    const temp = document.getElementById("temp").value;
    const humidity = document.getElementById("humidity").value;
    const rainfall = document.getElementById("rainfall").value;

    fetch("http://127.0.0.1:5000/check", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            crop: crop,
            temperature: temp,
            humidity: humidity,
            rainfall: rainfall
        })
    })
        .then(res => res.json())
        .then(data => {
            document.getElementById("output").innerHTML = `
                <div class="result-card">
                    <div class="result-title">${data.result}</div>
                    <div class="section-title">Top Recommended Crops</div>
                    <ul class="result-list">
                        ${data.top_crops.map(x => `
                            <li>${x.crop} (${(x.confidence * 100).toFixed(2)}%)</li>
                        `).join("")}
                    </ul>
                </div>
            `;
        })
        .catch(err => {
            document.getElementById("output").innerHTML = "Error connecting to server.";
        });
});
