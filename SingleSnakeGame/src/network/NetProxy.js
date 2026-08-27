/**
 * Created by billbao on 2016/4/22.
 */

var NetProxy = {};

/**
 * set music
 */
NetProxy.playMusic = function (bPlay) {
    MusicManager.setMusicEnable(bPlay);
    MusicManager.setSoundEnable(bPlay);
    console.log("playMusic setting");
};

/**
 * 登陆
 * @param nickName : 玩家名字（string）
 * @constructor
 */
NetProxy.Login = function (nickName, historyScore, imgUrl, rankList) {
    console.log("NetProxy.Login: nickName= " + nickName + ", historyScore= " + historyScore);

    //save request data
    LOGIN_REQUEST_DATA.GAME_START = true;
    LOGIN_REQUEST_DATA.USER_NAME = nickName;
    LOGIN_REQUEST_DATA.USER_LENGTH = historyScore;
    //LOGIN_REQUEST_DATA.USER_IMG_URL = dataManager.clearString(imgUrl);
    LOGIN_REQUEST_DATA.RANK_LIST = rankList;
    dataManager.nickName = nickName;
    dataManager.maxHistoryLen = historyScore;

    //storageManager.recordNickName(name);
    //MusicManager.playEffect(MusicEffectFiles.Audio_button);

    //for new guy
    if (historyScore < gameConfig.new_guy_length) {
        gameConfig = JSON.parse(Util.readTxtFileSync("res/game_config_newGuy.json"));
    } else {
        gameConfig = JSON.parse(Util.readTxtFileSync("res/game_config.json"));
    }
    gameConfigStage = gameConfig.stage_1; //for AI snake
    //console.log("NetProxy.Login: gameConfig.notice.notice_acc_time= " + gameConfig.notice.notice_acc_time);

    //send message to start game
    CEventManager.dispatchEvent(new CEvent(CEventType.ON_START_GAME_EVENT));

    //initialise bad js upload
    //H5jssdk.loadJS('//h5game.qq.com/platform/js/bj-report.js?r=2', function () {
    //    BJ_REPORT.init({
    //        id: 1115,
    //        combo: 0,
    //        url: "//badjs2.qq.com/badjs"
    //    });
    //});
    //LogPanel.endOneInfo();
    //LogPanel.addInfo('NetProxy.Login: send ON_START_GAME_EVENT');
};

/**
 * start server
 */
NetProxy.startServer = function () {
    //open it directly
    netManager.onOpened();

    //run main loop
    var server = serverLogic;
    //console.log("serverLogic= " + server);
    if (server) {
        console.log("serverLogic.runServer()");
        server.runServer();
    }

    //send login in here
    var winSize = cc.director.getWinSize();
    var msg = new PDataDef.Packet(PDataDef.WD.CMsgType.LOGIN_REQUEST);
    console.log("NetProxy: LoginRequest");
    msg.loginRequest = new PDataDef.WD.LoginRequest(dataManager.nickName, Math.round(winSize.width), Math.round(winSize.height), "2.1.1");
    netManager.sendMessage(msg);

    //LogPanel.addInfo('游戏启动startServer: winSize.width: ' + winSize.width + 'winSize.height: ' + winSize.height);

};

/**
 * pause server
 */
NetProxy.pauseServer = function () {
    var server = serverLogic;
    if (server) {
        console.log("NetProxy: pauseServer");
        server.pauseGame();
    }
};
/**
 * resume server
 */
NetProxy.resumeServer = function () {
    var server = serverLogic;
    if (server) {
        console.log("NetProxy: resumeServer");
        server.resumeGame();
    }
};

/**
 * 复活
 * @constructor
 */
NetProxy.Revive = function () {
    cc.log("NetProxy.Revive");
    var winSize = cc.director.getWinSize();
    var msg = new PDataDef.Packet(PDataDef.WD.CMsgType.REVIVE_SNAKE);
    msg.reviveSnake = new PDataDef.WD.ReviveSnake(dataManager.nickName, Math.round(winSize.width), Math.round(winSize.height), dataManager.lastId);
    cc.log("nick name : " + dataManager.nickName);
    netManager.sendMessage(msg);
};

/**
 * 改变游戏窗口
 * @constructor
 */
NetProxy.ResizeWindow = function () {
    var winSize = cc.director.getWinSize();
    var msg = new PDataDef.Packet(PDataDef.WD.CMsgType.RESIZE_SCREEN);
    msg.resizeClientScreen = new PDataDef.WD.ResizeClientScreen(Math.round(winSize.width), Math.round(winSize.height));
    netManager.sendMessage(msg);
};

/**
 * 移动蛇
 * @param pos ： 玩家点击屏幕时的世界坐标{x:0, y:0}
 * @constructor
 */
NetProxy.MoveSnake = function (pos) {
    var msg = new PDataDef.Packet(PDataDef.WD.CMsgType.MOVE_SNAKE);
    msg.moveSnake = new PDataDef.WD.MoveSnake(new PDataDef.Point(pos.x, pos.y));

    netManager.sendMessage(msg);
};

/**
 * 蛇变速
 * @param status : 变速状态（1: 开始加速，2:停止加速）
 * @constructor
 */
NetProxy.ChangeSnakeSpeed = function (status) {
    //
    var msg = new PDataDef.Packet(PDataDef.WD.CMsgType.CHANGE_SNAKE_SPEED);
    msg.changeSnakeSpeed = new PDataDef.WD.ChangeSnakeSpeed(status);

    //
    netManager.sendMessage(msg);
};

/**
 * 退出登陆
 * @constructor
 */
NetProxy.SignOut = function () {
    netManager.disconnectServer();
};