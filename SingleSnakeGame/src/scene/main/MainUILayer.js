/**
 * Created by malloyzhu on 2016/4/26.
 */

var MainUILayer = cc.Layer.extend({
    isStartedTimeEffect: false,
    _accButton: null,
    _rootNode: null,
    _listenerList: null,
    _killPanel: null,

    _playerName: null,
    _playerScore: 0,
    _playerIcon: null,
    _bShowMyScore: false,
    _nPreTime: 0,
    _nCurrIndex: -1,
    _bTimeLabel: false,
    _duration: 3.2,
    _bNoticed: false,
    _numList: [],

    isPlayingAnnounceEffect: false,

    ctor: function () {
        this._super();
        cc.log("new MainUILayer");

        this._listenerList = [];

        this._initView();

        MusicManager.playMusic(MusicEffectFiles.Audio_bgm, true);
    },

    _initView: function () {
        var rootNode = UIHelper.bindUIWidget(this, res.MainUILayer_json);
        UIHelper.adjustUILayout(rootNode);
        this._rootNode = rootNode;

        var miniMap = new MiniMap(mapSize);
        miniMap.setPosition(this._radarPositionPanel.getPosition());
        this.addChild(miniMap);
        this._radarPositionPanel.setVisible(false);

        var positionType = PositionType.FOLLOW;
        var rocker = new Rocker("controlBkg.png", "btn_control_N.png", "btn_control_S.png", 90, positionType, DirectionType.FOUR);
        rocker.setSpeed(5);
        rocker.setEnable(true);
        rocker.setCallBack(this._onRockerUpdate.bind(this));
        rocker.setPosition(this._rockerPositionPanel.getWorldPosition());
        rocker.setDefaultPosition(this._rockerPositionPanel.getWorldPosition());

        this.addChild(rocker);
        this._rockerPositionPanel.setVisible(false);
        this._timeLabel.setVisible(false);

        this.addChild(rootNode);

        //need hide accelerate button or not
        this._accButton = ccui.helper.seekWidgetByName(rootNode, "_accelerateButton");
        this._accButton.setVisible(true);

        //length
        var maxLen = Math.round(dataManager.maxHistoryLen);
        this._selfRankText.setString("历史最长：" + maxLen);

        //show guide notice
        if (maxLen < gameConfig.notice.notice_ctrl_len) {
            setTimeout(function () {
                var index = 1;
                playerManager.showGuideNotice(index, 0);
                rocker.notifyFinger();

            }, 500);
        } else {
            console.log("don't need show guide");
        }

        //rank list information
        var parentPanel = this._text_exceed;
        var posY = 0;
        var sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName("name_bg.png");
        sprite.setAnchorPoint(1, 0.5);
        sprite.setScaleY(4);
        sprite.setPosition(208, posY - 40);
        parentPanel.addChild(sprite, 0);
        //player name
        var pos = sprite.getPosition();
        var name = new cc.LabelTTF("", "Arial", 24, cc.size(160, 30));
        name.setAnchorPoint(0.5, 0.5);
        name.setPosition(pos.x - 156, pos.y + 15);
        name.setHorizontalAlignment(cc.TEXT_ALIGNMENT_LEFT);
        parentPanel.addChild(name, 1);
        this._playerName = name;
        //player score
        var score = new cc.LabelTTF("", "Arial", 28, cc.size(160, 40));
        score.setAnchorPoint(0.5, 0.5);
        score.setPosition(pos.x - 156, pos.y - 22);
        score.setHorizontalAlignment(cc.TEXT_ALIGNMENT_LEFT);
        parentPanel.addChild(score, 1);
        this._playerScore = score;

        //create kill notice panel
        var layer = new cc.Layer();
        layer.setAnchorPoint(0.5, 0.5);
        layer.setContentSize(480, 80);
        this.addChild(layer, 0);
        //back image
        var bkg = new cc.Sprite();
        bkg.initWithSpriteFrameName("cy_bg.png");
        bkg.setAnchorPoint(1, 0.5);
        bkg.setPosition(240, 40);
        layer.addChild(bkg);
        var sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName("mul_kill.png");
        sprite.setPosition(310, 46);
        bkg.addChild(sprite, 1, 100);
        this._killPanel = layer;
        this._killPanel.setVisible(false);

        //start schedule
        this.scheduleUpdate();

        //initialise rank
        var rankList = LOGIN_REQUEST_DATA.RANK_LIST;
        if (rankList) {
            this.freshRankPanel(0);
        } else {
            console.log("null == rankList!");
        }
    },

    _onRockerUpdate: function (rocker) {
        snakeMoveController.onOperatorRocker(rocker);
    },

    onEnter: function () {
        this._super();

        Util.registerListener(this._listenerList, CEventType.UPDATE_GLOBAL_INFO, this.refreshMyInfo.bind(this));
        Util.registerListener(this._listenerList, CEventType.ON_ACC_BTN_NOTICE, this.playAccBtnAnimation.bind(this));
        Util.registerListener(this._listenerList, CEventType.EXCEED_FRIEND_NOTICE, this.playExceedAnimation.bind(this));
        Util.registerListener(this._listenerList, CEventType.RESIZE_WINDOW, this._onWindowSizeReset.bind(this));
        Util.registerListener(this._listenerList, CEventType.ON_START_ACCELERATE, this._onStartAccelerate.bind(this));
        Util.registerListener(this._listenerList, CEventType.ON_END_ACCELERATE, this._onEndAccelerate.bind(this));
        Util.registerListener(this._listenerList, CEventType.TIME_OVER, this._onGameOver.bind(this));
        snakeMoveController._focusGameCanvas();
    },

    _onStartAccelerate: function () {
        this._startAccelerate();
    },

    _onEndAccelerate: function () {
        this._endAccelerate();
    },

    _onWindowSizeReset: function () {
        UIHelper.adjustUILayout(this._rootNode);
    },

    onExit: function () {
        this._super();

        Util.unRegisterListeners(this._listenerList);
        snakeMoveController.reset();

        MusicManager.stopAllEffects();
        MusicManager.stopMusic(true);

        this._bShowMyScore = false;
        this._bNoticed = false;
    },

    refreshMyInfo: function () {
        var length = NetDataBuf.globalInfo.snakeSelf ? MathUtil.toDecimal(NetDataBuf.globalInfo.snakeSelf.energy) : 0;
        length = Math.round(length);
        this._selfLengthText.setString("长度：" + length);

        if (this._bShowMyScore) {
            var parentPanel = this._text_exceed;
            parentPanel.setVisible(false);
        }

        //only update per 800
        var currTime = Date.now();
        var change = currTime - this._nPreTime;
        if (change > 950) {
            this._nPreTime = currTime;
            this.updateTime(NetDataBuf.leftTime);

            //exceed
            var index = -1;
            var stageLen;
            var configList = gameConfig.exceed;
            var len = configList.length;
            var maxLen = configList[len - 1];
            if (length > maxLen) {
                index = len - 1;
                stageLen = maxLen;
            } else {
                for (var i = 0; i < len - 1; ++i) {
                    stageLen = configList[i];
                    if (length > stageLen && length < configList[i + 1]) {
                        index = i;
                        break;
                    }
                }
            }
            if (-1 != index && index > this._nCurrIndex) {
                this._nCurrIndex = index;
                console.log("index= " + index);

                this.playExceedNotice(stageLen);
            }
        }
    },

    freshRankPanel: function (index) {
        var name;
        var score;
        //var imgUrl;
        var rankList = LOGIN_REQUEST_DATA.RANK_LIST;
        if (index < 0 || index >= rankList.length) {
            //i am the number one
            this._bShowMyScore = true;
            return;
        }
        var data = rankList[index];
        name = data.nickName;
        score = data.score;
        //imgUrl = data.img;
        name = UIHelper.clipLongTextLabel(this._playerName, name, 24, 140, 10);
        this._playerName.setString(name);
        this._playerScore.setString(score);
        //update icon
        if (null == this._playerIcon) {
            var random = Math.round(Math.random() * 100) % 4 + 1;
            var sprite = new cc.Sprite();
            sprite.initWithSpriteFrameName("head_" + random + ".png");
            sprite.setAnchorPoint(0, 0);
            sprite.setPosition(126, -66);
            var parentPanel = this._text_exceed;
            parentPanel.addChild(sprite, 1);
            this._playerIcon = sprite;
        }
        //only for test
        //var texture = "\/9j\/4AAQSkZJRgABAQEAYABgAAD\/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT\/2wBDAQMEBAUEBQkFBQkUDQsNFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBT\/wAARCAAoACgDASIAAhEBAxEB\/8QAGgAAAgMBAQAAAAAAAAAAAAAAAAcEBggJBf\/EADEQAAEDAgUCBQMCBwAAAAAAAAECAwQFEQAGBxIhEzEIIkFRYRQjkRUyM0JSYnGBgv\/EABgBAQEBAQEAAAAAAAAAAAAAAAMFAgEG\/8QAKBEAAQMDAgUEAwAAAAAAAAAAAQACAwQREgUhIjFBYXEGUYGxkaHx\/9oADAMBAAIRAxEAPwDLGlOumbsr6dOZcg16fCiMNK+lYZfUgJK3dytpB4B3qJ\/PfFSokbJE\/P8AIrOo1dlmCAZD9Mp7ZVJnu\/0hweVAPcqJBPPvfHgU9mNHisqiS7lohCupYKVxe\/cW9eL4eWhfhbzDrzRZUynookCIy5tk1SrBNmyrlKEg3ubEH\/oc4JuTz2CXAWs0blQ4+vemFOUmNlrSLKjEQHeDU+pJm8WsnrvKPPuQebmwGOkWneksPVTw60CNnPL0KNNqkQTV05psJRFKlFTO21ilSUFAuOb398YE1J8NNGyLm+l0uov0WupcX0DMpDaYyA8FBRS42ni9hbyq9TxewxdKf4uc5V\/MRynFpgqdVlOmJGpMBbkRiMEgeYrQsOXG1ZUSoAAEnjgEWAybtuUMweG43smNpP4RsvQc5S5VUgvVPMEIdb6QJUERwu6kFSR\/EWACNyh\/q9jgxqHRtNE0syjDpFSrDFSrZcMqq1Fl3qtfUuG9iVErG0WSndyUpB9xgwZoC85ZlGH2FgVw\/wAtQ3666zSqdAfqU6UfIzHAPHub8JA9VEgDHQHwkZPfyVlCRTc2sPPsuzg6mI6NgjutoQlwLsbrTZKSCLgi455ukMiJoWVqNGREqU55mOVWaYiCOlvcrcOooncq3v2\/wcWrPmu8qblQxUx4zkwja1LC3Q4ALcjzD3Hfjjti5Dp8tSRHC7i59luOrbC7Jzdk5tTMy\/rUxbD9Fh0gS6myiPVPpClCgT5NxX9wq33WQUjg2tzha+H3QWo6Jaxu51zb0atlKGh5BmJIaWouIUkudK5UkJN7377gfjFBrUjM1PotD1CzKKtLhhndS0T3y4y4\/wApb2m9rA3+QATYWwtKhmGdnSpRqVUqrKltuFUyetb6h11qPYi\/7b+n9oxvT9Okq3kZWINvJ9vjr\/ElfO3YgbEfr3W3si5XrmsGcptXpClRqdJDal1J1CSlO26fJwN52cXtxzgwgvDBqC9pBrrRodDaWnL1fW1TqxGQv7SUuOpbakEHgFLi08gftUocXwY5XUx02c08m5HUclOiBmbk3YJM07PtcrG5lhTkkbC30kRiqwPf0Px+MT5UKssSqeursuoS5ZptDqgSrtxbuOQn84MGKGkyOFdGfP0VuUZMIPb7VVrKl\/rqm3HnlMwkmzbi1FDJJuUgHhPyBbtidpzlaZNqVNnqYuzUp\/RQhtRLgsk2Tt+eO3scGDFhkzm6mywG7iljp2Pppi6\/C3b8p3ztGavk3OuUKzmWjVKh0xdUZ3PymlR\/tg7ilO4Cxsnjj+UYMGDHlPUlZJPWZkAbdPPylpYGsjtzX\/\/Z";
        //use base64 image
        //var head = "data:image/png;base64, ";
        //var imgUrl = null;
        //var self = this;
        ////upload data to page
        //window.getUserheaderPic(data.openid, function (texture) {
        //    if (texture && texture.length > 0) {
        //        imgUrl = head + dataManager.clearString(texture);
        //        self._onTexResponsed(imgUrl);
        //    } else {
        //        console.log("window.getUserheaderPic: null===texture!");
        //    }
        //});
    },

    _onTexResponsed: function (imgUrl) {
        var self = this;
        cc.loader.loadImg(imgUrl, {isCrossOrigin: false}, function (err, texture) {
            if (null == texture) {
                return;
            }
            if (self._playerIcon) {
                self._playerIcon.removeFromParent(true);
                self._playerIcon = null;
            }
            var width = texture.width;
            var height = texture.height;
            var texture2d = new cc.Texture2D();
            texture2d.initWithElement(texture);
            texture2d.handleLoadedTexture();

            var sprite = new cc.Sprite(texture2d);
            sprite.setAnchorPoint(0.5, 0.5);
            sprite.setPosition(154, -40);
            sprite.setScaleX(64 / width);
            sprite.setScaleY(64 / height);

            //add child
            var parentPanel = self._text_exceed;
            parentPanel.addChild(sprite, 1);
            self._playerIcon = sprite;
        });
    },

    _onAccelerateButtonTouched: function (sender, type) {
        switch (type) {
            case ccui.Widget.TOUCH_BEGAN:
            {
                //var self = this;
                //setTimeout(function () {
                //    self._startAccelerate();
                //}, 10);
                this._startAccelerate();

                //stop timer
                if (ALREADY_SHOW_ACC) {
                    this.unschedule(this._setAccBtnNotice);
                    Util.unRegisterListener(this._listenerList, CEventType.ON_ACC_BTN_NOTICE);
                    playerManager.removeCanAccNotice();
                }
            }
                break;
            case ccui.Widget.TOUCH_MOVED:
                break;
            case ccui.Widget.TOUCH_ENDED:
            case ccui.Widget.TOUCH_CANCELED:
            {
                this._endAccelerate();
            }
                break;
        }
    },

    playExceedAnimation: function (event) {
        var rankList = LOGIN_REQUEST_DATA.RANK_LIST;
        if (rankList && rankList.length > 0) {
            var length = rankList.length;
            var index = event.data;
            if (index < 0 || index >= length) {
                console.log("playExceedAnimation: error index");
                return;
            }
            MusicManager.playEffect(MusicEffectFiles.Audio_exceed);

            //update rank panel data
            this.freshRankPanel(index + 1);

            var data = LOGIN_REQUEST_DATA.RANK_LIST[index];
            var name = data.nickName;
            if (data.nickName == LOGIN_REQUEST_DATA.USER_NAME) {
                name = "自己的最长纪录！";
            }
            //console.log("data.nickName= " + data.nickName);
            //console.log("data.img= " + data.img);
            //console.log("data.score= " + data.score);
            //show notice
            var panel = this._Sprite_Bkg;
            if (0 != panel.getNumberOfRunningActions()) {
                panel.stopAllActions();
            }
            panel.setOpacity(255);
            panel.setVisible(true);

            var time = this._duration;
            panel.runAction(cc.fadeOut(time));
            this._Text_Name.setString(name);
            //hide
            setTimeout(function () {
                panel.setVisible(false);
            }, (time - 0.5) * 1000);
        }
    },

    playAccBtnAnimation: function () {
        console.log("playAccBtnAnimation");

        //add animation
        var sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName("taotaobottom.png");
        sprite.setAnchorPoint(0.5, 0.5);
        sprite.setPosition(75, 75);

        var top = new cc.Sprite();
        top.initWithSpriteFrameName("new_alpha_ball.png");
        top.setAnchorPoint(0.5, 0.5);
        top.setPosition(92, 92);
        sprite.addChild(top, 1);
        this._accButton.addChild(sprite, 1);

        //run
        var duration = this._duration;
        sprite.runAction(cc.blink(duration, 4));
        //timer
        setTimeout(function () {
            if (sprite) {
                sprite.stopAllActions();
                sprite.removeFromParent(true);
            }

            //show guide notice
            var maxLen = Math.round(dataManager.maxHistoryLen);
            if (maxLen < gameConfig.notice.notice_ctrl_len) {
                playerManager.showGuideNotice(4, 0);
            }
            setTimeout(function () {
                playerManager.hideGuideNotice();

            }, 2 * 1000);

        }, (duration + 0.5) * 1000);

        //notice again
        if (!this._bNoticed) {
            var delay = gameConfig.notice.notice_acc_time;
            this.scheduleOnce(this._setAccBtnNotice, delay, "");
            this._bNoticed = true;
        }
    },

    _setAccBtnNotice: function () {
        var time = 4;
        playerManager.notifyCanAcc(time);
        this.playAccBtnAnimation();

        //stop timer
        this.unschedule(this._setAccBtnNotice);
        Util.unRegisterListener(this._listenerList, CEventType.ON_ACC_BTN_NOTICE);
    },

    _startAccelerate: function () {
        var mainPlayer = playerManager.getMainPlayer();
        mainPlayer && mainPlayer.onAccelerateStart();
    },

    _endAccelerate: function () {
        var status = 2; //1: 开始加速，2:停止加速
        NetProxy.ChangeSnakeSpeed(status);
        var mainPlayer = playerManager.getMainPlayer();
        mainPlayer && mainPlayer.onAccelerateEnd();
    },

    _onGameOver: function () {
        this.updateTime(0);
    },

    updateTime: function (time) {
        var leftTime = Math.ceil(time * 0.001);
        this._timeLabel.setVisible(true);
        this._timeLabel.setString(Util.formatTime(leftTime, TimeFormatType.ms));

        if (leftTime <= 10 && leftTime > 0) {
            if (!this.isStartedTimeEffect) {
                this.isStartedTimeEffect = true;
                this.playTimeEffect(this._timeLabel);

                MusicManager.playEffect(MusicEffectFiles.Audio_countdown, null, true);
            }
        } else if (leftTime <= 30 && leftTime > 10) {
            this._bTimeLabel = !this._bTimeLabel;
            if (this._bTimeLabel) {
                this._timeLabel.setColor(cc.color(0xFF, 0x72, 0x72));
            } else {
                this._timeLabel.setColor(cc.color(0xFF, 0xFF, 0xFF));
            }
        } else if (leftTime <= 0) {
            this._timeLabel.stopAllActions();
            this._timeLabel.setScale(1.0);
            this._timeLabel.setVisible(false);

            MusicManager.stopAllEffects();
            this.playTimeNotice(3);
            return;
        }

        //change stage config
        switch (leftTime) {
            case 60: //60
            {
                netManager.setServerConfig(2);
                this.playTimeNotice(1);
            }
                break;
            case 30: //30
            {
                netManager.setServerConfig(3);
                this.playTimeNotice(2);
            }
                break;
            case 10: //10
            {
                netManager.setServerConfig(4);
            }
                break;
        }

        //only for test
        //if (1 == leftTime % 4) {
        //    this.playAnnounceEffect(PDataDef.RD.Board_Type_Enum.multi_kill, leftTime % 10 + 10);
        //}
    },

    playTimeEffect: function (timeLabel) {
        timeLabel.setColor(cc.color(0xFF, 0x72, 0x72));
        //cc.log("playTimeEffect");
        var callback = function (target) {
            target.setScale(1.2)
        };
        timeLabel.setScale(1.2);
        var action = cc.repeatForever(cc.sequence(cc.scaleTo(0.5, 1.5), cc.delayTime(0.5), cc.callFunc(callback)));
        timeLabel.runAction(action);
    },

    playTimeNotice: function (stage) {
        var panel = this._Sprite_Time;
        panel.setAnchorPoint(0.5, 0.5);
        panel.setVisible(true);
        panel.setOpacity(255);
        panel.removeAllChildren(true);
        var height = 50;
        var text = new cc.Sprite();
        text.setAnchorPoint(0.5, 0.5);
        switch (stage) {
            case 1: //60
            {
                var num1 = new cc.Sprite();
                num1.initWithSpriteFrameName("6.png");
                num1.setPosition(150, height);
                panel.addChild(num1, 1);
                var num2 = new cc.Sprite();
                num2.setPosition(190, height);
                num2.initWithSpriteFrameName("0.png");
                panel.addChild(num2, 1);

                text.initWithSpriteFrameName("count_time.png");
                text.setPosition(290, height);
                panel.addChild(text, 1);
            }
                break;
            case 2: //30
            {
                var num1 = new cc.Sprite();
                num1.initWithSpriteFrameName("30m.png");
                num1.setPosition(170, height);
                panel.addChild(num1, 1);

                text.initWithSpriteFrameName("count_time.png");
                text.setPosition(290, height);
                panel.addChild(text, 1);
            }
                break;
            case 3: //game over
            {
                text.initWithSpriteFrameName("game_over.png");
                text.setPosition(238, height);
                panel.addChild(text, 1);
            }
                break;
            default :
                break;
        }
        //animation
        var duration = this._duration;
        panel.runAction(cc.fadeOut(duration));

        this.scheduleOnce(function () {
            panel.stopAllActions();
            panel.setVisible(false);

        }, duration - 0.5, "");
    },

    playExceedNotice: function (length) {
        MusicManager.playEffect(MusicEffectFiles.Audio_length);

        var panel = this._Sprite_Exceed;
        panel.setAnchorPoint(0.5, 0.5);
        panel.setVisible(true);
        panel.setOpacity(255);
        panel.removeAllChildren(true);
        var height = 50;
        var text = new cc.Sprite();
        text.setAnchorPoint(0.5, 0.5);
        text.initWithSpriteFrameName("exceed.png");
        text.setPosition(140, height);
        panel.addChild(text, 1);

        var qian = Math.floor(length / 1000);
        var bai = Math.floor((length - qian * 1000) / 100);
        var offset = 0;
        var posX = 220;
        var res;
        //qian pic
        if (0 < qian) {
            var sprite = new cc.Sprite();
            res = "" + qian + ".png"
            sprite.initWithSpriteFrameName(res);
            sprite.setPosition(posX, height);
            panel.addChild(sprite, 1);
            offset = 36;
        }
        //bai pic
        posX += offset;
        var sprite = new cc.Sprite();
        res = "" + bai + ".png"
        sprite.initWithSpriteFrameName(res);
        sprite.setPosition(posX, height);
        panel.addChild(sprite, 1);
        //0 pic
        posX += 36;
        sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName("0.png");
        sprite.setPosition(posX, height);
        panel.addChild(sprite, 1);
        //0 pic
        posX += 36;
        sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName("0.png");
        sprite.setPosition(posX, height);
        panel.addChild(sprite, 1);
        //! pic
        posX += 36;
        sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName("aa.png");
        sprite.setPosition(posX, height);
        panel.addChild(sprite, 1);

        //animation
        var duration = this._duration;
        panel.runAction(cc.fadeOut(duration));

        this.scheduleOnce(function () {
            panel.stopAllActions();
            panel.setVisible(false);

        }, duration - 0.5, "");

    },

    playAnnounceEffect: function (board_type, killCount) {
        this.isPlayingAnnounceEffect = true;

        //if (PDataDef.RD.Board_Type_Enum.kill_top_three == board_type) {
        //    console.log("kill_top_three");
        //}
        // 连续多杀
        if (PDataDef.RD.Board_Type_Enum.multi_kill == board_type) {
            if (killCount < 2) {
                console.log("killCount < 2");
                return;
            }
            MusicManager.playEffect(MusicEffectFiles.Audio_combo);

            //play animation
            var pos = cc.p(-200, 480);
            this._killPanel.setVisible(true);
            this._killPanel.setOpacity(300);
            this._killPanel.setPosition(pos);
            //stop action
            this._killPanel.stopAllActions();
            this._killPanel.removeChildByTag(100);
            this._killPanel.removeChildByTag(101);

            //add number
            var count = killCount;
            var shi = Math.floor(count / 10);
            var ge = count % 10;
            var picRes;
            var sprite = new cc.Sprite();
            picRes = "" + ge + ".png";
            sprite.initWithSpriteFrameName(picRes);
            sprite.setPosition(-8, 62);
            this._killPanel.addChild(sprite, 0, 100);

            if (shi > 0) { //十位
                picRes = "" + shi + ".png"
                sprite = new cc.Sprite();
                sprite.initWithSpriteFrameName(picRes);
                sprite.setPosition(-44, 62);
                this._killPanel.addChild(sprite, 0, 101);
            }
            var targetPosition = cc.p(100, 480);
            var action = this._createAction(targetPosition);
            this._killPanel.runAction(action);
        }
    },

    _createAction: function (targetPosition) {
        var duration = 0.65;
        var moveAction = cc.moveTo(duration, targetPosition);
        var callback = new cc.CallFunc(this._onMoveActionComplete, this);
        var action = new cc.Sequence(moveAction, cc.delayTime(1.4), callback);
        return action;
    },

    _onMoveActionComplete: function () {
        this._killPanel.setVisible(false);

        this.isPlayingAnnounceEffect = false;
    },

    update: function (dt) {
        snakeMoveController._tickKeyboardSteer();

        if (!this.isPlayingAnnounceEffect) {

            var msg = PDataParser.boardMsgQueue.dequeue();
            if (msg && LOGIN_REQUEST_DATA.USER_NAME == msg.killerName) {

                this.playAnnounceEffect(msg.boardType, msg.killCount);
            }
        }
    }
});
