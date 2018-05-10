var express = require('express');
var app = express();
var bodyparser = require('body-parser');

app.use(bodyparser.urlencoded({
    extended: true
}));

app.use(bodyparser.json());

app.listen(3000, function(){
    console.log("Running on 3000");
});

var URL = "";
app.post('/',function(req,res){

    console.log(req.body.amazonURL);
    URL = req.body.amazonURL;
    fetchReviews(URL);
    res.send("Gotcha!");
});


function fetchReviews(URL){
    var spawn = require("child_process").spawn;

    var process = spawn('python', ['./src/scrap.py',URL]);

    process.stdout.on('data', function(data){
        console.log(data.toString());
    })

    process.stderr.on('data', function(data){
        console.error(data.toString());
    })
}