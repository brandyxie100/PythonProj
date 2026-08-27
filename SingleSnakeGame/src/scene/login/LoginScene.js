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

        //only for test
        //setTimeout(function () {
        //    var rankList = [
        //        {
        //            "openid": "HJEHFJPOFOIEJF",
        //            "nickName": "jowzhang\uff08ZJ\uff09",
        //            "img": "",
        //            "score": 180
        //        },
        //        {
        //            "openid": "HJEH89LJF898OIEJF",
        //            "nickName": "Encore",
        //            "img": "",
        //            "score": 240
        //        },
        //        {
        //            "openid": "HJZSFDF898OIEJF",
        //            "nickName": "test_test",
        //            "img": "",
        //            "score": 320
        //        },
        //        {
        //            "openid": "HJEH89HFF8OIEJF",
        //            "nickName": "eteaganhnhgge",
        //            "img": "",
        //            "score": 480
        //        },
        //        {
        //            "openid": "HJEH89LJF89FTEJF",
        //            "nickName": "egea36",
        //            "img": "",
        //            "score": 786
        //        }];
        //    NetProxy.Login("brandyxie", 1320, "", rankList);
        //}, 100);

        //loading layer
        var loadingLayer = new LoadingLayer();
        this.addChild(loadingLayer);

        //start loading
        loadingLayer.startLoading();

        //var name = "test_test"; //get from url
        //name = name.replace(/\n/g, '');
        //console.log("your name is: " + name);
        //storageManager.recordNickName(name);
        //MusicManager.playEffect(MusicEffectFiles.Audio_button);
    }
});