let uiContainer = null;
let selectionMode = false;
let selectedTweet = null;
let currentReply = null;  // Store current AI reply for feedback

console.log("🔥 content.js loaded!");

// Listen for messages from background script
chrome.runtime.onMessage.addListener((msg) => {
  console.log("Received message:", msg);
  if (msg.action === "toggle_ui") {
    if (uiContainer) {
      // If open, close it
      uiContainer.remove();
      uiContainer = null;
      disableTweetSelection();
    } else {
      createOverlay();
    }
  }
});

function createOverlay() {
  uiContainer = document.createElement("div");
  // Attach a Shadow DOM to prevent Twitter styles from breaking your UI
  const shadow = uiContainer.attachShadow({mode: "open"});

  // Create the HTML structure
  const wrapper = document.createElement("div");
  wrapper.innerHTML = `
    <style>
      .ai-assistant-overlay {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 320px;
        background: white;
        z-index: 9999;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      .ai-assistant-overlay h3 {
        margin: 0 0 15px 0;
        font-size: 16px;
        font-weight: 600;
      }
      .ai-assistant-overlay textarea {
        width: 100%;
        min-height: 80px;
        padding: 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 14px;
        resize: vertical;
      }
      .ai-assistant-overlay button {
        padding: 8px 16px;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
      }
      .btn-primary {
        background: #1d9bf0;
        color: white;
        margin-right: 8px;
      }
      .btn-primary:hover {
        background: #1a8cd8;
      }
      .btn-primary:disabled {
        background: #94a3b8;
        cursor: not-allowed;
      }
      .btn-secondary {
        background: #f3f4f6;
        color: #374151;
      }
      .btn-secondary:hover {
        background: #e5e7eb;
      }
      .tweet-preview {
        background: #f8f9fa;
        color: black;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 13px;
        border-left: 3px solid #1d9bf0;
      }
      .tweet-preview strong {
        color: #1d9bf0;
      }
      .response-area {
        background: #f8f9fa;
        color: black;
        padding: 10px;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 13px;
        white-space: pre-wrap;
        max-height: 200px;
        overflow-y: auto;
      }
      .close-btn {
        position: absolute;
        top: 10px;
        right: 10px;
        background: none;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: #666;
      }
      .close-btn:hover {
        color: #000;
      }
      .feedback-section {
        margin-top: 10px;
        padding: 10px;
        background: #f0f0f0;
        border-radius: 4px;
      }
      .feedback-buttons {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
      }
      .feedback-btn {
        padding: 6px 12px;
        border: 1px solid #ddd;
        background: white;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
      }
      .feedback-btn:hover {
        background: #f8f9fa;
      }
      .feedback-btn.good {
        color: #22c55e;
      }
      .feedback-btn.bad {
        color: #ef4444;
      }
      .quality-score {
        font-size: 12px;
        color: #666;
        margin-top: 5px;
      }
      .quality-score.high {
        color: #22c55e;
      }
      .quality-score.medium {
        color: #f59e0b;
      }
      .quality-score.low {
        color: #ef4444;
      }
    </style>
    <div class="ai-assistant-overlay">
      <button class="close-btn">×</button>
      <h3>Twitter AI Assistant</h3>

      <button id="selectTweetBtn" class="btn-primary">Select Tweet</button>
      <button id="clearBtn" class="btn-secondary">Clear</button>

      <div id="tweetPreview"></div>

      <label style="display: block; margin: 15px 0 5px 0; font-size: 14px;">Helper text (optional):</label>
      <textarea id="helperText" placeholder="Add context for the AI reply..."></textarea>

      <button id="sendBtn" class="btn-primary" disabled>Send to AI</button>

      <div id="response" class="response-area"></div>
    </div>
  `;

  shadow.appendChild(wrapper);
  document.body.appendChild(uiContainer);

  // Get references to the elements
  const overlay = shadow.querySelector(".ai-assistant-overlay");
  const selectBtn = shadow.getElementById("selectTweetBtn");
  const clearBtn = shadow.getElementById("clearBtn");
  const sendBtn = shadow.getElementById("sendBtn");
  const helperText = shadow.getElementById("helperText");
  const tweetPreview = shadow.getElementById("tweetPreview");
  const response = shadow.getElementById("response");
  const closeBtn = shadow.querySelector(".close-btn");

  // Add event listeners
  closeBtn.addEventListener("click", () => {
    uiContainer.remove();
    uiContainer = null;
    disableTweetSelection();
  });
  selectBtn.addEventListener("click", () => {
    enableTweetSelection();
    selectBtn.textContent = "Click a tweet...";
    selectBtn.disabled = true;
  });

  clearBtn.addEventListener("click", () => {
    selectedTweet = null;
    tweetPreview.innerHTML = "";
    sendBtn.disabled = true;
    disableTweetSelection();
    selectBtn.textContent = "Select Tweet";
    selectBtn.disabled = false;
    response.innerHTML = "";
  });

  sendBtn.addEventListener("click", async () => {
    if (!selectedTweet) return;

    sendBtn.textContent = "Processing...";
    sendBtn.disabled = true;
    response.innerHTML = "";

    try {
      // Get or create user ID (stored in local storage)
      let userId = localStorage.getItem('twitter_ai_user_id');
      if (!userId) {
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('twitter_ai_user_id', userId);
      }

      const res = await fetch("http://localhost:8000/api/analyze_tweet", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          user_id: userId,
          tweet_url: selectedTweet.tweet_url,
          tweet_text: selectedTweet.tweet_text,
          helper_text: helperText.value
        })
      });

      const data = await res.json();
      currentReply = data.reply;

      // Display reply with quality score
      const scoreClass = data.quality_score >= 80 ? 'high' : data.quality_score >= 60 ? 'medium' : 'low';
      response.innerHTML = `
        <strong>AI Reply:</strong><br>${data.reply}
        <div class="quality-score ${scoreClass}">
          Quality Score: ${data.quality_score.toFixed(1)}/100 - ${data.quality_feedback}
        </div>
        <div class="feedback-section">
          <div style="font-size: 12px; margin-bottom: 5px;">Was this helpful?</div>
          <div class="feedback-buttons">
            <button class="feedback-btn good" data-feedback="good">👍 Good</button>
            <button class="feedback-btn bad" data-feedback="bad">👎 Bad</button>
            <button class="feedback-btn" data-feedback="too_formal">Too formal</button>
            <button class="feedback-btn" data-feedback="too_casual">Too casual</button>
          </div>
        </div>
      `;

      // Add feedback button listeners
      const feedbackButtons = response.querySelectorAll('.feedback-btn');
      feedbackButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
          const feedbackType = btn.getAttribute('data-feedback');
          await submitFeedback(userId, feedbackType);

          // Visual feedback
          btn.style.background = '#e5e7eb';
          setTimeout(() => {
            btn.style.background = 'white';
          }, 1000);
        });
      });

    } catch (e) {
      response.innerHTML = `<strong>Error:</strong> ${e.message}`;
    }

    sendBtn.textContent = "Send to AI";
    sendBtn.disabled = false;
  });

  // Listen for close event
  document.addEventListener(
    "closeUI",
    () => {
      uiContainer = null;
      disableTweetSelection();
    },
    {once: true}
  );
}

