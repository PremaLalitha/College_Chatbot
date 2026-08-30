// ============================================================
// GLOBAL USER & SYSTEM STATE
// ============================================================
let userDetails = {
    name: "",
    location: "",
    source: ""
};

// ============================================================
// THEME MANAGEMENT (DARK / LIGHT MODE)
// ============================================================
function initTheme() {
    const savedTheme = localStorage.getItem("nec_theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("nec_theme", newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
        themeBtn.innerHTML = theme === "dark" 
            ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
            : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
    }
}

// Initialize theme on script load
initTheme();

// ============================================================
// HANDLE SURVEY SUBMISSION
// ============================================================
function handleSurveySubmit(event) {
    event.preventDefault();

    const nameInput = document.getElementById("user-name").value.trim();
    const locationInput = document.getElementById("user-location").value.trim();
    const sourceSelect = document.getElementById("user-source").value;

    if (!nameInput || !locationInput || !sourceSelect) {
        return;
    }

    // Save user details
    userDetails.name = nameInput;
    userDetails.location = locationInput;
    userDetails.source = sourceSelect;

    // Hide Survey Modal
    document.getElementById("survey-modal").classList.add("hidden");

    // Enable Controls
    const inputField = document.getElementById("question-input");
    const sendButton = document.getElementById("send-btn");

    inputField.disabled = false;
    sendButton.disabled = false;
    inputField.focus();

    // Display personalized greeting from bot
    addMessage(`Hello **${userDetails.name}**! Welcome visitor from **${userDetails.location}**!\nHow can I help you today regarding National Engineering College?`, "bot");
}

// ============================================================
// RESET CHAT SESSION
// ============================================================
function resetChatSession() {
    if (!confirm("Are you sure you want to reset the chat session?")) return;

    const chatContainer = document.getElementById("chat-container");
    chatContainer.innerHTML = `
        <div class="welcome" id="welcome-card">
            <div class="welcome-badge">Official AI Assistant</div>
            <h2>Welcome to NEC Chatbot</h2>
            <p>Get instant answers about admissions, B.E./B.Tech courses, hostel facilities, placements, and campus life.</p>
            
            <div class="quick-pills-label">Quick Suggestions:</div>
            <div class="quick-pills-grid">
                <button class="pill-btn" onclick="quickAsk('What UG courses are available at NEC?')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>
                    <span>UG Courses</span>
                </button>
                <button class="pill-btn" onclick="quickAsk('What is the highest placement package?')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                    <span>Placements & Packages</span>
                </button>
                <button class="pill-btn" onclick="quickAsk('Who is the Principal of NEC?')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M5 21V7l7-4 7 4v14"></path></svg>
                    <span>Principal & Founder</span>
                </button>
                <button class="pill-btn" onclick="quickAsk('Who is the Head of Department of CSE?')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    <span>HOD of CSE</span>
                </button>
                <button class="pill-btn" onclick="quickAsk('What hostel facilities and food timings are available?')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
                    <span>Hostel & Mess</span>
                </button>
                <button class="pill-btn" onclick="quickAsk('Does NEC provide bus transportation routes?')">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2"></rect><path d="M7 20h10"></path><circle cx="7" cy="16" r="1.5"></circle><circle cx="17" cy="16" r="1.5"></circle></svg>
                    <span>Bus Transport</span>
                </button>
            </div>
        </div>
    `;

    document.getElementById("survey-modal").classList.remove("hidden");
    document.getElementById("question-input").disabled = true;
    document.getElementById("send-btn").disabled = true;
}

// ============================================================
// QUICK SUGGESTION PILLS
// ============================================================
function quickAsk(questionText) {
    const input = document.getElementById("question-input");
    if (input.disabled) {
        alert("Please complete the quick details modal first!");
        return;
    }
    input.value = questionText;
    sendQuestion();
}

