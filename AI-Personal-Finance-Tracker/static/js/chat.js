const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const userQuestion = document.getElementById("userQuestion");
const statementFile = document.getElementById("statementFile");

function appendChatBubble(message, type = "ai") {
  const bubble = document.createElement("div");
  bubble.classList.add("chat-bubble", type === "ai" ? "chat-ai" : "chat-user");
  bubble.innerText = message;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = userQuestion.value.trim();
  if (!question) {
    return;
  }

  appendChatBubble(question, "user");
  userQuestion.value = "";
  appendChatBubble("Thinking...", "ai");

  const formData = new FormData();
  formData.append("user_question", question);
  if (statementFile.files.length > 0) {
    formData.append("statement_file", statementFile.files[0]);
  }

  try {
    const response = await fetch("/chat", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    const lastBubble = chatWindow.querySelector(".chat-bubble.chat-ai:last-child");
    if (data.response) {
      lastBubble.innerText = data.response;
    } else {
      lastBubble.innerText = data.error || "Unexpected AI service response.";
    }
  } catch (error) {
    const lastBubble = chatWindow.querySelector(".chat-bubble.chat-ai:last-child");
    lastBubble.innerText = "Unable to contact AI service.";
  }
});
