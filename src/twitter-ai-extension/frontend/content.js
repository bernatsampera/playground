// ========================================
// Twitter AI Assistant - Content Script
// ========================================

console.log("Twitter AI Assistant loaded!");

// ========================================
// State Management
// ========================================
const State = {
  uiContainer: null,
  selectionMode: false,
  selectedTweet: null,
  currentReply: null
};

// ========================================
// CSS Loader
// ========================================
async function loadCSS(shadowRoot) {
  try {
    const response = await fetch(chrome.runtime.getURL('content.css'));
    const css = await response.text();
    const style = document.createElement('style');
    style.textContent = css;
    shadowRoot.appendChild(style);
  } catch (error) {
    console.error('Failed to load CSS:', error);
    injectFallbackStyles(shadowRoot);
  }
}

function injectFallbackStyles(shadowRoot) {
  const style = document.createElement('style');
  style.textContent = `
    .ai-assistant-overlay {
      position: fixed; top: 20px; right: 20px;
      width: 320px; background: white;
      z-index: 9999; padding: 16px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    .ai-assistant-overlay h3 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: black;
    }
    .btn-primary {
      background: black;
      color: white;
      margin-right: 8px;
    }
    .btn-secondary {
      background: white;
      color: black;
      border: 1px solid #ccc;
    }
  `;
  shadowRoot.appendChild(style);
}

// ========================================
// Notification Module
// ========================================
const Notification = {
  show(message, duration = 3000) {
    const notification = document.createElement('div');
    notification.className = 'ai-assistant-notification';
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, duration);
  }
};

// ========================================
// Utility Functions
// ========================================
const Utils = {
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  extractTweetText(article) {
    const tweetTextDiv = article.querySelector("[data-testid='tweetText']");
    if (tweetTextDiv) {
      return tweetTextDiv.textContent.trim();
    }

    const tweetText = article.querySelector("[data-testid='tweet'] div[lang]");
    if (tweetText) {
      return tweetText.textContent.trim();
    }

    return "";
  },

  extractTweetUrl(article) {
    const anchor = article.querySelector("a[href*='/status/']");
    return anchor ? anchor.href : null;
  },

  findClosestTweet(el) {
    return el.closest("article");
  },

  async pasteTextIntoEditable(element, text) {
    try {
      element.focus();

      // Clear existing content safely
      while (element.firstChild) {
        element.removeChild(element.firstChild);
      }

      // Try multiple approaches to insert text in a way React recognizes

      // Approach 1: Simulate typing character by character
      // This is the most reliable for React apps
      element.textContent = text;

      // Dispatch events that React expects
      const events = [
        new FocusEvent('focus', { bubbles: true }),
        new InputEvent('input', {
          bubbles: true,
          cancelable: true,
          data: text,
          inputType: 'insertText'
        }),
        new Event('change', { bubbles: true })
      ];

      for (const event of events) {
        element.dispatchEvent(event);
      }

      // Approach 2: Try execCommand as fallback
      if (element.textContent !== text) {
        element.textContent = '';
        const success = document.execCommand('insertText', false, text);
        if (!success) {
          element.textContent = text;
        }
      }

      // Verify text was inserted
      return element.textContent === text || element.innerText === text;
    } catch (error) {
      console.log('Text insertion failed:', error.message);
      // Last resort: just set textContent
      try {
        element.textContent = text;
        return true;
      } catch {
        return false;
      }
    }
  }
};

// ========================================
// Tweet Selection Module
// ========================================
const TweetSelection = {
  enable() {
    State.selectionMode = true;
    this.highlightTweets();

    this.handleClick = this.handleClick.bind(this);
    this.handleHover = this.handleHover.bind(this);

    document.addEventListener("click", this.handleClick, true);
    document.addEventListener("mouseover", this.handleHover, true);
  },

  disable() {
    State.selectionMode = false;
    this.removeHighlights();

    if (this.handleClick) {
      document.removeEventListener("click", this.handleClick, true);
    }
    if (this.handleHover) {
      document.removeEventListener("mouseover", this.handleHover, true);
    }
  },

  handleClick(e) {
    if (!State.selectionMode) return;

    const tweet = Utils.findClosestTweet(e.target);
    if (!tweet) return;

    e.preventDefault();
    e.stopPropagation();

    const tweetText = Utils.extractTweetText(tweet);
    const tweetUrl = Utils.extractTweetUrl(tweet);

    State.selectedTweet = {
      articleElement: tweet,
      tweet_text: tweetText,
      tweet_url: tweetUrl
    };

    UI.updateTweetPreview(tweetText);
    this.disable();
  },

  handleHover(e) {
    if (!State.selectionMode) return;

    const tweet = Utils.findClosestTweet(e.target);
    if (tweet) {
      tweet.style.outline = "3px solid #1d9bf0";
    }
  },

  highlightTweets() {
    const tweets = document.querySelectorAll("article");
    tweets.forEach((tweet) => {
      tweet.style.outline = "2px solid rgba(29,155,240,0.4)";
      tweet.style.cursor = "pointer";
    });
  },

  removeHighlights() {
    const tweets = document.querySelectorAll("article");
    tweets.forEach((tweet) => {
      tweet.style.outline = "";
      tweet.style.cursor = "";
    });
  }
};

