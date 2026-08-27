/**
 * Created by malloyzhu on 2016/2/2.
 */

var TouchType = {
    BEGAN: "BEGAN",
    MOVED: "MOVED",
    ENDED: "ENDED"
};

var PositionType = {
    FIXED: "FIXED",
    FOLLOW: "FOLLOW"
};

var DirectionType = {
    FOUR: "FOUR",
    EIGHT: "EIGHT",
    ALL: "ALL"
};

var DirectionValue = {
    LEFT: "LEFT",
    RIGHT: "RIGHT",
    UP: "UP",
    DOWN: "DOWN",
    LEFT_UP: "LEFT_UP",
    LEFT_DOWN: "LEFT_DOWN",
    RIGHT_UP: "RIGHT_UP",
    "RIGHT_DOWN": "RIGHT_DOWN",
    "ALL": "ALL"
};

var Rocker = cc.Node.extend({
    _bTouching: null,
    _rockerControl: null,       //控杆
    _rockerControlTouched: null,
    _rockerBg: null,     //控杆背景
    _listener: null,    //监听器
    _radius: 0,         //半径
    _angle: null,       //角度
    _radian: null,      //弧度
    _speed: 0,          //实际速度
    _positionType: null,   //位置类型
    _directionType: null,   //方向类型
    _opacity: 0,        //透明度
    _callback: null,
    _touchType: null,
    _directionValue: null,
    _increment: {},
    _defaultPosition: null,
    _bScheduleUpdate: null,
    _controlFinger: null,
    _startIndex: 0,
    _circleList: [],

    isLeftRocker: true,

    ctor: function (rockerBg, rockerControl, rockerControlTouched, radius, positionType, directionType) {
        this._super();
        this._positionType = positionType;
        this._directionType = directionType;
        this._radius = radius;
        this._bTouching = false;
        this._bScheduleUpdate = false;

        this.setAnchorPoint(0.5, 0.5);

        //创建摇杆精灵
        this._createStickSprite(rockerBg, rockerControl, rockerControlTouched, radius);

        //初始化触摸事件
        this._initTouchEvent();

        this.isLeftRocker = StorageManager.GetInstance().isLeftRocker();

    },

    setDefaultPosition: function (position) {
        this._defaultPosition = position;
    },

    setCallBack: function (fun) {
        this._callback = fun;
    },

    _createStickSprite: function (rockerBg, rockerControl, rockerControlTouched, radius) {
        //摇杆背景精灵
        this._rockerBg = new cc.Sprite();
        this._rockerBg.initWithSpriteFrameName(rockerBg);
        this._rockerBg.setPosition(radius, radius);
        this.addChild(this._rockerBg);

        //摇杆精灵
        this._rockerControl = new cc.Sprite();
        this._rockerControl.initWithSpriteFrameName(rockerControl);
        this._rockerControl.setPosition(radius, radius);
        this.addChild(this._rockerControl);

        //摇杆精灵，按下状态
        if (null != rockerControlTouched) {
            this._rockerControlTouched = new cc.Sprite();
            this._rockerControlTouched.initWithSpriteFrameName(rockerControlTouched);
            this._rockerControlTouched.setPosition(radius, radius);
            this._rockerControlTouched.setVisible(false);
            this.addChild(this._rockerControlTouched);
        }

        //根据半径设置缩放比例
        var scale = radius / (this._rockerBg.getContentSize().width / 2);
        this._rockerBg.setScale(scale);
        this._rockerControl.setScale(scale);
        this._rockerControlTouched && this._rockerControlTouched.setScale(scale);

        //设置大小
        this.setContentSize(this._rockerBg.getBoundingBox());

        //show guide notice
        var maxLen = Math.round(dataManager.maxHistoryLen);
        if (maxLen < gameConfig.notice.notice_ctrl_len) {
            //add control finger
            var sprite = new cc.Sprite();
            sprite.initWithSpriteFrameName("new_finger.png");
            sprite.setAnchorPoint(0.5, 0.5);
            sprite.setPosition(140, 10);
            this.addChild(sprite, 1);

            this._controlFinger = sprite;
        }
    },

    moveToPos: function () {
        if (this._controlFinger) {
            this._startIndex = (this._startIndex >= this._circleList.length) ? 0 : this._startIndex;

            var pos = this._circleList[this._startIndex];
            this._controlFinger.setPosition(pos);

            ++this._startIndex;
        }
    },

    notifyFinger: function () {
        if (this._controlFinger && 0 == this._controlFinger.getNumberOfRunningActions()) {
            this._controlFinger.setVisible(true);

            this._circleList.splice(0);
            var srcPos = cc.p(70, 10);
            var radius = 80;
            var num = 32;
            var angle = 2 * Math.PI * 100 / num * 0.01;
            for (var i = 0; i < num; ++i) {
                var pos = cc.p(0, 0);
                pos.x = srcPos.x + radius * Math.cos(i * angle);
                pos.y = srcPos.y + radius * Math.sin(i * angle);

                this._circleList.push(pos);
            }

            this._startIndex = 0;
            this.schedule(this.moveToPos, 0.04, 60, 0.2, "");

            var self = this;
            setTimeout(function () {
                self.removeFingerNotice();

            }, (60 * 0.04 + 0.2) * 1000);
        }
    },

    removeFingerNotice: function () {
        if (this._controlFinger) {
            this._controlFinger.stopAllActions();
            this._controlFinger.removeFromParent(true);
            this._controlFinger = null;
            console.log("removeFingerNotice");

            this._circleList.splice(0);
            this.unschedule(this.moveToPos);

            //timer
            this.scheduleOnce(this.removeNotice.bind(this), 0.5, "");
        }
    },

    removeNotice: function () {
        playerManager.showGuideNotice(2, 0);

        //timer
        this.scheduleOnce(function () {
            playerManager.hideGuideNotice();
        }, 2, "");
    },

    getControlViewPosition: function () {
        return this._rockerControl.getPosition();
    },

    _initTouchEvent: function () {
        this._listener = cc.EventListener.create({
            event: cc.EventListener.TOUCH_ONE_BY_ONE,
            swallowTouches: false,
            onTouchBegan: this._onTouchBegan.bind(this),
            onTouchMoved: this._onTouchMoved.bind(this),
            onTouchEnded: this._onTouchEnded.bind(this)
        });
    },

    //计算角度并返回
    _getAngle: function (point) {
        var pos = this._rockerBg.getPosition();
        this._angle = Math.atan2(point.y - pos.y, point.x - pos.x) * (180 / cc.PI);

        return this._angle;
    },

    //计算弧度并返回
    _getRadian: function (point) {
        this._radian = cc.PI / 180 * this._getAngle(point);
        return this._radian;
    },

    //计算两点间的距离并返回
    _getDistanceSquare: function (pos1, pos2) {
        return Math.pow(pos1.x - pos2.x, 2) +
            Math.pow(pos1.y - pos2.y, 2);
    },

    _onTouchBegan: function (touch, event) {
        //if (this._bTouching) {
        //    return false;
        //}
        //cc.log("_onTouchBegan");
        this._bTouching = true;
        this._touchType = TouchType.BEGAN;

        //触摸监听目标
        //var target = event.getCurrentTarget();
        var location = touch.getLocation();
        //cc.log("location x:" + location.x + ", y:" + location.y);
        if (this.isLeftRocker && location.x > (cc.winSize.width / 2)) {
            this._bTouching = false;
            this._touchType = null;
            return false;
            //} else if (!this.isLeftRocker && location.x < (cc.winSize.width / 2)) {
            //    return false;
        }

        //把触摸点坐标转换为相对与目标的模型坐标
        var touchPos = this.convertToNodeSpace(location);
        //更新角度
        this._getAngle(touchPos);

        if (this._positionType == PositionType.FOLLOW) {
            if (null != this._rockerControlTouched) {
                this._rockerControl.setVisible(false);
                this._rockerControlTouched.setVisible(true);
            }
            this.setPosition(location);
            this.setVisible(true);

            return true;
            //} else {
            //    //点与圆心的距离
            //    var distanceSquare = this._getDistanceSquare(touchPos, target);
            //
            //    //圆的半径
            //    var radius = target.getBoundingBox().width / 2;
            //
            //    //如果点与圆心距离小于圆的半径,返回true
            //    if (radius * radius > distanceSquare) {
            //        if (null != this._rockerControlTouched) {
            //            this._rockerControl.setVisible(false);
            //            this._rockerControlTouched.setVisible(true);
            //        }
            //        this._rockerControl.setPosition(touchPos);
            //        this._rockerControlTouched && this._rockerControlTouched.setPosition(touchPos);
            //        this.scheduleUpdate();
            //        this._updateDirectionsMove();
            //        return true;
            //    }
        }
        return false;
    },

    _onTouchMoved: function (touch, event) {
        //cc.log("_onTouchMoved");
        this._touchType = TouchType.MOVED;

        //触摸监听目标
        var target = event.getCurrentTarget();

        //把触摸点坐标转换为相对与目标的模型坐标
        var touchPos = this.convertToNodeSpace(touch.getLocation());

        //点与圆心的距离
        var distanceSquare = this._getDistanceSquare(touchPos, target);

        //圆的半径
        var radius = target.getBoundingBox().width / 2;

        //如果点与圆心距离小于圆的半径,控杆跟随触摸点
        if (radius * radius > distanceSquare) {
            this._rockerControl.setPosition(touchPos);
            this._rockerControlTouched && this._rockerControlTouched.setPosition(touchPos);
        }
        else {
            var radian = this._getRadian(touchPos);
            var xLimit = Math.cos(radian) * this._radius;
            var yLimit = Math.sin(radian) * this._radius;
            var x = target.getPositionX() + xLimit;
            var y = target.getPositionY() + yLimit;
            this._rockerControl.setPosition(x, y);
            this._rockerControlTouched && this._rockerControlTouched.setPosition(x, y);

            //if (this._positionType == PositionType.FOLLOW) {
            //    var length = cc.pDistance(target.getPosition(), touchPos);
            //    var xLength = Math.cos(radian) * length;
            //    var yLength = Math.sin(radian) * length;
            //    var xDiff = xLength - xLimit;
            //    var yDiff = yLength - yLimit;
            //    this.setPosition(this.getPositionX() + xDiff, this.getPositionY() + yDiff);
            //}
        }

        //更新角度
        this._getAngle(touchPos);

        if (this._positionType == PositionType.FOLLOW) {
            this.scheduleUpdate();
        }
    },

    _onTouchEnded: function (touch, event) {
        //cc.log("_onTouchEnded");
        this._bTouching = false;
        this._touchType = TouchType.ENDED;
        this.setVisible(true);
        if (null != this._rockerControlTouched) {
            this._rockerControl.setVisible(true);
            this._rockerControlTouched.setVisible(false);
        }

        //触摸监听目标
        var target = event.getCurrentTarget();
        //如果触摸类型为FOLLOW，离开触摸后隐藏
        //this.setVisible(!(this._positionType == PositionType.FOLLOW));

        //摇杆恢复位置
        var distance = Math.sqrt(this._getDistanceSquare(target.getPosition(), this._rockerControl.getPosition()));
        var moveAction = new cc.MoveTo(distance / 500, target.getPosition());
        var action = new cc.EaseElasticOut(moveAction, 0.6);
        this._rockerControl.stopAllActions();
        this._rockerControl.runAction(action);

        if (null != this._rockerControlTouched) {
            this._rockerControlTouched.stopAllActions();
            this._rockerControlTouched.runAction(action.clone());
        }

        this.setPosition(this._defaultPosition);
        this._updateDirectionsMove();
        this.unscheduleUpdate();

        //remove finger
        this.removeFingerNotice();
        //console.log("main loop: cost time: " + (Date.now() - this.timeCost));
    },

    scheduleUpdate: function () {
        if (!this._bScheduleUpdate) {
            this._super();
            this._bScheduleUpdate = true;
        }
    },

    unscheduleUpdate: function () {
        if (this._bScheduleUpdate) {
            this._super();
            this._bScheduleUpdate = false;
        }
    },

    //更新移动目标
    update: function (dt) {
        this._updateDirectionsMove();
    },

    _updateDirectionsMove: function () {
        switch (this._directionType) {
            case DirectionType.FOUR:
                this._fourDirectionsMove();
                break;
            case DirectionType.EIGHT:
                this._eightDirectionsMove();
                break;
            case DirectionType.ALL:
                this._allDirectionsMove();
                break;
            default :
                break;
        }
    },

    _updateCallBack: function () {
        if (typeof this._callback === 'function') {
            this._callback(this);
        }
    },

    getDirectionValue: function () {
        return this._directionValue;
    },

    getDirectionType: function () {
        return this._directionType;
    },

    getTouchType: function () {
        return this._touchType;
    },

    getIncrement: function () {
        return this._increment;
    },

    //四个方向移动(上下左右)
    _fourDirectionsMove: function () {
        var incrementX = 0;
        var incrementY = 0;
        if (this._angle > 45 && this._angle < 135) {
            this._directionValue = DirectionValue.UP;
            incrementY = this._speed;
        } else if (this._angle > -135 && this._angle < -45) {
            this._directionValue = DirectionValue.DOWN;
            incrementY = -this._speed;
        } else if (this._angle < -135 && this._angle > -180 || this._angle > 135 && this._angle < 180) {
            this._directionValue = DirectionValue.LEFT;
            incrementX = -this._speed;
        } else if (this._angle < 0 && this._angle > -45 || this._angle > 0 && this._angle < 45) {
            this._directionValue = DirectionValue.RIGHT;
            incrementX = this._speed;
        }
        this._increment = {x: incrementX, y: incrementY};
        this._updateCallBack();
    },

    //八个方向移动(上下左右、左上、右上、左下、右下)
    _eightDirectionsMove: function () {
        var incrementX = 0;
        var incrementY = 0;
        if (this._angle > 67.5 && this._angle < 112.5) {
            this._directionValue = DirectionValue.UP;
            incrementY = this._speed;
        } else if (this._angle > -112.5 && this._angle < -67.5) {
            this._directionValue = DirectionValue.DOWN;
            incrementY = -this._speed;
        } else if (this._angle < -157.5 && this._angle > -180 || this._angle > 157.5 && this._angle < 180) {
            this._directionValue = DirectionValue.LEFT;
            incrementX = -this._speed;
        } else if (this._angle < 0 && this._angle > -22.5 || this._angle > 0 && this._angle < 22.5) {
            this._directionValue = DirectionValue.RIGHT;
            incrementX = this._speed;
        } else if (this._angle > 112.5 && this._angle < 157.5) {
            this._directionValue = DirectionValue.LEFT_UP;
            incrementX = -this._speed / 1.414;
            incrementY = this._speed / 1.414;
        } else if (this._angle > 22.5 && this._angle < 67.5) {
            this._directionValue = DirectionValue.RIGHT_DOWN;
            incrementX = this._speed / 1.414;
            incrementY = this._speed / 1.414;
        } else if (this._angle > -157.5 && this._angle < -112.5) {
            this._directionValue = DirectionValue.LEFT_DOWN;
            incrementX = -this._speed / 1.414;
            incrementY = -this._speed / 1.414;
        } else if (this._angle > -67.5 && this._angle < -22.5) {
            this._directionValue = DirectionValue.RIGHT_DOWN;
            incrementX = this._speed / 1.414;
            incrementY = -this._speed / 1.414;
        }
        this._increment = {x: incrementX, y: incrementY};
        this._updateCallBack();
    },

    //全方向移动
    _allDirectionsMove: function () {
        var incrementX = Math.cos(this._angle * (Math.PI / 180)) * this._speed;
        var incrementY = Math.sin(this._angle * (Math.PI / 180)) * this._speed;
        this._directionValue = DirectionValue.ALL;
        this._increment = {x: incrementX, y: incrementY};
        this._updateCallBack();
    },

    //设置透明度
    setOpacity: function (opacity) {
        this._super(opacity);
        this._rockerControl.setOpacity(opacity);
        this._rockerControlTouched && this._rockerControlTouched.setOpacity(opacity);
        this._rockerBg.setOpacity(opacity);
    },

    setSpeed: function (speed) {
        this._speed = speed;
    },

    //设置遥控杆开关
    setEnable: function (enable) {
        if (this._listener != null) {
            if (enable) {
                cc.eventManager.addListener(this._listener, this._rockerBg);
            } else {
                cc.eventManager.removeListener(this._listener);
            }
        }
    },

    //获取角度
    getAngle: function () {
        return this._angle;
    },

    onExit: function () {
        this._super();

        //移除触摸监听
        if (this._listener != null) {
            cc.log("disable roker");
            cc.eventManager.removeListener(this._listener);
        }
    }
});
