console.log("Twitter AI Autoreply loaded!");

// ========================================
// Utility Functions
// ========================================
const Utils = {
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  async pasteTextIntoEditable(element, text) {
    try {
      element.focus();

      // Clear existing content safely
      while (element.firstChild) {
        element.removeChild(element.firstChild);
      }

      // Try multiple approaches to insert text in a way React recognizes
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

      // Try execCommand as fallback
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
// Reply Module
// ========================================
const Reply = {
  async waitForDialogAndTextArea(maxWait = 5000) {
    const startTime = Date.now();

    while (Date.now() - startTime < maxWait) {
      const dialogs = document.querySelectorAll('[role="dialog"]');

      for (const dialog of dialogs) {
        const rect = dialog.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          const textArea = this.findTextAreaInDialog(dialog);
          if (textArea) {
            return { dialog, textArea };
          }
        }
      }
      await Utils.sleep(50);
    }

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
        const rect = element.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
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
// Add button to tweets
// ========================================
async function addReplyButton(tweet) {
  // Check if we already added a button to this tweet
  if (tweet.querySelector('.ai-reply-btn')) {
    return;
  }

  // Find the tweet text
  const tweetText = tweet.querySelector('[data-testid="tweetText"]');
  if (!tweetText) return;

  // Find the action bar (where like, reply, retweet buttons are)
  const actionBar = tweet.querySelector('[data-testid="reply"]');
  if (!actionBar) return;

  // Create the button
  const button = document.createElement('button');
  button.className = 'ai-reply-btn';
  button.innerHTML = '🤖';
  button.title = 'AI Reply';

  // Add click handler
  button.addEventListener('click', async (e) => {
    e.stopPropagation();
    e.preventDefault();

    // Get tweet text and URL
    const tweetText = tweet.querySelector('[data-testid="tweetText"]')?.textContent?.trim() || '';
    const tweetUrlLink = tweet.querySelector('a[href*="/status/"]');
    const tweetUrl = tweetUrlLink?.href || '';

    // Get or create user ID
    let userId = localStorage.getItem('twitter_ai_user_id');
    if (!userId) {
      userId = 'user_' + Math.random().toString(36).substring(2, 11);
      localStorage.setItem('twitter_ai_user_id', userId);
    }

    // Show loading state on button
    const originalHTML = button.innerHTML;
    button.innerHTML = '⏳';

    try {
      // Call the backend API FIRST, wait for response
      const res = await fetch("http://localhost:8000/api/analyze_tweet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          tweet_url: tweetUrl,
          tweet_text: tweetText,
          helper_text: ''
        })
      });

      const data = await res.json();
      const replyText = data.reply;

      // NOW open the reply dialog after we have the response
      const replyBtn = tweet.querySelector('[data-testid="reply"]');
      if (!replyBtn) return;
      replyBtn.click();

      // Wait for the dialog and text area
      const result = await Reply.waitForDialogAndTextArea();
      if (!result) return;

      const { textArea } = result;

      textArea.focus();
      textArea.click();

      await Utils.sleep(200);

      // Paste the AI response
      await Reply.tryPaste(textArea, replyText);
    } catch (error) {
      console.error('API call failed:', error);
      // Fallback to mocked reply on error
      const replyBtn = tweet.querySelector('[data-testid="reply"]');
      if (!replyBtn) return;
      replyBtn.click();

      const result = await Reply.waitForDialogAndTextArea();
      if (!result) return;

      const { textArea } = result;
      textArea.focus();
      textArea.click();
      await Utils.sleep(200);

      await Reply.tryPaste(textArea, 'This is a mocked AI reply! 🤖');
    } finally {
      button.innerHTML = originalHTML;
    }
  });

  // Insert the button before the action bar
  actionBar.parentElement.insertBefore(button, actionBar);
}

// Process all existing tweets
function processTweets() {
  const tweets = document.querySelectorAll('[data-testid="tweet"]');
  tweets.forEach(addReplyButton);
}

// Observe for new tweets
function observeTweets() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          if (node.dataset?.testid === 'tweet') {
            addReplyButton(node);
          } else {
            const tweets = node.querySelectorAll?.('[data-testid="tweet"]');
            tweets?.forEach(addReplyButton);
          }
        }
      });
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

// Initial processing and start observing
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    processTweets();
    observeTweets();
  });
} else {
  processTweets();
  observeTweets();
}