// ========================================
// Reply Module
// ========================================
const Reply = {
  async openDialogAndFill(replyText) {
    console.log('Reply.openDialogAndFill called with:', replyText?.substring(0, 50));

    if (!State.selectedTweet?.articleElement) {
      Notification.show('No tweet selected. Please select a tweet first.');
      return;
    }

    // Find the reply button within the selected tweet
    const replyBtn = State.selectedTweet.articleElement.querySelector('[data-testid="reply"]');
    console.log('Reply button found:', !!replyBtn);

    if (!replyBtn) {
      Notification.show('Could not find reply button. Try refreshing the page.');
      return;
    }

    // Copy to clipboard as backup
    await navigator.clipboard.writeText(replyText);

    // Click the reply button to open Twitter's native dialog
    replyBtn.click();

    // Wait for the dialog to appear and text area to be ready
    const result = await this.waitForDialogAndTextArea();
    if (!result) {
      Notification.show('Reply dialog not found. Text copied to clipboard.');
      return;
    }

    const { textArea } = result;
    console.log('Dialog and text area found, filling text...');

    // Focus and click the text area first to ensure it's ready
    textArea.focus();
    textArea.click();

    // Small delay to ensure React has processed the focus
    await Utils.sleep(200);

    // Try paste approach (most reliable for Twitter's React)
    const success = await this.tryPaste(textArea, replyText);
    console.log('Text fill success:', success);

    if (success) {
      Notification.show('Reply filled! Click Send to post.');
    } else {
      Notification.show('Could not fill text. Text copied to clipboard.');
    }
  },

  async waitForDialog(maxWait = 5000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const dialogs = document.querySelectorAll('[role="dialog"]');
      for (const dialog of dialogs) {
        const rect = dialog.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          console.log('Dialog found:', rect);
          return dialog;
        }
      }
      await Utils.sleep(50);
    }

    console.log('Dialog not found after timeout');
    return null;
  },

  async waitForDialogAndTextArea(maxWait = 5000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const dialogs = document.querySelectorAll('[role="dialog"]');

      for (const dialog of dialogs) {
        const rect = dialog.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          // Dialog is visible, now look for text area
          const textArea = this.findTextAreaInDialog(dialog);
          if (textArea) {
            console.log('Found dialog and text area');
            return { dialog, textArea };
          }
        }
      }
      await Utils.sleep(50);
    }

    console.log('Dialog or text area not found after timeout');
    return null;
  },

  findTextAreaInDialog(dialog) {
    const selectors = [
      '[data-testid="tweetTextarea_0"]',
      '[data-testid="tweetTextarea"]',
      'div[contenteditable="true"][aria-label]',
      'div[contenteditable="true"]'
    ];

    for (const selector of selectors) {
      const elements = dialog.querySelectorAll(selector);
      for (const element of elements) {
        // Make sure the element is visible and has reasonable size
        const rect = element.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          console.log('Found text area with selector:', selector);
          return element;
        }
      }
    }

    return null;
  },

  async tryPaste(element, text) {
    // First, copy text to clipboard
    await navigator.clipboard.writeText(text);

    // Try to trigger a paste event
    try {
      const pasteEvent = new ClipboardEvent('paste', {
        bubbles: true,
        cancelable: true,
        clipboardData: new DataTransfer()
      });
      pasteEvent.clipboardData.setData('text/plain', text);
      element.dispatchEvent(pasteEvent);
    } catch (e) {
      console.log('ClipboardEvent failed:', e);
    }

    // Also try direct text insertion as fallback
    await Utils.pasteTextIntoEditable(element, text);

    // Check if text was inserted
    await Utils.sleep(100);
    const content = element.textContent || element.innerText || '';
    return content.includes(text) || text.includes(content.trim());
  }
};

