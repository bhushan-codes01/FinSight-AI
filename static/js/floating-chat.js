// Toggle Floating Chat Panel
function toggleFloatingChat() {
  const panel = document.getElementById('floatingChatPanel');
  if (panel) {
    panel.classList.toggle('active');
    
    // Scroll to bottom on open
    if (panel.classList.contains('active')) {
      const msgs = document.getElementById('floatingChatMessages');
      if (msgs) {
        msgs.scrollTop = msgs.scrollHeight;
      }
    }
  }
}

// Send Message from Floating Chat Input
function sendFloatingChatMessage(promptText = null) {
  const inputEl = document.getElementById('floatingChatInputField');
  const messageText = promptText || (inputEl ? inputEl.value.trim() : '');
  
  if (!messageText) return;
  
  // Clear input
  if (inputEl && !promptText) {
    inputEl.value = '';
  }
  
  const messagesContainer = document.getElementById('floatingChatMessages');
  if (!messagesContainer) return;
  
  // 1. Append User Message
  const userBubble = document.createElement('div');
  userBubble.className = 'floating-chat-message-bubble user';
  userBubble.textContent = messageText;
  messagesContainer.appendChild(userBubble);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  // 2. Append Typing Animation Placeholder
  const typingBubble = document.createElement('div');
  typingBubble.className = 'floating-chat-message-bubble ai typing-indicator-wrapper';
  typingBubble.id = 'floatingChatTypingPlaceholder';
  typingBubble.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
  messagesContainer.appendChild(typingBubble);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
  
  // CSS styling for typing dots inline injection if not defined
  const style = document.createElement('style');
  style.innerHTML = `
    .typing-dot {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--text-secondary);
      margin-right: 3px;
      animation: waveDot 1.2s infinite;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.15s; }
    .typing-dot:nth-child(3) { animation-delay: 0.3s; }
    @keyframes waveDot {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-4px); }
    }
  `;
  document.head.appendChild(style);
  
  // 3. Send Request to Chatbot API
  fetch('/chatbot/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: messageText })
  })
  .then(res => res.json())
  .then(data => {
    // Remove typing placeholder
    const placeholder = document.getElementById('floatingChatTypingPlaceholder');
    if (placeholder) placeholder.remove();
    
    // Append AI Response
    const aiBubble = document.createElement('div');
    aiBubble.className = 'floating-chat-message-bubble ai';
    
    // Simple markdown formatting helper
    let formattedText = data.response || "No response received.";
    // Simple bold markdown
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Simple bullet markdown
    formattedText = formattedText.replace(/^\* (.*?)$/gm, '• $1');
    
    aiBubble.innerHTML = formattedText.replace(/\n/g, '<br>');
    messagesContainer.appendChild(aiBubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  })
  .catch(err => {
    console.error('Chat error:', err);
    const placeholder = document.getElementById('floatingChatTypingPlaceholder');
    if (placeholder) placeholder.remove();
    
    const errorBubble = document.createElement('div');
    errorBubble.className = 'floating-chat-message-bubble ai text-danger';
    errorBubble.textContent = 'Sorry, I encountered an error connecting to the AI Assistant. Please try again.';
    messagesContainer.appendChild(errorBubble);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  });
}

// Key Listener for Enter Key in Input
document.addEventListener('DOMContentLoaded', () => {
  // Manual dropdown toggle fallback for language selector (bulletproof to browser translations)
  const globeBtns = Array.from(document.querySelectorAll('.dropdown button')).filter(btn => btn.querySelector('.fa-globe'));
  globeBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const parent = btn.closest('.dropdown');
      if (parent) {
        const menu = parent.querySelector('.dropdown-menu');
        if (menu) {
          const isShown = menu.classList.contains('show');
          // Hide all other dropdowns
          document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
          document.querySelectorAll('.dropdown button.show').forEach(b => b.classList.remove('show'));
          
          if (!isShown) {
            menu.classList.add('show');
            btn.classList.add('show');
          } else {
            menu.classList.remove('show');
            btn.classList.remove('show');
          }
        }
      }
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
    document.querySelectorAll('.dropdown button.show').forEach(btn => btn.classList.remove('show'));
  });

  const inputEl = document.getElementById('floatingChatInputField');
  if (inputEl) {
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        sendFloatingChatMessage();
      }
    });
  }

  // Initialize count-up counters
  document.querySelectorAll('.count-up').forEach(el => {
    const val = parseFloat(el.getAttribute('data-value') || '0');
    if (!isNaN(val) && val !== 0) {
      animateValue(el, 0, val, 1000);
    } else {
      el.textContent = '0';
    }
  });
});

// Animate Value Count Up
function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    const currentValue = progress * (end - start) + start;
    
    // Check if we need decimal formatting
    const isFloat = end % 1 !== 0;
    obj.textContent = formatNumber(currentValue, isFloat);
    
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      obj.textContent = formatNumber(end, isFloat);
    }
  };
  window.requestAnimationFrame(step);
}

function formatNumber(num, hasDecimals) {
  if (hasDecimals) {
    return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return Math.floor(num).toLocaleString();
}

// Sidebar Mobile Toggle Hamburger Helper
function toggleSidebarMobile() {
  const sidebar = document.getElementById('sidebarWrapper');
  if (sidebar) {
    sidebar.classList.toggle('active');
  }
}

// Global Theme Toggle Handler
function toggleTheme() {
  const isLight = document.body.classList.toggle('theme-light');
  localStorage.setItem('theme-pref', isLight ? 'light' : 'dark');
  
  // Update toggle icons globally
  document.querySelectorAll('.theme-toggle-icon').forEach(icon => {
    if (isLight) {
      icon.className = 'fas fa-moon theme-toggle-icon';
    } else {
      icon.className = 'fas fa-sun theme-toggle-icon';
    }
  });

  // Dynamically update active charts if available
  if (typeof window.updateChartsTheme === 'function') {
    window.updateChartsTheme();
  }

  fetch('/settings/toggle-theme', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ theme: isLight ? 'light' : 'dark' })
  }).catch(e => console.error('Theme sync error:', e));
}
