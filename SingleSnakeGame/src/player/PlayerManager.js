/**
 * 20160407
 * created by brandyxie
 *
 */

var PlayerManager = cc.Class.extend({
    _mainPlayer: null,
    _otherPlayers: null,
    _diedSnakeArray: null,
    _parent: null,
    _isMainPlayerDied: null,
    _viewPointPos: null,
    _canAccPanel: null,
    _guideNoticeBkg: null,
    _rankIndex: -1,
    _oldEnergy: 10,
    _addEnergy: null,

    _headFaceBatchNode: null,
    //moveSnakeEyes: null,

    ctor: function () {

    },

    init: function (mainGameLayer) {
        this._parent = mainGameLayer;

        this._otherPlayers = [];
        this._diedSnakeArray = [];
        this._headFaceBatchNode = null;
        this._isMainPlayerDied = false;

        //add skin plist file
        var frameCache = cc.spriteFrameCache;
        frameCache.addSpriteFrames(res.snake_plist);

        //create sprite batch for body skin
        this._headFaceBatchNode = new cc.SpriteBatchNode(res.snake_png);
        this._parent.addChild(this._headFaceBatchNode, LAYER_DEF.PLAYER_SNAKE_HEAD);

        //add notice panel
        var accRes = "canNotAcc.png";
        var spriteAcc = new cc.Sprite();
        spriteAcc.initWithSpriteFrameName(accRes);
        spriteAcc.setAnchorPoint(0.5, 0.5);
        spriteAcc.setVisible(false);
        this._parent.addChild(spriteAcc, LAYER_DEF.PLAYER_SNAKE_HEAD);
        this._notifyPanel = spriteAcc;

        accRes = "canAcc.png";
        spriteAcc = new cc.Sprite();
        spriteAcc.initWithSpriteFrameName(accRes);
        spriteAcc.setAnchorPoint(0.5, 0.5);
        spriteAcc.setVisible(false);
        this._parent.addChild(spriteAcc, LAYER_DEF.PLAYER_SNAKE_HEAD);
        this._canAccPanel = spriteAcc;

        //add energy animation
        accRes = "add_plus.png";
        spriteAcc = new cc.Sprite();
        spriteAcc.initWithSpriteFrameName(accRes);
        spriteAcc.setVisible(false);
        this._parent.addChild(spriteAcc, LAYER_DEF.PLAYER_SNAKE_HEAD);
        this._addEnergy = spriteAcc;
    },

    getMainPlayer: function () {
        return this._mainPlayer;
    },

    clearAll: function () {
        if (this._mainPlayer) {
            this._mainPlayer.destroy();
        }
        if (this._otherPlayers) {
            var player = null;
            for (var i in this._otherPlayers) {
                player = this._otherPlayers.pop();
                player.destroy();
            }
        }
        if (this._headFaceBatchNode) {
            this._headFaceBatchNode.removeAllChildren(true);
            this._headFaceBatchNode.removeFromParent(true);
        }
        if (this._notifyPanel) {
            this._notifyPanel.removeFromParent(true);
        }
        this.hideGuideNotice();

        this._notifyPanel = null;
        this._headFaceBatchNode = null;
        this._mainPlayer = null;
        this._isMainPlayerDied = false;
        this._otherPlayers = [];
        this._diedSnakeArray = [];
        this._rankIndex = -1;
        this._oldEnergy = 10;
    },

    addSpriteToBatch: function (sprite) {
        if (sprite) {
            this._headFaceBatchNode.addChild(sprite);
        }
    },

    createMainPlayer: function () {
        var data = dataManager.getMainPlayerData();
        if (null == data) {
            //console.log("createMainPlayer: null==data!")
            return;
        }
        //save view point position
        this._viewPointPos = cc.p(data.bodyPoints[0].xPos, data.bodyPoints[0].yPos);

        var snake = this.createOneSnake(data);
        this._mainPlayer = snake;
    },

    //get data from server
    createOtherPlayer: function () {
        var dataArray = dataManager.getOtherPlayerData();
        if (null == dataArray || 0 == dataArray.length) {
            //console.log("createOtherPlayer: null == dataArray!")
            return;
        }
        var len = dataArray.length;
        var data = null;
        var snake = null;
        for (var i = 0; i < len; ++i) {
            data = dataArray[i];
            snake = this.createOneSnake(data);
            this._otherPlayers.push(snake);
        }
    },

    createOneSnake: function (data) {
        var snake = new Snake(); //data.skinId
        snake.createSnake(data);

        this._parent.addChild(snake, LAYER_DEF.PLAYER_SNAKE_BODY);

        return snake;
    },

    setNotifyPanel: function (visible) {
        if (this._notifyPanel) {
            this._notifyPanel.setVisible(visible);
        }
    },

    runNotifyAnim: function () {
        if (this._notifyPanel && 0 == this._notifyPanel.getNumberOfRunningActions()) {
            this._notifyPanel.setVisible(true);
            this._notifyPanel.setOpacity(300);
            this._notifyPanel.runAction(cc.fadeOut(2.5));
        }
    },

    notifyCanAcc: function (time) {
        if (this._canAccPanel) {
            this._notifyPanel.stopAllActions();
            this._canAccPanel.stopAllActions();
            this._canAccPanel.setVisible(true);
            this._canAccPanel.setOpacity(300);
            this._canAccPanel.runAction(cc.fadeOut(time));
        }

        //send message
        CEventManager.dispatchEvent(new CEvent(CEventType.ON_ACC_BTN_NOTICE));
    },

    showGuideNotice: function (index, pos) {
        this.hideGuideNotice();

        //add notice control
        var noticeBkg = "new_paopao_" + index + ".png";
        var sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName(noticeBkg);
        sprite.setAnchorPoint(0.5, 0.5);
        sprite.setVisible(true);
        this._parent.addChild(sprite, LAYER_DEF.PLAYER_SNAKE_HEAD);
        this._guideNoticeBkg = sprite;

        if (pos) {
            this._guideNoticeBkg.setPosition(pos.x, pos.y);
        }
    },

    hideGuideNotice: function () {
        if (this._guideNoticeBkg) {
            this._guideNoticeBkg.stopAllActions();
            this._guideNoticeBkg.removeFromParent(true);
            this._guideNoticeBkg = null;
        }
    },

    removeCanAccNotice: function () {
        if (this._canAccPanel) {
            this._canAccPanel.stopAllActions();
            this._canAccPanel.removeFromParent(true);
            this._canAccPanel = null;
        }
    },

    updateMainPlayer: function () {
        if (!this._mainPlayer || this._isMainPlayerDied) {
            return;
        }
        var data = dataManager.getMainPlayerData();
        if (null == data) {
            return;
        }

        //update view point position
        this._viewPointPos = cc.p(data.bodyPoints[0].xPos, data.bodyPoints[0].yPos);
        //update position
        if (this._notifyPanel) {
            this._notifyPanel.setPosition(this._viewPointPos.x - 26, this._viewPointPos.y + 90);
        }
        this._headFaceBatchNode.setPosition(this._viewPointPos);

        if (this._canAccPanel) {
            this._canAccPanel.setPosition(this._viewPointPos.x - 26, this._viewPointPos.y + 90);
        }
        if (this._guideNoticeBkg) {
            this._guideNoticeBkg.setPosition(this._viewPointPos.x - 26, this._viewPointPos.y + 90);
        }

        this._mainPlayer.updateSnakePos(data);

        //update player energy data here
        var energy = Math.round(data.energy);
        if (energy == this._oldEnergy) {
            return;
        }
        var add = energy - this._oldEnergy;
        this._oldEnergy = energy;
        if (add < 0 || add >= 100) {
            return;
        }

        //add energy animation
        //update icon
        var headPos = this.getMainPlayer().getHeadPosition();
        if (this._addEnergy) {
            this._addEnergy.stopAllActions();
            this._addEnergy.removeAllChildren(true);
            this._addEnergy.setPosition(headPos);
            this._addEnergy.setOpacity(300);
        }
        var shi = Math.floor(add / 10);
        var ge = add % 10;
        var offset = 0;
        var pos = cc.p(34, 10);
        var picRes;
        var sprite;
        if (shi > 0) { //十位
            sprite = new cc.Sprite();
            picRes = "add_" + shi + ".png"
            sprite.initWithSpriteFrameName(picRes);
            sprite.setPosition(pos.x, pos.y);
            this._addEnergy.addChild(sprite, 1);
            offset = 18;
        }
        //个位
        picRes = "add_" + ge + ".png";
        sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName(picRes);
        sprite.setPosition(pos.x + offset, pos.y);
        this._addEnergy.addChild(sprite, 1);
        this._addEnergy.setVisible(true);

        //run action
        pos = cc.p(headPos.x, headPos.y + 68);
        var action = this._createAction(pos);
        this._addEnergy.runAction(action);

        //send exceed notice message
        var rankData = LOGIN_REQUEST_DATA.RANK_LIST;
        if (!rankData || rankData.length <= 0) {
            return;
        }
        var length = rankData.length;
        var index = this._rankIndex;
        if (rankData[length - 1].score < energy) {
            index = length - 1;
        } else {
            for (var i = 0; i < length - 1; ++i) {
                if (rankData[i + 1].score > energy && energy > rankData[i].score) {
                    index = i;
                    break;
                }
            }
        }
        //only notice new rank
        if (index > this._rankIndex) {
            this._rankIndex = index;
            //send message
            CEventManager.dispatchEvent(new CEvent(CEventType.EXCEED_FRIEND_NOTICE, index));
        }
    },

    _createAction: function (targetPosition) {
        var duration = 0.6;
        var moveAction = cc.moveTo(duration, targetPosition);
        var fadeOutAction = cc.fadeOut(0.8);
        var spawnAction = cc.spawn(moveAction, fadeOutAction);
        var callback = new cc.CallFunc(this._onMoveActionComplete, this);
        var action = new cc.Sequence(spawnAction, callback);
        return action;
    },

    _onMoveActionComplete: function () {
        this._addEnergy.setVisible(false);
    },

    updateOtherPlayer: function () {
        var dataArray = dataManager.getOtherPlayerData();
        if (null == dataArray) {
            return;
        }

        //if send too many players
        var data = null;
        var player = null;
        var total = dataArray.length;
        for (var i = 0; i < total; ++i) {
            data = dataArray[i];
            if (this.isSnakeDied(data.snakeId)) {
                continue;
            }

            player = this.getPlayerByID(data.snakeId);
            if (null != player) { //there already is one
                player.updateSnakePos(data);
                player.showSnake();

            } else { //create a new player
                player = this.createOneSnake(data);
                this._otherPlayers.push(player);
            }
        }

        //release invisible snake
        var length = this._otherPlayers.length;
        var exist = false;
        for (var i = 0; i < length; ++i) {
            player = this._otherPlayers[i];
            exist = false;
            for (var j = 0; j < total; ++j) {
                data = dataArray[j];
                if (data.snakeId == player.getPlayerID()) {
                    exist = true;
                    break;
                }
            }
            if (!exist) {
                player.hideSnake();
                player.destroy();
                this._otherPlayers.splice(i, 1);
                length = this._otherPlayers.length;
            }
        }
    },

    onMainPlayerRecovery: function () {
        cc.log("onMainPlayerRecovery");
        this._isMainPlayerDied = false;
        this.createMainPlayer();

        //reset game scale
        GAME_MAP_SCALE = 1;
        var evt = new CEvent(CEventType.ON_SNAKE_RECOVERY);
        CEventManager.dispatchEvent(evt);
    },

    onMainPlayerDied: function () {
        if (this._mainPlayer) {
            this.removePlayerByID(this._mainPlayer._id);
        }
        this._mainPlayer = null;
        this._isMainPlayerDied = true;
    },

    destroyMainPlayer: function (callback) {
        //whether need show notice
        if (this._notifyPanel) {
            var pos = this._notifyPanel.getPosition();
            var maxLength = Math.round(Math.max(dataManager.maxHistoryLen, NetDataBuf.globalInfo.snakeSelf.energy));
            if (maxLength < gameConfig.notice.notice_die_len) {

                this.showGuideNotice(3, pos);
            }
        }

        if (this._mainPlayer) {
            this._mainPlayer.died(callback, 0.7);
        }
        this._mainPlayer = null;
        this._isMainPlayerDied = true;

    },

    destoryOtherById: function (playerID) {
        var length = this._otherPlayers.length;
        var player = null;
        for (var i = 0; i < length; ++i) {
            player = this._otherPlayers[i];
            if (player && (playerID == player.getPlayerID())) {
                this._diedSnakeArray.push(playerID);

                //release this ball
                player.died(function () {
                    //this.removeDeadSnakeId(playerID);
                }.bind(this), 1.0);

                this._otherPlayers.splice(i, 1);
                break;
            }
        }
    },

    isSnakeDied: function (snakeID) {
        var length = this._diedSnakeArray.length;
        for (var j = 0; j < length; ++j) {
            if (snakeID == this._diedSnakeArray[j]) {
                return true;
            }
        }
        return false;
    },

    removeDeadSnakeId: function (snakeID) {
        var length = this._diedSnakeArray.length;
        for (var j = 0; j < length; ++j) {
            if (snakeID == this._diedSnakeArray[j]) {
                this._diedSnakeArray.splice(j, 1);
                break;
            }
        }
    },

    removeAllDiedPlayers: function () {
        console.log("removeAllDiedPlayers");

        var player = null;
        var len = this._otherPlayers.length;
        for (var i = 0; i < len; ++i) {
            player = this._otherPlayers.pop();
            player.destroy();
        }
        this._otherPlayers = [];
        this.createOtherPlayer();
    },

    getViewPointPos: function () {
        return this._viewPointPos;
    },

    getPlayerPositionByID: function (playerID) {
        if (this._mainPlayer && this._mainPlayer.getPlayerID() == playerID) {
            return this._viewPointPos;
        }

        var player = this.getPlayerByID(playerID);
        if (null != player) {
            return player.getHeadPosition();
        }

        //console.log("playerID error");
        return null;
    },

    getPlayerByID: function (playerID) {
        var length = this._otherPlayers.length;
        var player = null;
        for (var i = 0; i < length; ++i) {
            var data = this._otherPlayers[i];
            if (playerID == data.getPlayerID()) {
                player = data;
                break;
            }
        }

        return player;
    },

    removePlayerByID: function (playerID) {
        var length = this._otherPlayers.length;
        var player = null;
        for (var i = 0; i < length; ++i) {
            player = this._otherPlayers[i];
            if (player && (playerID == player.getPlayerID())) {
                //release this player
                player.destroy();

                this._otherPlayers.splice(i, 1);
                break;
            }
        }
    },

    addNewPlayer: function (newPlayer) {
        if (null == newPlayer) {
            console.log("addNewPlayer: null == newPlayer");
            return;
        }

        var playerID = newPlayer.getPlayerID();
        var player = this.getPlayerByID(playerID);
        if (null == player) {
            this._otherPlayers.push(newPlayer);
        }
        else {
            console.log("addNewBall: add repeatedly");
        }
    },

    //moveSnakeEyes: function (pos) {
    //if (null == this._mainPlayer) {
    //    return;
    //}
    //this._mainPlayer.updateEyesPos(pos);
    //},

    //updateAllPlayerLocally: function (dt) {
    //    if (!this._mainPlayer || this._isMainPlayerDied) {
    //        return;
    //    }
    //
    //    this._mainPlayer.updatePosition(dt);
    //
    //    var length = this._otherPlayers.length;
    //    var player = null;
    //    for (var i = 0; i < length; ++i) {
    //        player = this._otherPlayers[i];
    //        player.updatePosition(dt);
    //    }
    //},

});

PlayerManager.getInstance = function () {
    if (PlayerManager._instance == null) {
        PlayerManager._instance = new PlayerManager();
    }

    return PlayerManager._instance;
};

/**
 * manage the array of all players
 */
var playerManager = PlayerManager.getInstance();