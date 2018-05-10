let button = document.getElementById('btn');

var url ;
button.onclick = function(element) {
    let color = element.target.value;
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      url = tabs[0].url;
      chrome.tabs.executeScript(
          tabs[0].id,
          {code: 'document.body.style.backgroundColor = "' + color + '"; chrome.storage.sync.set({\'URL\':"'+url+'"},function(){ console.log("SET: "+"'+url+'");});'});
    }); 
    chrome.tabs.query({},function(tabs){
        console.log("dope"+url);
        var http = new XMLHttpRequest();
        var siteURL = "https://review-digger.herokuapp.com/";
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
