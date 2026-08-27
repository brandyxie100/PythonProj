/**
 * Created by billbao on 2016/4/22.
 */

var PDataParser = {
    globalInfoQueue: null,
    eatFoodQueue: null,
    events: {},
    //lastServerTime: 0
};

PDataParser.getEventByType = function (type, data) {
    if (this.events[type] == null) {
        this.events[type] = new CEvent(type);
    }
    this.events[type].data = data;
    return this.events[type];
};

PDataParser.onHandleMessage = function (msg, list) {
    //cc.log("serverTime: " + msg.messageHead.serverTime);
    //var time = Date.now();
    var msgSize = msg.messageType.length;
    //cc.log("msgSize: " + msgSize);
    for (var i = 0; i < msgSize; i++) {
        var messageType = msg.messageType[i];

        //if (this.lastServerTime != 0 && messageType == 202) {
        //var interval = msg.messageHead.serverTime - this.lastServerTime;
        //this.lastServerTime = msg.messageHead.serverTime;
        //cc.log("onHandleMessage:" + interval);
        //if (messageType == 202 && interval > 50) {
        //netManager.longtimeFrames++;
        //StatisticUtil.netLongFrames++;
        //}
        //} else if (messageType == 202) {
        //    this.lastServerTime = msg.messageHead.serverTime;
        //}
        switch (messageType) {
            case PDataDef.RD.SMsgType.PING_RESPONSE:
            {
                //心跳回应
                PDataParser._start();
                this.onPingRsp(msg.pingResponse);
                PDataParser._end("PING_RESPONSE", list);
            }
                break;
            case PDataDef.RD.SMsgType.LOGIN_RESPONSE:
            {
                //玩家初始化
                PDataParser._start();
                this.onLoginRsp(msg.loginResponse);
                PDataParser._end("LOGIN_RESPONSE", list);
            }
                break;
            case PDataDef.RD.SMsgType.REVIVE_RESPONSE:
            {
                //玩家复活
                PDataParser._start();
                this.onReviveRsp(msg.reviveResponse);
                //SnakeDeadLayer.Close();
                PDataParser._end("REVIVE_RESPONSE", list);
            }
                break;
            case PDataDef.RD.SMsgType.ERROR_RESPONSE:
            {
                //服务端返回了错误
                PDataParser._start();
                this.onErrRsp(msg.errorResponse, msg.messageHead.errorCode);
                PDataParser._end("ERROR_RESPONSE", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_GLOBAL_INFO:
            {
                //更新全量信息
                PDataParser._start();
                this.onUpdateGlobalInfo(msg.updateGlobalInfo, msg.messageHead.serverTime);
                PDataParser._end("UPDATE_GLOBAL_INFO", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_RANK_LIST:
            {
                //刷新排行
                PDataParser._start();
                this.onUpdateRankList(msg.updateRankList);
                PDataParser._end("UPDATE_RANK_LIST", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_EAT_FOOD:
            {
                //刷新被吃食物
                PDataParser._start();
                this.onUpdateEatFood(msg.updateEatFood);
                PDataParser._end("UPDATE_EAT_FOOD", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_SNAKE_DEAD:
            {
                //刷新蛇死亡信息
                PDataParser._start();
                this.onUpdateKillInfo(msg.updateSnakeDeath);
                PDataParser._end("UPDATE_SNAKE_DEAD", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_SNAKE_SUICIDE:
            {
                //刷新蛇撞墙
                PDataParser._start();
                this.onUpdateSnakeSuicide(msg.updateSnakeSuicide);
                PDataParser._end("UPDATE_SNAKE_SUICIDE", list);
            }
                break;
            case PDataDef.RD.SMsgType.TIME_OVER:
            {
                //局时到
                PDataParser._start();
                this.onTimeOver(msg.timeOver);
                PDataParser._end("TIME_OVER", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_RADAR_INFO:
            {
                //更新雷达信息
                PDataParser._start();
                this.onUpdateRadarInfo(msg.updateRadarInfo);
                PDataParser._end("UPDATE_RADAR_INFO", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_SELF_RANK:
            {
                //更新自己的排行信息
                PDataParser._start();
                this.onUpdateSelfRank(msg.updateSelfRank);
                PDataParser._end("UPDATE_SELF_RANK", list);
            }
                break;
            case PDataDef.RD.SMsgType.UPDATE_CALL_BOARD:
            {
                //公告消息
                PDataParser._start();
                this.onUpdateBoard(msg.updateCallBoardInfo);
                PDataParser._end("UPDATE_CALL_BOARD", list);
            }
                break;
            default :
            {
                cc.log("undefined message!");
            }
                break;
        }
    }
    //console.log("PDataParser.onHandleMessage: cost time= " + (Date.now() - time));
};

PDataParser._start = function () {
    return;
    PDataParser._startTime = new Date().getTime();
};

PDataParser._end = function (funName, list) {
    //console.log("PDataParser: " + funName);
    return;
    PDataParser._endTime = new Date().getTime();
    var time = PDataParser._endTime - PDataParser._startTime;
    list.push({time: time, funName: funName});
};

PDataParser.onPingRsp = function (pingResponse) {
    //cc.log("rspHeartbeat");
    //netManager.closeHeartbeatTiemOut();
};

PDataParser.onLoginRsp = function (loginResponse) {
    //netManager.closeLoginTiemOut();
    if (!loginResponse) {
        netManager.disconnectServer();
        //NetErrHandler.handleError(-1, stringRes.getString("NET_TIPS_LOGIN_DATA_NULL"));
        return;
    }

    NetDataBuf.isLogin = true;
    NetDataBuf.isSelfDead = false;
    NetDataBuf.isTimeOver = false;
    NetDataBuf.endTime = loginResponse.endTime;
    NetDataBuf.nickName = loginResponse.name;
    NetDataBuf.globalInfo = loginResponse.globalInfo;
    NetDataBuf.initFoods = loginResponse.globalInfo.foodInfo;

    mapRadius = NetDataBuf.globalInfo.mapRadius * 2;
    mapBorder = NetDataBuf.globalInfo.mapBorder;
    mapSize = cc.size(mapBorder * 2 + mapRadius, mapBorder * 2 + mapRadius);
    this.viewSize = NetDataBuf.globalInfo.viewSize;

    //save some information of mine
    //MY_SNAKE_NAME = loginResponse.name;
    MY_SKIN_ID = NetDataBuf.globalInfo.snakeSelf.skinId;
    MY_SNAKE_ID = NetDataBuf.globalInfo.snakeSelf.snakeId; //save my snake ID

    var evt = this.getEventByType(CEventType.INIT_GAME)/*new CEvent(CEventType.INIT_GAME)*/;
    CEventManager.dispatchEvent(evt);

    //var curTime = new Date().getTime();
    //var leftTime = NetDataBuf.endTime - curTime;
    //Mta.trackCustomKVEvent("onEnterRoom", {
    //    "leftTime": ("" + Math.round(leftTime / 1000)),
    //    "roomId": "" + dataManager.selectedRoomId
    //});

};

PDataParser.onReviveRsp = function (reviveResponse) {
    if (!reviveResponse) {
        return;
    }
    NetDataBuf.isSelfDead = false;
    NetDataBuf.nickName = reviveResponse.name;
    NetDataBuf.globalInfo = reviveResponse.globalInfo;
    NetDataBuf.initFoods = reviveResponse.globalInfo.foodInfo;

    //mapRadius = NetDataBuf.globalInfo.mapRadius * 2;
    //mapBorder = NetDataBuf.globalInfo.mapBorder;
    //mapSize = cc.size(mapBorder * 2 + mapRadius, mapBorder * 2 + mapRadius);
    //this.viewSize = NetDataBuf.globalInfo.viewSize;

    var evt = this.getEventByType(CEventType.SNAKE_REVIVE)/*new CEvent(CEventType.SNAKE_REVIVE)*/;
    CEventManager.dispatchEvent(evt);
};

PDataParser.onErrRsp = function (errResponse, errCode) {
    //netManager.closeLoginTiemOut();
    netManager.disconnectServer();
    //NetErrHandler.handleError(-1, "服务器返回了错误!");
    //if (1 == errCode) {
    //    var evt = this.getEventByType(CEventType.NET_WORK_ERR, {text: "your version is too old!"});
    //    CEventManager.dispatchEvent(evt);
    //    //UpgradeDialog.Show();
    //} else if (2 == errCode) {
    //    //var evt = this.getEventByType(CEventType.NET_WORK_ERR, {text: "nickname_not_accept!"});
    //    //CEventManager.dispatchEvent(evt);
    //    //NetStatusTips.Show("昵称有问题，需要重新输入昵称!");
    //    //SensitiveNickNameWindow.Show();
    //} else if (3 == errCode) {
    //    var evt = this.getEventByType(CEventType.NET_WORK_ERR, {text: "room_is_full!"});
    //    CEventManager.dispatchEvent(evt);
    //    NetStatusTips.Show(stringRes.getString("NET_TIPS_ROOM_FULL"));
    //} else {
    //    var evt = this.getEventByType(CEventType.NET_WORK_ERR, {text: "unknown net error!"});
    //    CEventManager.dispatchEvent(evt);
    //    NetStatusTips.Show(stringRes.getString("NET_TIPS_UNKNOWN_ERROR"));
    //}
};

PDataParser.onUpdateGlobalInfo = function (updateGlobalInfo, curServerTime) {
    //cc.log("PDataParser.onUpdateGlobalInfo");
    NetDataBuf.leftTime = Math.max(NetDataBuf.endTime - curServerTime, 0);
    if (!updateGlobalInfo) {
        return;
    }
    NetDataBuf.globalInfo = updateGlobalInfo.globalInfo;
    //NetDataBuf.isNewGlobalInfo = true;

    var evt = this.getEventByType(CEventType.UPDATE_GLOBAL_INFO)/*new CEvent(CEventType.UPDATE_GLOBAL_INFO)*/;
    CEventManager.dispatchEvent(evt);
    //cc.log("PDataParser.onUpdateGlobalInfo end");
};

PDataParser.onUpdateRankList = function (updateRankList) {
    //if (!updateRankList) {
    //    return;
    //}
    //NetDataBuf.playersNum = updateRankList.totalUserNum;
    //NetDataBuf.userRankList = updateRankList.userRankList || [];
    //
    //var evt = this.getEventByType(CEventType.UPDATE_RANK)/*new CEvent(CEventType.UPDATE_RANK)*/;
    //CEventManager.dispatchEvent(evt);
    //
    ////雷达信息合到排行榜信息里面了
    //evt = this.getEventByType(CEventType.UPDATE_RADAR_INFO)/*new CEvent(CEventType.UPDATE_RADAR_INFO)*/;
    //CEventManager.dispatchEvent(evt);
};

PDataParser.onUpdateEatFood = function (updateEatFood) {
    if (!updateEatFood) {
        return;
    }
    NetDataBuf.eatenFoods = updateEatFood.eatFoodInfo || [];

    var evt = this.getEventByType(CEventType.UPDATE_EAT_FOOD)/*new CEvent(CEventType.UPDATE_EAT_FOOD)*/;
    CEventManager.dispatchEvent(evt);
};

PDataParser.onUpdateKillInfo = function (updateSnakeDeath) {
    if (!updateSnakeDeath) {
        return;
    }
    NetDataBuf.snakeKillInfo = updateSnakeDeath.snakeKillInfo || [];

    var evt = this.getEventByType(CEventType.UPDATE_SNAKE_DEATH)/*new CEvent(CEventType.UPDATE_SNAKE_DEATH)*/;
    CEventManager.dispatchEvent(evt);
};

PDataParser.onUpdateSnakeSuicide = function (updateSnakeSuicide) {
    if (!updateSnakeSuicide) {
        return;
    }
    var evt = this.getEventByType(CEventType.UPDATE_SNAKE_SUICIDE, updateSnakeSuicide.snakeId)/*new CEvent(CEventType.UPDATE_SNAKE_SUICIDE, updateSnakeSuicide.snakeId)*/;
    CEventManager.dispatchEvent(evt);
};

PDataParser.onTimeOver = function (timeOver) {
    NetDataBuf.isTimeOver = true;

    if (timeOver) {
        NetDataBuf.playersNum = timeOver.totalUserNum;
        NetDataBuf.userRankList = timeOver.userRankList || [];
        NetDataBuf.myRank = timeOver.myRankPos;
        if (timeOver.myRank) {
            NetDataBuf.myRankInfo = timeOver.myRank;
        }
    }

    var evt = this.getEventByType(CEventType.TIME_OVER);
    CEventManager.dispatchEvent(evt);
};

PDataParser.onUpdateRadarInfo = function (updateRadarInfo) {
    if (!updateRadarInfo) {
        return;
    }
    NetDataBuf.radarInfo = updateRadarInfo.radarSnakeInfo;

    var evt = this.getEventByType(CEventType.UPDATE_RADAR_INFO);
    CEventManager.dispatchEvent(evt);
};

PDataParser.onUpdateSelfRank = function (updateSelfRank) {
    if (!updateSelfRank) {
        return;
    }
    NetDataBuf.myRank = updateSelfRank.myRankPos;
    if (updateSelfRank.myRank && updateSelfRank.myRank.energy) {
        NetDataBuf.myRankInfo = updateSelfRank.myRank;
    }

    var evt = this.getEventByType(CEventType.UPDATE_SELF_RANK)/*new CEvent(CEventType.UPDATE_SELF_RANK)*/;
    CEventManager.dispatchEvent(evt);
};

PDataParser.onUpdateBoard = function (updateCallBoardInfo) {
    //console.log('PDataParser.onUpdateBoard= ' + updateCallBoardInfo);
    if (!updateCallBoardInfo) {
        return;
    }

    this.boardMsgQueue.enqueue(updateCallBoardInfo);
    //console.log('PDataParser.onUpdateBoard= ' + this.boardMsgQueue.size());

};