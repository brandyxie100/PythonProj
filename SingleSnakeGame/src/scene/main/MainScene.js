/**
 * 20160329
 * created by brandyxie
 *
 */

var MainGameScene = cc.Scene.extend({
    _eventListener: null,
    _mapBgView: null,
    _mapBorder: null,
    _mainGameLayer: null,
    _mainUILayer: null,
    _scale: null,
    _frontSprite: null,
    _list: null,

    _curFPS: 0,

    onEnter: function () {
        console.log("MainGameScene: onEnter");
        this._super();

        //save original scale
        GAME_MAP_SCALE = GAME_MAP_ORIGINAL_SCALE;
        this._scale = GAME_MAP_SCALE;
        this._list = [];

        this._mapBgView = new MapBgView(mapSize);
        this.addChild(this._mapBgView, LAYER_DEF.BACKGROUND);

        var frontSprite = new cc.Sprite(res.bgFront_png);
        frontSprite.setPosition(cc.winSize.width / 2, cc.winSize.height / 2);
        UIHelper.adjustBgImage(frontSprite);
        this.addChild(frontSprite);
        this._frontSprite = frontSprite;

        this._mapBorder = new MapBorder(mapSize);
        this.addChild(this._mapBorder);
        //open light
        var bgLightSprite = new cc.Sprite(res.bgLight_png);
        bgLightSprite.setPosition(cc.winSize.width / 2, cc.winSize.height / 2);
        UIHelper.adjustBgImage(bgLightSprite);
        this.addChild(bgLightSprite);

        this._mainUILayer = new MainUILayer();
        this.addChild(this._mainUILayer, LAYER_DEF.UI_LAYER);

        this._mainGameLayer = new MainGameLayer();
        this.addChild(this._mainGameLayer, LAYER_DEF.UI_MAINGAME_LAYER);

        this._updateScale(GAME_MAP_SCALE);

        this._eventListener = [];
        Util.registerListener(this._eventListener, CEventType.ON_SNAKE_RECOVERY, this.onGameRestart.bind(this));
        Util.registerListener(this._eventListener, CEventType.UPDATE_GLOBAL_INFO, this.onUpdateServerInfo.bind(this));
        Util.registerListener(this._eventListener, CEventType.RESIZE_WINDOW, this._onWindowSizeReset.bind(this));

        //set view point center
        var mainPlayer = playerManager.getMainPlayer();
        if (mainPlayer) {
            this.setViewPointCenter(mainPlayer.getPosition());
        }

        //Mta.trackBeginPage("MainGameScene");
        dataManager.curScene = "MainGameScene";
        dataManager.curPage = "gamePage";

        //this._curFPS = 0;
        //this.fpsIntervalId = setInterval(function () {
        //cc.log("curFPS :" + this._curFPS);
        //StatisticUtil.recordRenderRate(this._curFPS);
        //this._curFPS = 0;
        //}.bind(this), 1000);
    },

    _onWindowSizeReset: function () {
        UIHelper.adjustBgImage(this._frontSprite);
    },

    onExit: function () {
        console.log("MainGameScene: onExit");
        MDlgManager.ClearAllDialog();

        if (this.fpsIntervalId != null) {
            clearInterval(this.fpsIntervalId);
        }
        this.fpsIntervalId = null;

        this._super();

        Util.unRegisterListeners(this._eventListener);

        //stop schedule
        this.unscheduleUpdate();

        //Mta.trackEndPage("MainGameScene");
    },

    _updateScale: function (scale) {
        this._mapBgView.setScale(scale);
        this._mapBorder.setScale(scale);
        this._mainGameLayer.setScale(scale);
    },

    onUpdateServerInfo: function () {
        //var time = Date.now();
        //reset window size
        var viewScale = NetDataBuf.globalInfo.viewSize;
        var scale = 1 / (viewScale * 0.00001) * 0.1;
        if (this._scale != scale) {
            GAME_MAP_SCALE = scale;
            this._scale = scale;
            this._updateScale(scale);

            //console.log("current viewScale : " + viewScale);
            //console.log("onUpdateServerInfo: scale= " + scale);
        }

        //update all position by server
        this.updateAllPlayers();

        //update view point
        if (playerManager.getMainPlayer()) {
            var pos = NetDataBuf.globalInfo.snakeSelf.bodyPoints[0];
            this.setViewPointCenter(cc.p(pos.xPos, pos.yPos));
        }
        //console.log("onUpdateServerInfo: cost time= " + (Date.now() - time));
    },

    updateAllPlayers: function () {
        playerManager.updateMainPlayer();
        playerManager.updateOtherPlayer();
    },

    //set view point center of window
    setViewPointCenter: function (pos) {
        var winSize = cc.winSize;
        var scaleHalfWidth = winSize.width / 2;
        var scaleHalfHeight = winSize.height / 2;
        var x = Math.max(pos.x, scaleHalfWidth); //use methods and functions of math
        var y = Math.max(pos.y, scaleHalfHeight);
        x = Math.min(x, mapRadius + mapBorder * 2 - scaleHalfWidth);
        y = Math.min(y, mapRadius + mapBorder * 2 - scaleHalfHeight);

        var actualPosition = cc.p(x, y); //create a point
        var centerOfView = cc.p(scaleHalfWidth, scaleHalfHeight);
        var viewPointX = centerOfView.x - actualPosition.x;
        var viewPointY = centerOfView.y - actualPosition.y;

        //set layer's position
        var positionX = viewPointX * GAME_MAP_SCALE;
        var positionY = viewPointY * GAME_MAP_SCALE;
        this._mapBgView.setPosition(positionX, positionY);
        this._mapBorder.setPosition(positionX, positionY);
        this._mainGameLayer.setPosition(positionX, positionY);
        snakeMoveController.setViewPortOffset(this._mapBgView.getPosition());
    },

    onGameRestart: function () {
        GAME_MAP_SCALE = GAME_MAP_ORIGINAL_SCALE;
        this._updateScale(GAME_MAP_SCALE);
        console.log("reset game scale");
    },
});
