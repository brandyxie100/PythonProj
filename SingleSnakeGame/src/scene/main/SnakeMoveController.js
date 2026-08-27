/**
 * Created by malloyzhu on 2016/5/18.
 */

var SnakeMoveController = cc.Class.extend({
    //_bCanMoveSnake: null,
    _viewportOffsetPosition: null,
    _event: null,

    ctor: function () {
        //this._bCanMoveSnake = true;
        this._event = new CEvent();
    },

    onOperatorRocker: function (rocker) {
        //if (!bUseRocker) {
        //    return;
        //}
        var touchType = rocker.getTouchType();
        if (touchType == TouchType.MOVED) {
            //if (this._bCanMoveSnake) {
            //this._bCanMoveSnake = false;
            //this._scheduleUpdate();
            this._moveSnakeByRocker(rocker);
            //}
        }
    },

    _moveSnakeByRocker: function (rocker) {
        var contentSize = rocker.getContentSize();
        var position = rocker.getControlViewPosition();
        var targetPosition = cc.p(position.x - contentSize.width / 2, position.y - contentSize.height / 2);
        if (0 == parseInt(targetPosition.x) && 0 == parseInt(targetPosition.y)) {
            Logger.debug("zero point");
            return;
        }

        //var xInViewPort = position.x * cc.winSize.width / contentSize.width;
        //var yInViewPort = position.y * cc.winSize.height / contentSize.height;
        //var eyePoint = cc.p(xInViewPort - cc.winSize.width / 2, yInViewPort - cc.winSize.height / 2);
        NetProxy.MoveSnake(targetPosition);
        //playerManager.moveSnakeEyes(eyePoint);
    },

    //onMouseDown: function (event) {
    //    this._event.type = CEventType.ON_START_ACCELERATE;
    //    CEventManager.dispatchEvent(this._event);
    //},
    //
    //onMouseMove: function (event) {
    //    if (bUseRocker) {
    //        return;
    //    }
    //
    //    if (this._bCanMoveSnake) {
    //        this._bCanMoveSnake = false;
    //
    //        this._scheduleUpdate();
    //        this._moveSnakeByTouch(event);
    //    }
    //},
    //
    //onMouseUp: function (event) {
    //    this._event.type = CEventType.ON_END_ACCELERATE;
    //    CEventManager.dispatchEvent(this._event);
    //},

    //_scheduleUpdate: function () {
    //    cc.director.getScheduler().schedule(this._onReachTime, this, 0.05);
    //},
    //
    //_unScheduleUpdate: function () {
    //    cc.director.getScheduler().unschedule(this._onReachTime, this);
    //},
    //
    //_onReachTime: function () {
    //    this._unScheduleUpdate();
    //    this._bCanMoveSnake = true;
    //},

    _moveSnakeByTouch: function (touch) {
        var touchPos = touch.getLocation();
        var target = cc.p(touchPos.x - cc.winSize.width / 2, touchPos.y - cc.winSize.height / 2);
        NetProxy.MoveSnake(target);

        //playerManager.moveSnakeEyes(touchPos);
    },

    reset: function () {
        //this._unScheduleUpdate();
        //this._bCanMoveSnake = true;
        this._viewportOffsetPosition = null;
    },

    setViewPortOffset: function (offsetPosition) {
        this._viewportOffsetPosition = offsetPosition;
    }
});

SnakeMoveController.GetInstance = function () {
    if (null == SnakeMoveController._instance) {
        SnakeMoveController._instance = new SnakeMoveController();
    }
    return SnakeMoveController._instance;
};

var snakeMoveController = SnakeMoveController.GetInstance();