function enableTweetSelection() {
  selectionMode = true;
  highlightTweets();

  document.addEventListener("click", handleTweetClick, true);
  document.addEventListener("mouseover", handleTweetHover, true);
}

function disableTweetSelection() {
  selectionMode = false;
  removeHighlights();

  document.removeEventListener("click", handleTweetClick, true);
  document.removeEventListener("mouseover", handleTweetHover, true);
}

function handleTweetClick(e) {
  if (!selectionMode) return;

  const tweet = findClosestTweet(e.target);
  if (!tweet) return;

  e.preventDefault();
  e.stopPropagation();

  const tweetText = extractTweetText(tweet);
  const tweetUrl = extractTweetUrl(tweet);

  selectedTweet = {
    tweet_text: tweetText,
    tweet_url: tweetUrl
  };

  // Update the UI
  const shadow = uiContainer.shadowRoot;
  const selectBtn = shadow.getElementById("selectTweetBtn");
  const tweetPreview = shadow.getElementById("tweetPreview");
  const sendBtn = shadow.getElementById("sendBtn");

  selectBtn.textContent = "Select Tweet";
  selectBtn.disabled = false;

  tweetPreview.innerHTML = `
    <div class="tweet-preview">
      <strong>Selected Tweet:</strong><br>
      ${tweetText.substring(0, 200)}${tweetText.length > 200 ? "..." : ""}
    </div>
  `;

  sendBtn.disabled = false;

  disableTweetSelection();
}

function handleTweetHover(e) {
  if (!selectionMode) return;

  const tweet = findClosestTweet(e.target);
  if (tweet) {
    tweet.style.outline = "3px solid #1d9bf0";
  }
}

function findClosestTweet(el) {
  return el.closest("article");
}

function extractTweetText(article) {
  const spans = article.querySelectorAll("span");
  return Array.from(spans)
    .map((s) => s.innerText)
    .join(" ")
    .trim();
}

function extractTweetUrl(article) {
  const anchor = article.querySelector("a[href*='/status/']");
  return anchor ? anchor.href : null;
}

function highlightTweets() {
  const tweets = document.querySelectorAll("article");
  tweets.forEach((tweet) => {
    tweet.style.outline = "2px solid rgba(29,155,240,0.4)";
    tweet.style.cursor = "pointer";
  });
}

function removeHighlights() {
  const tweets = document.querySelectorAll("article");
  tweets.forEach((tweet) => {
    tweet.style.outline = "";
    tweet.style.cursor = "";
  });
}

async function submitFeedback(userId, feedbackType) {
  try {
    await fetch("http://localhost:8000/api/feedback", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        user_id: userId,
        tweet_text: selectedTweet.tweet_text,
        ai_reply: currentReply,
        feedback: feedbackType
      })
    });
    console.log("Feedback submitted:", feedbackType);
  } catch (e) {
    console.error("Failed to submit feedback:", e);
  }
}
