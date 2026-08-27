/**
 * Created by billbao on 2016/4/21.
 */

var PDataDef = {};

PDataDef.WD = {};
PDataDef.RD = {};

PDataDef.Packet = function (msgType) {

    this.messageType = [];        //命令字
    this.messageType.push(msgType);

    this.messageHead = null;     //(PDataDef.RD.ResponseBase对象)服务器返回的包才会携带
    this.pingRequest = null;     //optional
    this.pingResponse = null;    //optional
    this.loginRequest = null;    //optional
    this.loginResponse = null;   //optional
    this.moveSnake = null;        //optional
    this.changeSnakeSpeed = null;  //optional
    this.updateRankList = null;    //optional
    this.updateGlobalInfo = null;  //optional
    this.updateEatFood = null;     //optional
    this.updateSnakeDeath = null;  //optional
    this.updateSnakeSuicide = null; //optional
    this.reviveSnake = null;        //optional
    this.reviveResponse = null;     //optional
    this.timeOver = null;           //optional
    this.updateRadarInfo = null;    //optional
    this.resizeClientScreen = null; //optional
    this.errorResponse = null;      //optional
    this.updateSelfRank = null;     //optional
    this.updateCallBoardInfo = null; //optional
};

PDataDef.Point = function (x, y) {
    this.xPos = x;
    this.yPos = y;
};

// 蛇的节点信息
PDataDef.PointInfo = function (x, y, add) {
    this.xPos = x;
    this.yPos = y;
    this.addNode = add;         // 节点属性用于增量数据(0:未增加 1:增加 -1:减少)
};

PDataDef.SnakeInfo = function (snakeId, skinId, name, width, energy, dirPos, status, increment) {
    this.snakeId = snakeId;    // 蛇ID
    this.skinId = skinId;     // 皮肤ID
    this.name = name;      // 昵称
    this.width = width;      // 蛇的宽度
    this.energy = energy;     // 蛇的能量值
    this.dirPos = dirPos;     // 蛇的方向点
    this.bodyPoints = []; // 身体节点数组（包含头部, 每个点相对于前一个点的偏移值）
    this.increment = increment;    // 当前蛇身体数据是否为增量: 0 - 全量，1 - 增量
    this.statusFlag = status;   // 蛇是否处于加速状态：0 - 不加速，1 - 加速 / 蛇是否处于新手保护状态: 0 - 不保护，1 - 保护
};

PDataDef.FoodType = {
    ordinary: 1,
    growUp: 2,
    movable: 3,
    accelerateResidual: 4,
    deathResidual: 5
};

PDataDef.FoodInfo = function (foodType, foodId, radius, color, position) {
    this.foodType = foodType;   // 食物类型：1-普通食物，2-基础成长型, 3-移动AI食物, 4-加速后残留, 5-死亡后残留
    this.foodId = foodId;     // 食物ID
    this.radius = radius;     // 食物半径
    this.color = color;      // 食物颜色
    this.position = position;   // 食物坐标this.
};

PDataDef.UserRankInfo = function (snakeId, name, energy, skinId, killSnake, maxEnergy, position) {
    this.snakeId = snakeId;
    this.name = name;   // 昵称
    this.energy = energy;  // 能量值
    this.skinId = skinId;  // 皮肤ID
    this.killSnake = killSnake;  // 杀蛇数量
    this.maxEnergy = maxEnergy;  // 最大能量值
    this.position = position;   // 蛇坐标
};

PDataDef.ResponseBase = function (errorCode, errorMsg, serverTime) {
    this.errorCode = errorCode;
    this.errorMsg = errorMsg;
    this.serverTime = serverTime;   // 服务器当前时间
};

PDataDef.GlobalInfo = function (mapRadius, viewSize, snakeSelf) {
    this.mapRadius = mapRadius;       // 地图半径
    this.viewSize = viewSize;        // 视野范围
    this.snakeSelf = snakeSelf;   // 玩家自己的蛇信息
    this.snakeOthers = []; // 其他玩家的蛇信息
    this.foodInfo = [];     // 食物信息
};

