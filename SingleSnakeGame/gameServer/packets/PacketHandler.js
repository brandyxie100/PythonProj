var consts = require("../utils/constants");
var settings = require("../utils/settings");
var CmdConfig = require('./CmdConfig');
var controllers = {
    'LoginController': require('../controllers/LoginController'),
    'SnakeController': require('../controllers/SnakeController')
};
var Services = require('../services/Services');
var EventEmitter = require('../utils/eventEmitter');
var PacketMsg = require("./PacketMsg");

//var builder = ProtoBuf.loadProtoFile(path.join(__dirname, "snake.proto"));
//var MessageBuilder = builder.build("Snake");
//var updateMoveCostTime = new CostTimeInfo('UpdateMove');
//var updateSnakeMoveCostTime = new CostTimeInfo('Step1:UpdateSnakeMove');
//var updateRobotMoveCostTime = new CostTimeInfo('Step2:UpdateRobotMove');
//var collisionAllCostTime = new CostTimeInfo('Step3:CollisionAll');
//var updateEatCostTime = new CostTimeInfo('Step4:UpdateEat');
//var updateDeadCostTime = new CostTimeInfo('Step5:UpdateDead');
//var updateRankCostTime = new CostTimeInfo('Step6:UpdateRank');
//var updateFoodCostTime = new CostTimeInfo('Step7:UpdateFood');
//var updateGlobalInfoCostTime = new CostTimeInfo('Step8:UpdateGlobalInfo');
//var encodeAndSendCostTime = new CostTimeInfo('step9:EncodeAndSend');
//var encodeCostTime = new CostTimeInfo('----->Encode');
//var WSsendMsgCostTime = new CostTimeInfo('----->WebsocketSend');
//var totalFrameCostTime = new CostTimeInfo('TotalFrame', null, [10, 20, 30, 40, 50]);
//var PING_DELAY_TIME = settings.readSetting("ping-delay", 30000);

var isPlaying = true;

var clients = [],     //all clients of player, only one now
    tickInterval = 0,
    firstTime = 0,
    tickMain = 0,     // move , collision update
    tickFood = 0,     // food spawn update
    tickRank = 0,     // leader board update

    g_frameTime = settings.readSetting("frame", 30);

// 主逻辑循环
var mainLoop = function (dt) {
    if (false == isPlaying) {
        return;
    }
    //var curTime = Date.now();
    // step1: 更新蛇的位置
    update('updateSnake', dt);

    // step2: 更新机器人位置
    Services.RobotService.updateRobots(clients[0].PacketHandler.visibleSnakes);

    // step3: 碰撞检测
    // 碰撞检测主逻辑
    Services.CollisionService.checkCollision(clients[0].PacketHandler);
    var collision = Services.CollisionService.collision;

    //curTime = Date.now();
    //console.log("main loop: check collision cost time: " + (Date.now() - curTime));

    // step4: 更新食物相关数据
    // 更新food model数据,通知snake成长,生成eatenFoodInfo
    Services.FoodService.updateEatenFoodInfo(collision);
    Services.FoodService.updateMovableFoodInfo(g_frameTime * 0.001, collision);
    update('eatFood');

    // step5: 更新蛇死亡相关数据
    Services.SnakeService.updateKillSnakeInfo(collision);
    update('snakeDeath');

    //curTime = Date.now();
    //console.log("main loop: snake and eat food cost time: " + (Date.now() - curTime));

    // step6: 更新排行榜和雷达 (每秒)
    tickRank++;
    if (tickRank * g_frameTime >= 1600) {
        Services.RadarService.updateRadarInfo();
        update('updateRank');

        tickRank = 0;   // Reset
    }

    // step7: 更新食物 (每秒)
    tickFood++;
    if (tickFood * g_frameTime >= 1500) {
        Services.FoodService.updateFood();
        Services.FoodService.spawnFood();

        tickFood = 0;   // Reset
    }
    //curTime = Date.now();
    //console.log("main loop: update food cost time: " + (Date.now() - curTime));

    // step8: 更新全局信息
    update('updateGlobalInfo');

    var send_datas = [];
    for (var client of clients) {
        send_datas.push({ph: client.PacketHandler, data: client.PacketHandler.sendQueue});
        client.PacketHandler.sendQueue = [];
    }

    ////////////分隔符//////////////////
    // step9: 编码和发送
    for (var data of send_datas) {
        data.ph.sendToClientRaw(data.data);
    }

    //console.log("main loop: cost time: " + (Date.now() - curTime));
};