// ========================================
// UI Module
// ========================================
const UI = {
  create() {
    State.uiContainer = document.createElement("div");
    const shadow = State.uiContainer.attachShadow({ mode: "open" });

    // Load CSS
    loadCSS(shadow);

    // Create HTML structure
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `
      <div class="ai-assistant-overlay">
        <button class="close-btn">×</button>
        <h3>Twitter AI Assistant</h3>
        <button id="selectTweetBtn" class="btn-primary">Select Tweet</button>
        <button id="clearBtn" class="btn-secondary">Clear</button>
        <div id="tweetPreview"></div>
        <label>Helper text (optional):</label>
        <textarea id="helperText" placeholder="Add context for the AI reply..."></textarea>
        <button id="sendBtn" class="btn-primary" disabled>Send to AI</button>
        <div id="response" class="response-area"></div>
      </div>
    `;
    shadow.appendChild(wrapper);

    document.body.appendChild(State.uiContainer);

    this.attachEventListeners(shadow);
  },

  attachEventListeners(shadow) {
    const closeBtn = shadow.querySelector(".close-btn");
    const selectBtn = shadow.getElementById("selectTweetBtn");
    const clearBtn = shadow.getElementById("clearBtn");
    const sendBtn = shadow.getElementById("sendBtn");
    const helperText = shadow.getElementById("helperText");
    const response = shadow.getElementById("response");

    closeBtn.addEventListener("click", () => this.close());

    selectBtn.addEventListener("click", () => {
      TweetSelection.enable();
      selectBtn.textContent = "Click a tweet...";
      selectBtn.disabled = true;
    });

    clearBtn.addEventListener("click", () => this.clearSelection());

    sendBtn.addEventListener("click", async () => {
      if (!State.selectedTweet) return;

      sendBtn.textContent = "Processing...";
      sendBtn.disabled = true;
      response.innerHTML = "";

      try {
        await this.sendToAI(helperText.value, response, sendBtn);
      } catch (e) {
        response.innerHTML = `<strong>Error:</strong> ${e.message}`;
        sendBtn.textContent = "Send to AI";
        sendBtn.disabled = false;
      }
    });
  },

  async sendToAI(helperText, responseContainer, sendBtn) {
    // Get or create user ID
    let userId = localStorage.getItem('twitter_ai_user_id');
    if (!userId) {
      userId = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('twitter_ai_user_id', userId);
    }

    const res = await fetch("http://localhost:8000/api/analyze_tweet", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        tweet_url: State.selectedTweet.tweet_url,
        tweet_text: State.selectedTweet.tweet_text,
        helper_text: helperText
      })
    });

    const data = await res.json();
    State.currentReply = data.reply;

    this.displayResponse(responseContainer, data.reply);

    sendBtn.textContent = "Send to AI";
    sendBtn.disabled = false;
  },

  displayResponse(container, replyText) {
    container.innerHTML = `
      <div class="reply-content">${replyText}</div>
      <div class="action-buttons">
        <button class="action-btn copy-btn">Copy</button>
        <button class="action-btn reply-btn">Reply</button>
      </div>
    `;

    container.querySelector('.copy-btn').addEventListener('click', () => {
      navigator.clipboard.writeText(replyText);
      Notification.show('Reply copied to clipboard');
    });

    container.querySelector('.reply-btn').addEventListener('click', async () => {
      await Reply.openDialogAndFill(replyText);
    });
  },

  updateTweetPreview(tweetText) {
    const shadow = State.uiContainer?.shadowRoot;
    if (!shadow) return;

    const selectBtn = shadow.getElementById("selectTweetBtn");
    const tweetPreview = shadow.getElementById("tweetPreview");
    const sendBtn = shadow.getElementById("sendBtn");

    selectBtn.textContent = "Select Tweet";
    selectBtn.disabled = false;

    tweetPreview.innerHTML = `
      <div class="tweet-preview">
        <strong>Selected Tweet:</strong><br>
        ${this.escapeHtml(tweetText.substring(0, 200))}${tweetText.length > 200 ? "..." : ""}
      </div>
    `;

    sendBtn.disabled = false;
  },

  clearSelection() {
    State.selectedTweet = null;

    const shadow = State.uiContainer?.shadowRoot;
    if (!shadow) return;

    const selectBtn = shadow.getElementById("selectTweetBtn");
    const tweetPreview = shadow.getElementById("tweetPreview");
    const sendBtn = shadow.getElementById("sendBtn");
    const response = shadow.getElementById("response");

    tweetPreview.innerHTML = "";
    sendBtn.disabled = true;
    selectBtn.textContent = "Select Tweet";
    selectBtn.disabled = false;
    response.innerHTML = "";

    TweetSelection.disable();
  },

  close() {
    if (State.uiContainer) {
      State.uiContainer.remove();
      State.uiContainer = null;
      TweetSelection.disable();
    }
  },

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
};

// ========================================
// Message Listener
// ========================================
chrome.runtime.onMessage.addListener((msg) => {
  console.log("Received message:", msg);
  if (msg.action === "toggle_ui") {
    if (State.uiContainer) {
      UI.close();
    } else {
      UI.create();
    }
  }
});
