chrome.runtime.onInstalled.addListener(function(){
    chrome.storage.sync.set({color: '#ffffff'}, function(){
    })
})

chrome.declarativeContent.onPageChanged.removeRules(undefined, function() {
    chrome.declarativeContent.onPageChanged.addRules([{
      conditions: [new chrome.declarativeContent.PageStateMatcher({
        pageUrl: {hostEquals: 'www.amazon.in'},
      })
      ],
          actions: [new chrome.declarativeContent.ShowPageAction()]
    }]);
  });