// 食物被吃数据信息
PDataDef.EatFoodInfo = function (id) {
    this.snakeId = id;    // 蛇ID
    this.eatFoods = [];   // 吃掉的食物ID数组（int数组）
};

// 蛇死亡信息
PDataDef.SnakeDeathInfo = function (id) {
    this.snakeId = id;    // 被杀蛇ID
//    this.generateFoods = [];   // （PDataDef.FoodInfo对象）生成的食物信息数组
};

// 蛇被杀数据信息
PDataDef.SnakeKillInfo = function (id, name) {
    this.killerId = id;    // 蛇ID
    this.killerName = name; // 杀死蛇昵称
    this.snakeDeathInfo = []; //（PDataDef.SnakeDeathInfo对象）被杀蛇信息数组
};

// 雷达蛇信息
PDataDef.RadarSnakeInfo = function (pos) {
    this.position = pos;   // 蛇坐标
};

// 雷达信息
PDataDef.RadarInfo = function () {
    this.radarSnakeInfo = [];   //（PDataDef.RadarSnakeInfo对象数组）雷达蛇信息
};

PDataDef.WD.CMsgType = {
    PING_REQUEST: 1,    //心跳请求
    LOGIN_REQUEST: 2,      //登陆请求
    MOVE_SNAKE: 3,     //蛇移动请求
    CHANGE_SNAKE_SPEED: 4,      //蛇变速请求
    REVIVE_SNAKE: 5,       //蛇复活
    RESIZE_SCREEN: 6,      //改变视野
};

PDataDef.WD.PingRequest = function () {

};

PDataDef.WD.LoginRequest = function (nickName, width, height, version) {
    this.name = nickName;
    this.screenWidth = width;   // 屏幕宽度
    this.screenHeight = height;  // 屏幕高度
    this.version = version;      // 客户端版本号
};

PDataDef.WD.MoveSnake = function (pos) {
    this.touchPos = pos; // 玩家点击屏幕时的世界坐标(PDataDef.Point对象)
};

PDataDef.WD.ChangeSnakeSpeed = function (status) {
    this.changeStatus = status;   // 1: 开始加速，2:停止加速
};

// 蛇复活
PDataDef.WD.ReviveSnake = function (nickName, width, height, lastId) {
    this.name = nickName;
    this.snakeId = lastId; 	  // 原蛇ID
    this.screenWidth = width;   // 屏幕宽度
    this.screenHeight = height;  // 屏幕高度
};

// 改变屏幕宽高
PDataDef.WD.ResizeClientScreen = function (width, height) {
    this.screenWidth = width;   // 屏幕宽度(int)
    this.screenHeight = height;  // 屏幕高度(int)
};


PDataDef.RD.SMsgType = {
    PING_RESPONSE: 101,        //心跳回应
    LOGIN_RESPONSE: 102,       //登录回应（玩家初始化）
    REVIVE_RESPONSE: 103,      //复活回应
    ERROR_RESPONSE: 104,       //错误回应

    UPDATE_RANK_LIST: 201,     //更新排行
    UPDATE_GLOBAL_INFO: 202,       //更新全量信息
    UPDATE_EAT_FOOD: 203,       //食物被吃
    UPDATE_SNAKE_DEAD: 204,        //蛇死亡
    UPDATE_SNAKE_SUICIDE: 205,      //蛇撞墙
    TIME_OVER: 206,            //游戏结束
    UPDATE_RADAR_INFO: 207,    //更新雷达信息
    UPDATE_INCREMENT_INFO: 208,     //暂时未用
    UPDATE_SELF_RANK: 209,      //更新自己的排行
    UPDATE_CALL_BOARD: 210,     //公告消息
};

