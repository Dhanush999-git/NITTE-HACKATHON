function appendBubble(text, type) {
    let box = document.getElementById("chatBox");

    let div = document.createElement("div");
    div.className = "bubble " + type;
    div.innerHTML = text;

    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function quick(keyword) {
    processMessage(keyword);
}

function sendMessage() {
    let input = document.getElementById("userInput").value.trim();
    if (input === "") return;

    appendBubble(input, "user");
    document.getElementById("userInput").value = "";

    processMessage(input.toLowerCase());
}

function botTyping() {
    appendBubble("⏳ Typing...", "bot");
}

function replaceLastBotMessage(newText) {
    let box = document.getElementById("chatBox");
    let bubbles = box.getElementsByClassName("bot");
    let last = bubbles[bubbles.length - 1];
    last.innerHTML = newText;
}

function processMessage(msg) {
    botTyping();

    setTimeout(() => {

        if (msg.includes("crop")) {
            replaceLastBotMessage(`
                🌾 <b>Crop Recommendation</b><br>
                Go to: <u>crop.html</u><br>
                ➤ Enter N, P, K<br>
                ➤ Enter pH<br>
                ➤ Enter weather values<br><br>
                Click Predict!
            `);
        }

        else if (msg.includes("weather") || msg.includes("suitability")) {
            replaceLastBotMessage(`
                🌤️ <b>Weather Suitability Checker</b><br>
                Link: <u>weather.html</u><br>
                ➤ Enter location<br>
                ➤ See climate match for your crop
            `);
        }

        else if (msg.includes("fertilizer") || msg.includes("npk")) {
            replaceLastBotMessage(`
                🧪 <b>Fertilizer Advisor</b><br>
                Link: <u>fertilizer.html</u><br>
                ➤ Choose soil type<br>
                ➤ Enter N, P, K levels<br>
                ➤ Click Recommend
            `);
        }

        else if (msg.includes("disease") || msg.includes("leaf") || msg.includes("infect")) {
            replaceLastBotMessage(`
                🍃 <b>Disease Detection</b><br>
                Link: <u>disease.html</u><br>
                ➤ Upload leaf photo<br>
                ➤ System identifies infection
            `);
        }

        else if (msg.includes("guide") || msg.includes("beginner")) {
            replaceLastBotMessage(`
                👨‍🌾 <b>Beginner Farmer Guidance</b><br>
                1️⃣ Soil testing<br>
                2️⃣ Crop planning<br>
                3️⃣ Fertilizer schedule<br>
                4️⃣ Watering routine<br>
                5️⃣ Disease monitoring
            `);
        }

        else {
            replaceLastBotMessage(`
                😊 How can I help you?<br><br>
                Try asking:<br>
                🌾 Crop Recommendation<br>
                🌤️ Weather Suitability<br>
                🧪 Fertilizer Advice<br>
                🍃 Disease Detection<br>
                👨‍🌾 Beginner Guide
            `);
        }

    }, 800);
}
