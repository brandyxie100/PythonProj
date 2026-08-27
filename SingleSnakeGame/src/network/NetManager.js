/**
 * Created by billbao on 2016/4/21.
 */

var netConfig = JSON.parse(Util.readTxtFileSync("res/config.json"));
var gameConfig = JSON.parse(Util.readTxtFileSync("res/game_config.json"));
var gameConfigStage = gameConfig.stage_1; //for AI snake
var playerConfig = gameConfig.player_pro; //only for player
var gCurrStage = 1;

function addScriptTag(src) {
    var script = document.createElement('script');
    script.setAttribute("type", "text/javascript");
    script.src = src;
    document.body.appendChild(script);
}

var NetManager = function () {
    this.connected = false;
};

NetManager.prototype.getServerConfig = function (snakeID) {
    var config;
    if (snakeID && snakeID == MY_SNAKE_ID) { //is player id
        config = playerConfig;
        //console.log("snakeID= " + snakeID + ", playerConfig= ", playerConfig);
    } else {
        config = gameConfigStage;
        //console.log("snakeID= " + snakeID + ", gameConfigStage= ", gameConfigStage);
    }
    return config;
};

NetManager.prototype.setServerConfig = function (stage) {
    if (2 == stage && stage != gCurrStage) {
        gameConfigStage = gameConfig.stage_2;
        gCurrStage = stage;
        console.log("set stage 2");
    } else if (3 == stage && stage != gCurrStage) {
        gameConfigStage = gameConfig.stage_3;
        gCurrStage = stage;
        console.log("set stage 3");
    } else if (4 == stage && stage != gCurrStage) {
        gameConfigStage = gameConfig.stage_4;
        gCurrStage = stage;
        console.log("set stage 4");
    } else {
        console.log("setServerConfig error!");
    }
};

NetManager.prototype.disconnectServer = function () {

    console.log("disconnectServer");
};

NetManager.prototype.onOpened = function () {
    console.log("Connected!");
    this.connected = true;

    if (!PDataParser.globalInfoQueue) {
        PDataParser.globalInfoQueue = new Queue();
    }

    if (!PDataParser.boardMsgQueue) {
        PDataParser.boardMsgQueue = new Queue();
    }

    PDataParser.globalInfoQueue.clear();
    PDataParser.boardMsgQueue.clear();
};

NetManager.prototype.onErr = function () {
    console.log("Error : cannot connect to server");
};

NetManager.prototype.onMessage = function (evt) {

    var data = JSON.parse(evt);
    var list = [];
    PDataParser.onHandleMessage(data, list);
};

NetManager.prototype.onClosed = function () {
    console.log("NetManager: onClosed!");

    if (PDataParser.globalInfoQueue) {
        PDataParser.globalInfoQueue.clear();
    }
    if (PDataParser.boardMsgQueue) {
        PDataParser.boardMsgQueue.clear();
    }
};

NetManager.prototype.sendMessage = function (msg) {
    var data = JSON.stringify(msg);
    //console.log("sendMessage: " + data);

    //to call server function
    var server = serverLogic;
    if (server) {
        var handle = server.getHandler();
        if (handle) {
            handle.handleMessage(data);
        }
        //console.log("sendMessage: " + data);
    }
};

var netManager = new NetManager();