PDataDef.RD.PingResponse = function () {
//    this.responseBase = responseBase;       //PDataDef.RD.ResponseBase对象
};

PDataDef.RD.LoginResponse = function (endTime, name, globalInfo) {
//    this.responseBase = responseBase;   //PDataDef.RD.ResponseBase对象
    this.endTime = endTime;     //游戏结束时间戳
    this.name = name; // 用户的名称，如果名称为空的话服务端会生成随机名称
    this.globalInfo = globalInfo; // 全量的数据信息（PDataDef.GlobalInfo对象）
};
// 复活回应
PDataDef.RD.ReviveResponse = function (name, globalInfo) {
    this.name = name;           // 用户的名称
    this.globalInfo = globalInfo; // 数据信息
};

// 错误返回
PDataDef.RD.ErrorResponse = function () {

};

PDataDef.RD.UpdateRankList = function () {
    this.totalUserNum = 0; // 总的用户人数
    this.userRankList = []; // 排行榜列表
};

// 更新玩家自己的排名信息
PDataDef.RD.UpdateSelfRank = function () {
    this.myRankPos = 0; // 我的排名
    this.myRank = {}; // 我的排行信息(PDataDef.UserRankInfo对象)
};

PDataDef.RD.UpdateGlobalInfo = function (globalInfo) {
    this.globalInfo = globalInfo; // 全量的数据信息(PDataDef.GlobalInfo对象)
};

PDataDef.RD.UpdateEatFood = function () {
    this.eatFoodInfo = [];  //PDataDef.EatFoodInfo对象数组
};

PDataDef.RD.UpdateSnakeDeath = function () {
    this.snakeKillInfo = [];   //PDataDef.SnakeKillInfo对象数组
};

// 更新蛇自杀(撞墙)
PDataDef.RD.UpdateSnakeSuicide = function () {
    this.snakeId = [];    // 撞墙的蛇ID数组
};

// 局时结束
PDataDef.RD.TimeOver = function () {
    this.totalUserNum = 0; // 总的用户人数
    this.userRankList = []; // 排行榜列表
    this.myRankPos = 0; // 我的排名
    this.myRank = {}; // 我的排行信息(PDataDef.UserRankInfo对象)
};

// 更新雷达信息
PDataDef.RD.UpdateRadarInfo = function (radarInfo) {
    this.radarInfo = radarInfo;     //PDataDef.RadarInfo对象
};

//公告类型
PDataDef.RD.Board_Type_Enum = {
    kill_top_three: 1, // 击杀前三名
    multi_kill: 2,     // 连续多杀
    total_kill: 3,     // 单局总杀戮
    revenge_kill: 4,   // 复仇击杀(仅自己可见)
};

PDataDef.RD.Top_Type_Enum = {
    kill_first: 1,     // 杀掉第一名
    kill_second: 2,    // 杀掉第二名
    kill_third: 3,     // 杀掉第三名
};
PDataDef.RD.Multi_Type_Enum = {
    two_kill: 1,       // 双杀
    three_kill: 2,     // 三杀
    four_kill: 3,      // 四杀
    five_kill: 4,      // 五杀
    six_kill: 5        // 五杀
};
PDataDef.RD.Total_Type_Enum = {
    da_sha_te_sha: 1,   // 大杀特杀
    jie_jin_bao_zou: 2, // 接近暴走
    wu_ren_ke_dang: 3,  // 无人可挡
    zhu_zai_bi_sai: 4,  // 主宰比赛
    jie_jin_shen_le: 5, // 接近神了
    cao_shen: 6,        // 超神
};

// 更新公告板信息
PDataDef.RD.UpdateCallBoardInfo = function () {

    this.boardType = 1;    // 公告类型
    this.killerName = "";  // 杀手昵称
    this.killedName = "";  // 被杀者昵称
    this.killCount = 0;    // 不同类型对应不同枚举值
};