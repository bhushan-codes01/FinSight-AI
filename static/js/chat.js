const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const userQuestion = document.getElementById("userQuestion");
const statementFile = document.getElementById("statementFile");
const uploadTriggerBtn = document.getElementById("uploadTriggerBtn");
const fileChipContainer = document.getElementById("fileChipContainer");
const fileNameDisplay = document.getElementById("fileNameDisplay");
const removeFileBtn = document.getElementById("removeFileBtn");
const sendBtn = document.getElementById("sendBtn");
const chatEmptyState = document.getElementById("chatEmptyState");

// Handle text input auto-resize and button state
userQuestion.addEventListener("input", () => {
  adjustTextareaHeight();
  toggleSendButton();
});

function adjustTextareaHeight() {
  userQuestion.style.height = "auto";
  userQuestion.style.height = (userQuestion.scrollHeight - 10) + "px";
}

function toggleSendButton() {
  const isQuestionEmpty = userQuestion.value.trim() === "";
  sendBtn.disabled = isQuestionEmpty;
}

// Paperclip trigger
uploadTriggerBtn.addEventListener("click", () => {
  statementFile.click();
});

// File input change
statementFile.addEventListener("change", () => {
  if (statementFile.files.length > 0) {
    const file = statementFile.files[0];
    fileNameDisplay.textContent = file.name;
    fileChipContainer.style.display = "flex";
  } else {
    clearFile();
  }
});

// Remove file contribution
removeFileBtn.addEventListener("click", () => {
  clearFile();
});

function clearFile() {
  statementFile.value = "";
  fileChipContainer.style.display = "none";
}

// Click suggestion chips
document.querySelectorAll(".suggestion-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const question = chip.getAttribute("data-question");
    userQuestion.value = question;
    adjustTextareaHeight();
    toggleSendButton();
    submitQuestion();
  });
});

// Enter key submit handler (but permit Shift+Enter for newlines)
userQuestion.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submitQuestion();
  }
});

// Submit form
chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion();
});

function appendUserBubble(message) {
  const row = document.createElement("div");
  row.classList.add("chat-row-premium", "user-row");
  const bubble = document.createElement("div");
  bubble.classList.add("chat-bubble-premium");
  bubble.innerText = message;
  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function appendAIBubble(message) {
  const row = document.createElement("div");
  row.classList.add("chat-row-premium", "ai-row");
  
  const avatar = document.createElement("div");
  avatar.classList.add("chat-avatar-premium");
  avatar.innerHTML = "🤖";
  
  const bubble = document.createElement("div");
  bubble.classList.add("chat-bubble-premium");
  bubble.innerText = message;
  
  row.appendChild(avatar);
  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showTypingIndicator() {
  const indicator = document.createElement("div");
  indicator.classList.add("typing-indicator-premium");
  indicator.id = "typingIndicator";
  indicator.innerHTML = "<span></span><span></span><span></span>";
  chatWindow.appendChild(indicator);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById("typingIndicator");
  if (indicator) {
    indicator.remove();
  }
}

async function submitQuestion() {
  const question = userQuestion.value.trim();
  if (!question) return;

  // Hide empty state if present
  if (chatEmptyState) {
    chatEmptyState.style.display = "none";
  }

  // Display user bubble
  appendUserBubble(question);
  
  // Clear textarea & input adjustments
  userQuestion.value = "";
  userQuestion.style.height = "auto";
  toggleSendButton();

  // Create form data before clearing file trigger
  const formData = new FormData();
  formData.append("user_question", question);
  if (statementFile.files.length > 0) {
    formData.append("statement_file", statementFile.files[0]);
  }

  // Clear selected file chip
  clearFile();

  // Show typing animation
  showTypingIndicator();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      body: formData
    });
    
    removeTypingIndicator();
    
    if (response.ok) {
      const data = await response.json();
      if (data.response) {
        appendAIBubble(data.response);
      } else {
        appendAIBubble(data.error || "Unexpected AI service response.");
      }
    } else {
      if (response.status === 401) {
        appendAIBubble("⚠️ Session expired or unauthorized. Please refresh the page and log in to use the AI Coach.");
      } else {
        try {
          const data = await response.json();
          appendAIBubble(data.response || data.message || data.error || `Error: Unable to connect to assistant (status ${response.status}).`);
        } catch (e) {
          appendAIBubble(`Error: Unable to connect to assistant (status ${response.status}).`);
        }
      }
    }
  } catch (error) {
    removeTypingIndicator();
    appendAIBubble("Unable to contact AI service.");
  }
}
