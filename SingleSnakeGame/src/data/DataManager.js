/**
 * 20160420
 * created by brandyxie
 */

var DataManager = cc.Class.extend({
    isRegisterListen: false,
    nickName: "",
    maxLength: 0,
    maxHistoryLen: 0,
    lastId: -1,
    curPage: "",    //当前页面
    curScene: "",   //当前场景

    endData: null,

    ctor: function () {

    },

    init: function () {
        if (!this.isRegisterListen) {
            var self = this;
            CEventManager.addEventListener(CEventType.UPDATE_SNAKE_DEATH, function () {

                var result = this.checkSelfDead();
                if (!result.isSelfDead) {
                    return;
                }
                //var tipsStr = "你被" + result.killerName + "干掉了！";
                playerManager.destroyMainPlayer(function () {
                    if (!NetDataBuf.isTimeOver) {
                        //dataManager.maxLength = Math.max(dataManager.maxLength, NetDataBuf.globalInfo.snakeSelf.energy);
                        //dataManager.lastId = NetDataBuf.globalInfo.snakeSelf.snakeId;
                        //var config = {
                        //    tips: tipsStr,
                        //    name: result.killerName,
                        //    curLength: NetDataBuf.globalInfo.snakeSelf.energy,
                        //    maxLength: dataManager.maxLength
                        //};
                        setTimeout(function () {
                            if (!NetDataBuf.isTimeOver) {
                                self.onSnakeDead();
                            }
                        }, 800);
                    }
                });

                NetDataBuf.isSelfDead = true;
                cc.log("self be killed");
            }.bind(this), 1);

            CEventManager.addEventListener(CEventType.UPDATE_SNAKE_SUICIDE, function (event) {
                //撞墙的蛇id
                var result = this.checkSelfSuicide(event.data);
                if (!result.isSelfDead) {
                    return;
                }
                playerManager.destroyMainPlayer(function () {
                    if (!NetDataBuf.isTimeOver) {
                        //dataManager.maxLength = Math.max(dataManager.maxLength, NetDataBuf.globalInfo.snakeSelf.energy);
                        //dataManager.lastId = NetDataBuf.globalInfo.snakeSelf.snakeId;
                        //自己撞墙
                        //var config = {
                        //    tips: "\"你撞墙挂掉了!\"",
                        //    curLength: NetDataBuf.globalInfo.snakeSelf.energy,
                        //    maxLength: dataManager.maxLength
                        //};
                        setTimeout(function () {
                            if (!NetDataBuf.isTimeOver) {
                                self.onSnakeDead();
                            }
                        }, 800);
                    }
                });

                NetDataBuf.isSelfDead = true;
                cc.log("self hit wall");
            }.bind(this), 1);

            CEventManager.addEventListener(CEventType.SNAKE_REVIVE, function () {
                //复活
                playerManager.onMainPlayerRecovery();
                MusicManager.playMusic(MusicEffectFiles.Audio_bgm, true);
            }.bind(this), 1);

            CEventManager.addEventListener(CEventType.TIME_OVER, function () {
                //时间到
                console.log("游戏房间时间到了");
                MusicManager.stopAllEffects();
                MusicManager.stopMusic(true);

                var server = serverLogic;
                if (server) {
                    server.restart();
                    console.log("serverLogic.restart()***");
                }

                var curLength = Math.round(NetDataBuf.globalInfo.snakeSelf.energy);
                console.log("config.curLength= " + curLength);

                //upload score and time
                var timeUse = Math.round((gGameTime * 60 * 1000 - NetDataBuf.leftTime) * 0.001);
                console.log("timeUse= " + timeUse);

                setTimeout(function () {
                    //exchange scene
                    cc.director.runScene(new LoginScene());

                    //reset login request data
                    LOGIN_REQUEST_DATA.GAME_START = false;
                    LOGIN_REQUEST_DATA.USER_NAME = "";
                    LOGIN_REQUEST_DATA.USER_LENGTH = 0;
                    LOGIN_REQUEST_DATA.RANK_LIST = [];
                    //set default
                    ALREADY_SHOW_ACC = false;
                    //reset stage
                    gameConfigStage = gameConfig.stage_1;
                    gCurrStage = 1;

                    //upload data to page
                    window.playGame(curLength, timeUse);
                }, 1200);

            }.bind(this), 1);

            this.isRegisterListen = true;
        }

        //this.updateServerInfo();
        //message to let main scene know game start
        //cc.eventManager.dispatchCustomEvent(GameEvent.GAME_EVENT_SETUP, null);
    },

    checkSelfDead: function () {
        var result = {isSelfDead: false, killerId: -1, killerName: ""};
        var mySnakeId = NetDataBuf.globalInfo.snakeSelf.snakeId;
        if (NetDataBuf.snakeKillInfo) {
            for (var i in NetDataBuf.snakeKillInfo) {
                var killInfo = NetDataBuf.snakeKillInfo[i];
                if (killInfo && killInfo.snakeDeathInfo) {
                    for (var j in killInfo.snakeDeathInfo) {
                        var deadInfo = killInfo.snakeDeathInfo[j];
                        if (deadInfo && deadInfo.snakeId == mySnakeId) {
                            result.isSelfDead = true;
                            result.killerId = killInfo.killerId;
                            result.killerName = killInfo.killerName;

                        } else if (deadInfo) {
                            playerManager.destoryOtherById(deadInfo.snakeId);
                        }
                    }
                }
            }
        }

        return result;
    },

    getRankList: function () {
        return NetDataBuf.userRankList;
    },

    //remove some special character
    clearString: function (s) {
        //var pattern = new RegExp("[`~!@#$^&*()=|{}':;',\\[\\].<>/?~！@#￥……&*（）&;|{}【】‘；：”“'。，、]")
        var pattern = new RegExp("[\\[\\]]");
        var rs = "";
        for (var i = 0; i < s.length; i++) {
            rs = rs + s.substr(i, 1).replace(pattern, '');
        }
        return rs;
    },

    checkSelfSuicide: function (snakeIdList) {
        var result = {isSelfDead: false};
        var mySnakeId = NetDataBuf.globalInfo.snakeSelf.snakeId;
        if (snakeIdList) {
            for (var i in snakeIdList) {
                if (snakeIdList[i] == mySnakeId) {
                    result.isSelfDead = true;
                } else {
                    playerManager.destoryOtherById(snakeIdList[i]);
                }
            }
        }

        return result;
    },

    getEatenFoods: function () {
        return NetDataBuf.eatenFoods;
    },

    getFoods: function () {
        return NetDataBuf.globalInfo.foodInfo;
    },

    getInitFoods: function () {
        return NetDataBuf.initFoods;
    },

    getMainPlayerData: function () {
        return NetDataBuf.globalInfo.snakeSelf;
    },

    getOtherPlayerData: function () {
        return NetDataBuf.globalInfo.snakeOthers;
    },

    getFoodData: function () {
        return NetDataBuf.globalInfo.foodInfo;
    },

    /**
     * 获取雷达信息
     * @returns {(PDataDef.RadarInfo对象)|{}}
     */
    getRadarInfo: function () {
        return NetDataBuf.radarInfo;
    },

    getPlayerNameById: function (playerId) {
        var name = "";
        var otherPlayers = this.getOtherPlayerData();
        var length = otherPlayers || 0;
        for (var i = 0; i < length; i++) {
            var player = otherPlayers[i];
            if (player && player.snakeId == playerId) {
                name = player.name;
                break;
            }
        }
        return name;
    },

    onSnakeDead: function () {
        //stop game room server
        var server = serverLogic;
        if (server) {
            var handle = server.getHandler();
            if (handle) {
                handle.onClientClose();
            }
            server.restart();
            console.log("serverLogic.restart()***");
        }
    }
});

DataManager.GetInstance = function () {
    if (DataManager._instance == null) {
        DataManager._instance = new DataManager();
    }

    return DataManager._instance;
};

/**
 * server data manager instance
 */
var dataManager = DataManager.GetInstance();