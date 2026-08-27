/**
 * Created by brandyxie
 * 20160414.
 */

var LoadingLayer = cc.Layer.extend({
    _bEnd: null,
    _node: null,
    _action: null,
    _listenerList: null,

    ctor: function () {
        this._super();
        var root = ccs.load(res.Loading_json);
        this._node = root.node;
        UIHelper.adjustUILayout(this._node);
        this.addChild(this._node);

        this._action = root.action;
        this._action.retain();
        this._bEnd = false;

        this._listenerList = [];
        Util.registerListener(this._listenerList, CEventType.INIT_GAME, this._onEnterMainScene.bind(this));
        Util.registerListener(this._listenerList, CEventType.RESIZE_WINDOW, this._onWindowSizeReset.bind(this));
        Util.registerListener(this._listenerList, CEventType.ON_START_GAME_EVENT, this._onStartServer.bind(this));
    },

    startLoading: function () {
        this._bEnd = false;
        this._node.stopAllActions();
        var action = this._action.clone();
        action.setLastFrameCallFunc(this._onLastFrameCallBack.bind(this));
        this._node.runAction(action);
        action.gotoFrameAndPlay(45, action.getDuration(), 45, false);

        //start game
        this._onStartServer();
    },

    _onLastFrameCallBack: function () {
        if (!this._bEnd) {
            this._bEnd = true;
            var action = this._action.clone();
            action.setLastFrameCallFunc(this._onLastFrameCallBack.bind(this));
            this._node.runAction(action);
            action.gotoFrameAndPlay(285, action.getDuration(), 285, false);
            this.scheduleOnce(this._onReachTime, 0.1);
        }
    },

    _onReachTime: function () {
        this._bEnd = false;
    },

    _onEnterMainScene: function () {
        //initialize data manager
        cc.director.runScene(new cc.TransitionFade(1.2, new MainGameScene()));
    },

    _onWindowSizeReset: function () {
        UIHelper.adjustUILayout(this._node);
    },

    _onStartServer: function () {
        if (!LOGIN_REQUEST_DATA.GAME_START) {
            return;
        }

        //run server
        var duration = 100;
        setTimeout(function () {

            NetProxy.startServer();

        }, duration);
    },

    onEnter: function () {
        this._super();
    },

    onExit: function () {
        this._super();

        Util.unRegisterListeners(this._listenerList);
        UIHelper.release(this._action);
    }
});

var LoginScene = cc.Scene.extend({

    onEnter: function () {
        this._super();
        console.log("LoginScene: onEnter");

        // Local / standalone play: originally this game expected a host H5 SDK
        // to call NetProxy.Login(). Without that, GAME_START stays false and
        // the loading loop never enters the match. Seed a local session so the
        // embedded serverLogic can start.
        setTimeout(function () {
            var rankList = [
                {openid: "local-1", nickName: "Alpha", img: "", score: 180},
                {openid: "local-2", nickName: "Bravo", img: "", score: 240},
                {openid: "local-3", nickName: "Charlie", img: "", score: 320},
                {openid: "local-4", nickName: "Delta", img: "", score: 480},
                {openid: "local-5", nickName: "Echo", img: "", score: 786}
            ];
            NetProxy.Login("Player", 0, "", rankList);
        }, 100);

        //loading layer
        var loadingLayer = new LoadingLayer();
        this.addChild(loadingLayer);

        //start loading
        loadingLayer.startLoading();
    }
});