const chatArea = document.getElementById("chatArea");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const getTopicBtn = document.getElementById("getTopicBtn");
const topicSelect = document.getElementById("topic");
const newChatBtn = document.getElementById("newChatBtn");
const chatHistoryList = document.getElementById("chatHistoryList");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");

let allChats = JSON.parse(localStorage.getItem("allChats") || "[]");
let currentChatIndex = null;

// Belge yükleme
uploadBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append("file", file);

        fetch("/upload", {
            method: "POST",
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                appendMessage("bot", "❌ Yükleme hatası: " + data.error);
            } else {
                appendMessage("user", "📂 Yüklendi: " + data.filename);
                if (data.content) {
                    appendMessage("bot", "```" + data.content + "```", true);
                } else {
                    appendMessage("bot", "Dosya başarıyla yüklendi ama önizleme desteklenmiyor.");
                }
            }
        })
        .catch(err => {
            appendMessage("bot", "❌ Sunucu hatası: " + err.message);
        });
    }
});

// Mesaj ekleme (kod bloklarını ayırır)
function appendMessage(sender, text, typing = false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = sender === "user" ? "msg user" : "msg bot";
    chatArea.appendChild(msgDiv);
    chatArea.scrollTop = chatArea.scrollHeight;

    const codeBlockRegex = /```([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(text)) !== null) {
        const beforeText = text.slice(lastIndex, match.index).trim();
        if (beforeText) {
            const p = document.createElement("p");
            p.textContent = beforeText;
            msgDiv.appendChild(p);
        }

        const codeContent = match[1].replace(/^(\w+)?\n/, "");
        const pre = document.createElement("pre");
        const code = document.createElement("code");
        code.textContent = codeContent;
        pre.appendChild(code);

        const copyBtn = document.createElement("button");
        copyBtn.textContent = "Kopyala";
        copyBtn.className = "copyBtn";
        copyBtn.addEventListener("click", () => {
            navigator.clipboard.writeText(codeContent);
            alert("Kod kopyalandı!");
        });

        msgDiv.appendChild(pre);
        msgDiv.appendChild(copyBtn);

        lastIndex = codeBlockRegex.lastIndex;
    }

    const afterText = text.slice(lastIndex).trim();
    if (afterText) {
        const p = document.createElement("p");
        if (typing) {
            let i = 0;
            const interval = setInterval(() => {
                p.textContent += afterText[i];
                i++;
                if (i >= afterText.length) clearInterval(interval);
                chatArea.scrollTop = chatArea.scrollHeight;
            }, 30);
        } else {
            p.textContent = afterText;
        }
        msgDiv.appendChild(p);
    }

    if (currentChatIndex !== null) {
        allChats[currentChatIndex] = chatArea.innerHTML;
        localStorage.setItem("allChats", JSON.stringify(allChats));
    }
}

// Mesaj gönderme
function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;
    appendMessage("user", message);
    messageInput.value = "";

    fetch("/send_message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
        appendMessage("bot", data.reply, true);
    })
    .catch(err => {
        appendMessage("bot", "Hata: " + err.message);
    });
}

sendBtn.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

// Konu seçme
getTopicBtn.addEventListener("click", () => {
    const topic = topicSelect.value;
    fetch("/get_topic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            appendMessage("bot", data.error, true);
        } else {
            let fullText = data.explanation + "\n\n```" + data.code + "```" + "\n" + data.warning;
            appendMessage("bot", fullText, true);
        }
    })
    .catch(err => {
        appendMessage("bot", "❌ Hata: " + err.message);
    });
});

// Yeni sohbet
newChatBtn.addEventListener("click", () => {
    const currentChat = chatArea.innerHTML.trim();
    if (currentChat !== "" && currentChatIndex !== null) {
        allChats[currentChatIndex] = currentChat;
    }
    allChats.push("");
    currentChatIndex = allChats.length - 1;
    chatArea.innerHTML = "";
    localStorage.setItem("allChats", JSON.stringify(allChats));
    renderChatHistory();
});

// Sohbet geçmişini listele
function renderChatHistory() {
    chatHistoryList.innerHTML = "";
    allChats.forEach((chat, index) => {
        const li = document.createElement("li");
        li.textContent = "Sohbet " + (index + 1);
        li.addEventListener("click", () => {
            currentChatIndex = index;
            chatArea.innerHTML = allChats[index];
        });
        chatHistoryList.appendChild(li);
    });
}

// Başlangıç durumu
if (allChats.length === 0) {
    allChats.push("");
    currentChatIndex = 0;
} else {
    currentChatIndex = allChats.length - 1;
    chatArea.innerHTML = allChats[currentChatIndex];
}
renderChatHistory();