// ============================================================
// FAQ DATABASE
// ============================================================
const faqQuestions = {
    admission: [
        "What documents are required for admission?",
        "What is the admission procedure?",
        "What is the TNEA requirement?",
        "What documents are required for First Graduate students?",
        "What should I bring for admission?",
        "How many photocopy sets are required?",
        "How can I reach NEC?",
        "What is the official admission contact?"
    ],
    courses: [
        "What courses are available at NEC?",
        "What courses can I join after 12th?",
        "Is CSE available at NEC?",
        "Does NEC have AI and Data Science?",
        "What PG courses are available?",
        "Does NEC offer B.Tech IT?",
        "Does NEC offer ECE & EEE?"
    ],
    hostel: [
        "Is hostel available for boys and girls?",
        "What hostel facilities are available?",
        "What are the hostel food timings?",
        "Is Wi-Fi available in the hostel?",
        "Does the hostel have a mess?"
    ],
    transport: [
        "Does NEC provide bus transportation?",
        "What are the NEC bus routes?",
        "Is there a bus from Tirunelveli?",
        "Is there a bus from Tuticorin?",
        "Who is the Transport Manager?"
    ],
    placement: [
        "Who is the Placement Convener?",
        "What is the highest package at NEC?",
        "What is the average salary in CSE?",
        "Which companies recruit from NEC?",
        "What placement training does NEC provide?"
    ],
    scholarship: [
        "What scholarships are available?",
        "What is the Merit Scholarship?",
        "What is the Talent Scholarship?",
        "Does NEC provide hostel fee scholarships?"
    ],
    campus: [
        "What facilities are available at NEC?",
        "Does NEC have a cafeteria?",
        "Does NEC provide healthcare?",
        "Does NEC have a Common Computer Centre?",
        "Does NEC have sports facilities?"
    ]
};

// ============================================================
// AUTO SCROLL UTILITY
// ============================================================
function scrollToBottom() {
    const chat = document.getElementById("chat-container");
    setTimeout(() => {
        chat.scrollTo({
            top: chat.scrollHeight,
            behavior: "smooth"
        });
    }, 50);
}

// ============================================================
// FAQ DRAWER UTILITIES
// ============================================================
function showQuestions(category) {
    const section = document.getElementById("questions-section");
    const title = document.getElementById("questions-title");
    const list = document.getElementById("questions-list");

    list.innerHTML = "";
    title.textContent = category.charAt(0).toUpperCase() + category.slice(1) + " Questions";

    if (faqQuestions[category]) {
        faqQuestions[category].forEach(function(question) {
            const button = document.createElement("button");
            button.className = "question-button";
            button.textContent = question;

            button.onclick = function() {
                document.getElementById("question-input").value = question;
                closeQuestions();
                sendQuestion();
            };

            list.appendChild(button);
        });
    }

    section.classList.remove("hidden");
}

function closeQuestions() {
    document.getElementById("questions-section").classList.add("hidden");
}

// ============================================================
// TYPING INDICATOR
// ============================================================
function showTypingIndicator() {
    const chat = document.getElementById("chat-container");
    const wrapper = document.createElement("div");
    wrapper.className = "message-wrapper bot-wrapper";
    wrapper.id = "typing-wrapper";

    wrapper.innerHTML = `
        <div class="avatar bot-avatar">NEC</div>
        <div class="message bot typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    chat.appendChild(wrapper);
    scrollToBottom();
}

function removeTypingIndicator() {
    const typing = document.getElementById("typing-wrapper");
    if (typing) typing.remove();
}

// ============================================================
// ADD MESSAGE TO CHAT CANVAS
// ============================================================
function addMessage(text, type) {
    const chat = document.getElementById("chat-container");
    const wrapper = document.createElement("div");

    wrapper.className = `message-wrapper ${type}-wrapper`;

    const avatar = document.createElement("div");
    avatar.className = `avatar ${type}-avatar`;
    avatar.textContent = type === "bot" ? "NEC" : "YOU";

    const msg = document.createElement("div");
    msg.className = `message ${type}`;

    if (type === "bot") {
        msg.innerHTML = formatAnswer(text);

        // Action bar for bot responses
        const actions = document.createElement("div");
        actions.className = "message-actions";

        const copyBtn = document.createElement("button");
        copyBtn.className = "action-btn";
        copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> <span>Copy</span>`;
        copyBtn.onclick = () => copyToClipboard(text, copyBtn);

        const speakBtn = document.createElement("button");
        speakBtn.className = "action-btn";
        speakBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg> <span>Listen</span>`;
        speakBtn.onclick = () => readAloud(text);

        actions.appendChild(copyBtn);
        actions.appendChild(speakBtn);
        msg.appendChild(actions);

    } else {
        msg.textContent = text;
    }

    wrapper.appendChild(avatar);
    wrapper.appendChild(msg);

    chat.appendChild(wrapper);
    scrollToBottom();

    return wrapper;
}

// ============================================================
// COPY TO CLIPBOARD
// ============================================================
function copyToClipboard(text, btn) {
    // Strip markdown formatting for clean clipboard text
    const cleanText = text.replace(/\*\*(.*?)\*\*/g, "$1").replace(/^\s*#+\s*/gm, "");
    navigator.clipboard.writeText(cleanText).then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> <span>Copied</span>`;
        setTimeout(() => { btn.innerHTML = original; }, 2000);
    }).catch(err => {
        console.error("Clipboard copy error:", err);
    });
}