var sendToAll = function (funName, param) {
    for (var i = 0, len = clients.length; i < len; i++) {
        var handler = clients[i] && clients[i].PacketHandler;
        handler && handler[funName] && handler[funName].call(handler, param);
    }
};

var update = function (name, param) {
    var methodConfig = {
        'updateSnake': 'updateSnake',
        'updateRank': 'updateRank',
        'eatFood': 'eatFood',
        'snakeDeath': 'snakeDeath',
        'updateGlobalInfo': 'updateGlobalInfo'
    };

    sendToAll(methodConfig[name], param);
};

EventEmitter.on('TimeOver', () => {
    //Services.RankService.updateFinalRank();
    sendToAll('timeOver');
});

EventEmitter.on('DestorySnake', (snakeIDs) => {
    sendToAll('destorySnake', snakeIDs);
});

EventEmitter.on('CallBoardInfo', (boardInfo) => {
    broadToAll(consts.MessageType.UPDATE_CALL_BOARD, boardInfo);
});

var broadToAll = function (cmd, data) {
    var message = PacketMsg.packetMsg(cmd, data);
    //console.log("broadToAll: message: ", message);
    //clients.forEach((client) => {
    //if (client.readyState == 1) {
    //send message to client
    netManager.onMessage(message);

    //}
    //});
};

/**
 * Manipulate connections and message delivery
 * @param wsServer
 * @param socket
 * @constructor
 */
class PacketHandler {
    constructor() {
        var socket = {clientId: 1, PacketHandler: null};
        socket.clientId = 1; //only one
        socket.PacketHandler = this;

        //add to clients
        clients.push(socket);

        this.snakeId = 0;
        this.controllers = {};
        this.useBinary = false; // 默认使用json

        this.visibleSnakes = new Set();   // 当前可见的蛇ID
        this.oldAddSnakes = [];    // 已加入的蛇ID
        this.newAddSnakes = [];    // 当前新增的蛇ID

        this.visibleFoods = [];    // 当前可见的食物ID
        this.newAddFoods = [];     // 当前新增加的食物ID
        this.sendQueue = [];       // 发送队列

        for (var key in controllers) {
            this.controllers[key] = new controllers[key](this);
        }

        this.triggerRoomLogic();

        if (Services.RoomService.getStatus() == "running") {
            isPlaying = true;
        }

        //start main loop
        cc.director.getScheduler().scheduleUpdate(this);
    }

    pauseServer() {
        cc.director.getScheduler().unscheduleUpdate(this);
        console.log("PacketHandler: pauseServer");
    }

    resumeServer() {
        cc.director.getScheduler().scheduleUpdate(this);
        console.log("PacketHandler: resumeServer");
    }

    update(dt) {
        //console.log("update: dt = " + dt);
        mainLoop(dt);
    }

    handleMessage(data) {
        var message = PacketMsg.decodeMsg(data);
        this.useBinary = false;
        if (message.messageType.length <= 0) {
            console.error("message miss messageType");
            return;
        }
        var messageType = message.messageType[0];
        var config = CmdConfig[messageType];

        if (config) {
            var packetBody = config.packetBody;
            var route = config.route;

            if (route) {
                var routeSplit = route.split('.'),
                    controller = routeSplit[0],
                    action = routeSplit[1],
                    controllerIns = this.controllers[controller],
                    method = controllerIns && controllerIns[action];
                method && method.call(controllerIns, message[packetBody]);
            }
        }
    }

    handleClose() {
        //stop main loop
        cc.director.getScheduler().unscheduleUpdate(this);

        if (this.snakeId > 0) {
            Services.SnakeService.delete(this.snakeId);
            console.info('delete player snake: ' + this.snakeId);
        }
        if (this.snake) {
            this.snake = null;
            console.info("this.snake = null;");
        }

        for (var i = 0, len = clients.length; i < len; i++) {
            var socket = clients.splice(i, 1);
            if (socket) {
                socket = null;
            }
        }
        //socket.PacketHandler = null;
        //EventEmitter.emit('clientClose', socket);
    }

    triggerRoomLogic() {
        var roomId = 1;

        Services.RoomService.trigger(roomId, clients.length);
    }

