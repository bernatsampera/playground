chrome.action.onClicked.addListener((tab) => {
  // Only send message if we're on a Twitter/X page
  if (tab.url.includes("twitter.com") || tab.url.includes("x.com")) {
    // Send a message to the content script to toggle the UI
    chrome.tabs.sendMessage(tab.id, { action: "toggle_ui" });
  }
});