// ============================================================
// TEXT TO SPEECH (READ ALOUD)
// ============================================================
function readAloud(text) {
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop any existing speech
        const cleanText = text.replace(/[\*#]/g, "");
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        window.speechSynthesis.speak(utterance);
    } else {
        alert("Text-to-speech is not supported in your browser.");
    }
}

// ============================================================
// FORMAT BOT ANSWER
// ============================================================
function formatAnswer(text) {
    if (!text) return "";

    let html = escapeHtml(text);

    // Headers: ####, #####, ###### (h4) and #, ##, ### (h3)
    html = html.replace(/^\s*#{4,6}\s*(.*?)$/gm, "<h4>$1</h4>");
    html = html.replace(/^\s*#{1,3}\s*(.*?)$/gm, "<h3>$1</h3>");

    // Bold text: **text**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Italic text: *text*
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");

    // Numbered lists: 1. text
    html = html.replace(/^\s*\d+\.\s+(.*?)$/gm, "<li>$1</li>");

    // Bullet lists: - text or * text or • text
    html = html.replace(/^\s*[-*•]\s+(.*?)$/gm, "<li>$1</li>");

    // Wrap consecutive <li> in <ul>
    html = html.replace(/(?:<li>.*?<\/li>\s*)+/g, "<ul>$&</ul>");

    // Line breaks
    html = html.replace(/\n/g, "<br>");

    // Clean up excessive line breaks around structural HTML elements
    html = html.replace(/(?:<br>\s*)+<(h[34]|ul|ol)/gi, "<$1");
    html = html.replace(/<\/(h[34]|ul|ol)>\s*(?:<br>\s*)+/gi, "</$1>");

    return html;
}

// ============================================================
// ESCAPE HTML TO PREVENT XSS
// ============================================================
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================
// SEND QUESTION TO BACKEND
// ============================================================
async function sendQuestion() {
    const input = document.getElementById("question-input");
    const question = input.value.trim();

    if (!question) return;

    // Display User Message
    addMessage(question, "user");
    input.value = "";

    // Show Typing Indicator
    showTypingIndicator();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ 
                question: question,
                user_name: userDetails.name,
                user_location: userDetails.location,
                user_source: userDetails.source
            })
        });

        if (!response.ok) {
            throw new Error(`Server status ${response.status}`);
        }

        const text = await response.text();
        const data = text ? JSON.parse(text) : {};
        removeTypingIndicator();

        // Display Bot Response
        addMessage(data.answer || "Thank you for asking. Please contact National Engineering College for more details.", "bot");

    } catch (error) {
        console.error("Chat Request Error:", error);
        removeTypingIndicator();
        addMessage("Unable to connect to the NEC chatbot. Please try again or contact principal@nec.edu.in.", "bot");
    }
}

// ============================================================
// ENTER KEY EVENT LISTENER
// ============================================================
document.getElementById("question-input").addEventListener("keydown", function(event) {
    if (event.key === "Enter" && !this.disabled) {
        event.preventDefault();
        sendQuestion();
    }
});