    init() {
        this.visibleSnakes = new Set();
        this.oldAddSnakes = [];
        this.newAddSnakes = [];

        this.visibleFoods = [];
        this.newAddFoods = [];
    }

    setSnake(data) {
        this.snakeId = data.snakeId;
        this.snake = data;
        this.init();
    }

    getSnake() {
        return this.snake;
    }

    isActive() {
        if (this.snake && !this.snake.dead) {
            return true;
        }
        return false;
    }

    getClientsNum() {
        return clients.length;
    }

    sendToClient(cmd, data) {
        this.sendQueue.push({cmd: cmd, data: data});
    }

    sendToClientRaw(datas) {
        if (datas.length <= 0) {
            return;
        }
        // 编码
        var message = PacketMsg.packetMsgBatch(datas, this.useBinary);

        // 真正发包
        netManager.onMessage(message);
    }

    sendErrorMsg(cmd, errCode) {
        var config = CmdConfig[cmd];
        var msgHead = {
            errorCode: errCode,
            serverTime: (new Date()).getTime()
        };
        var packetBody = config.packetBody;
        var result = {};
        result['messageType'] = [cmd];
        result['messageHead'] = msgHead;
        result[packetBody] = {};

        //use json
        var message = JSON.stringify(result);

        //send message to client
        netManager.onMessage(message);
    }

    updateSnake(dt) {
        Services.SnakeService.updateSnake(this, dt);
    }

    updateRank() {
        //var rankData = Services.RankService.getRankData();
        //this.sendToClient(consts.MessageType.UPDATE_RANK_LIST, rankData);
        //var selfRankData = Services.RankService.getSelfRankData(this.snakeId);
        //this.sendToClient(consts.MessageType.UPDATE_SELF_RANK, selfRankData);

        var radarData = Services.RadarService.getRadarInfo();
        this.sendToClient(consts.MessageType.UPDATE_RADAR_INFO, radarData);
    }

    updateGlobalInfo() {
        Services.GlobalInfoService.updateVisible(this);

        var globalInfo = Services.GlobalInfoService.getData(this);
        if (globalInfo) {
            this.sendToClient(consts.MessageType.UPDATE_GLOBAL_INFO, {globalInfo: globalInfo});
        }
    }

    eatFood() {
        var eatFoodInfo = Services.FoodService.getEatFoodInfo(this);
        if (eatFoodInfo && eatFoodInfo.length > 0) {
            this.sendToClient(consts.MessageType.UPDATE_EAT_FOOD, {eatFoodInfo: eatFoodInfo});
        }
    }

    snakeDeath() {
        var snakeKillInfo = Services.SnakeService.getKillSnakeInfo(this);
        if (snakeKillInfo && snakeKillInfo.length > 0) {
            this.sendToClient(consts.MessageType.UPDATE_SNAKE_DEATH, {snakeKillInfo: snakeKillInfo});
        }
    }

    destorySnake(snakeIDs) {
        this.sendToClient(consts.MessageType.UPDATE_SNAKE_SUICIDE, {snakeId: snakeIDs});
    }

    callBoardInfo(boardInfo) {
        this.sendToClient(consts.MessageType.UPDATE_CALL_BOARD, boardInfo);
    }

    timeOver() {
        //var finalRank = Services.RankService.getFinalRank(this.snakeId);
        var finalRank = 0;
        this.sendToClient(consts.MessageType.TIME_OVER, finalRank);

        console.log("PacketHandle: timeOver()");
    }

    onClientClose() {
        console.log("PacketHandle: onClientClose()");
        Services.RoomService.onClientClose();
    }
}

EventEmitter.on('TimeStart', () => {
    isPlaying = true;
    tickInterval = Date.now();
    console.info('%s: Time start....', new Date());
});

EventEmitter.on('TimeOver', () => {
    //close main loop
    isPlaying = false;
    console.info('PacketHandler: on TimeOver');

    //send all left messages to client
    var send_datas = [];
    for (var client of clients) {
        send_datas.push({ph: client.PacketHandler, data: client.PacketHandler.sendQueue});
        client.PacketHandler.sendQueue = [];
    }
    for (var data of send_datas) {
        data.ph.sendToClientRaw(data.data);
    }

    //close client
    for (var client of clients) {
        client.PacketHandler.handleClose();
    }

    //close message manager
    netManager.onClosed();
});

module.exports = PacketHandler;