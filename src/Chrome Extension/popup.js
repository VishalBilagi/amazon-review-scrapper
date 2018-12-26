let button = document.getElementById('btn');

var url ;
button.onclick = function(element) {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      url = tabs[0].url;
      chrome.tabs.executeScript(
          tabs[0].id,
          {code: 'chrome.storage.sync.set({\'URL\':"'+url+'"},function(){ console.log("SET: "+"'+url+'");});'});
    }); 
    chrome.tabs.query({},function(tabs){
        console.log("dope"+url);
        var http = new XMLHttpRequest();
        var siteURL = "http://localhost:5000/";
        var params = "amazonURL="+url;
        http.open("POST",siteURL,true);

        http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

        http.onreadystatechange = function(){
            if(http.readyState == 4 && http.status == 200){
                alert(http.responseText);
            }
        }
        http.send(params);
    });
    
  };
