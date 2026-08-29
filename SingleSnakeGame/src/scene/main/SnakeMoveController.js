/**
 * Created by malloyzhu on 2016/5/18.
 */

var SnakeMoveController = cc.Class.extend({
    _viewportOffsetPosition: null,
    _event: null,
    _keysPressed: null,
    _isKeyboardInit: false,

    ctor: function () {
        this._event = new CEvent();
        this._keysPressed = {
            up: false,
            down: false,
            left: false,
            right: false,
            acc: false
        };
        this.initKeyboardListener();
    },

    initKeyboardListener: function () {
        if (this._isKeyboardInit) {
            return;
        }
        this._isKeyboardInit = true;

        var self = this;

        // Cocos2d-JS EventListenerKeyboard
        if (cc.eventManager) {
            var keyboardListener = cc.EventListener.create({
                event: cc.EventListener.KEYBOARD,
                onKeyPressed: function (keyCode, event) {
                    self._handleKeyDown(keyCode);
                },
                onKeyReleased: function (keyCode, event) {
                    self._handleKeyUp(keyCode);
                }
            });
            cc.eventManager.addListener(keyboardListener, 1);
        }

        // Web DOM window fallback to guarantee input capture across all browsers
        if (typeof window !== "undefined" && window.addEventListener) {
            window.addEventListener("keydown", function (e) {
                self._handleKeyDown(e.keyCode || e.which, e.code || e.key);
            });
            window.addEventListener("keyup", function (e) {
                self._handleKeyUp(e.keyCode || e.which, e.code || e.key);
            });
        }
    },

    _handleKeyDown: function (keyCode, keyName) {
        var changed = false;

        // Key Up (Arrow Up / W)
        if (keyCode === 38 || keyCode === (cc.KEY && cc.KEY.up) || keyName === "ArrowUp" || keyName === "KeyW") {
            if (!this._keysPressed.up) {
                this._keysPressed.up = true;
                changed = true;
            }
        }
        // Key Down (Arrow Down / S)
        else if (keyCode === 40 || keyCode === (cc.KEY && cc.KEY.down) || keyName === "ArrowDown" || keyName === "KeyS") {
            if (!this._keysPressed.down) {
                this._keysPressed.down = true;
                changed = true;
            }
        }
        // Key Left (Arrow Left)
        else if (keyCode === 37 || keyCode === (cc.KEY && cc.KEY.left) || keyName === "ArrowLeft") {
            if (!this._keysPressed.left) {
                this._keysPressed.left = true;
                changed = true;
            }
        }
        // Key Right (Arrow Right / D)
        else if (keyCode === 39 || keyCode === (cc.KEY && cc.KEY.right) || keyName === "ArrowRight" || keyName === "KeyD") {
            if (!this._keysPressed.right) {
                this._keysPressed.right = true;
                changed = true;
            }
        }
        // Key A / Space (Acceleration)
        else if (keyCode === 65 || keyCode === 97 || keyCode === (cc.KEY && cc.KEY.a) || keyCode === 32 || keyCode === (cc.KEY && cc.KEY.space) || keyName === "KeyA" || keyName === "a" || keyName === "A" || keyName === "Space") {
            if (!this._keysPressed.acc) {
                this._keysPressed.acc = true;
                this._event.type = CEventType.ON_START_ACCELERATE;
                CEventManager.dispatchEvent(this._event);
            }
        }

        if (changed) {
            this._updateKeyboardDirection();
        }
    },

    _handleKeyUp: function (keyCode, keyName) {
        var changed = false;

        // Key Up
        if (keyCode === 38 || keyCode === (cc.KEY && cc.KEY.up) || keyName === "ArrowUp" || keyName === "KeyW") {
            if (this._keysPressed.up) {
                this._keysPressed.up = false;
                changed = true;
            }
        }
        // Key Down
        else if (keyCode === 40 || keyCode === (cc.KEY && cc.KEY.down) || keyName === "ArrowDown" || keyName === "KeyS") {
            if (this._keysPressed.down) {
                this._keysPressed.down = false;
                changed = true;
            }
        }
        // Key Left
        else if (keyCode === 37 || keyCode === (cc.KEY && cc.KEY.left) || keyName === "ArrowLeft") {
            if (this._keysPressed.left) {
                this._keysPressed.left = false;
                changed = true;
            }
        }
        // Key Right
        else if (keyCode === 39 || keyCode === (cc.KEY && cc.KEY.right) || keyName === "ArrowRight" || keyName === "KeyD") {
            if (this._keysPressed.right) {
                this._keysPressed.right = false;
                changed = true;
            }
        }
        // Key A / Space
        else if (keyCode === 65 || keyCode === 97 || keyCode === (cc.KEY && cc.KEY.a) || keyCode === 32 || keyCode === (cc.KEY && cc.KEY.space) || keyName === "KeyA" || keyName === "a" || keyName === "A" || keyName === "Space") {
            if (this._keysPressed.acc) {
                this._keysPressed.acc = false;
                this._event.type = CEventType.ON_END_ACCELERATE;
                CEventManager.dispatchEvent(this._event);
            }
        }

        if (changed) {
            this._updateKeyboardDirection();
        }
    },

    _updateKeyboardDirection: function () {
        var dirX = 0;
        var dirY = 0;

        if (this._keysPressed.up) dirY += 1;
        if (this._keysPressed.down) dirY -= 1;
        if (this._keysPressed.left) dirX -= 1;
        if (this._keysPressed.right) dirX += 1;

        if (dirX !== 0 || dirY !== 0) {
            NetProxy.MoveSnake(cc.p(dirX * 500, dirY * 500));
        }
    },

    onOperatorRocker: function (rocker) {
        var touchType = rocker.getTouchType();
        if (touchType == TouchType.MOVED) {
            this._moveSnakeByRocker(rocker);
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

        NetProxy.MoveSnake(targetPosition);
    },

    _moveSnakeByTouch: function (touch) {
        var touchPos = touch.getLocation();
        var target = cc.p(touchPos.x - cc.winSize.width / 2, touchPos.y - cc.winSize.height / 2);
        NetProxy.MoveSnake(target);
    },

    reset: function () {
        this._viewportOffsetPosition = null;
        if (this._keysPressed) {
            if (this._keysPressed.acc) {
                this._keysPressed.acc = false;
                this._event.type = CEventType.ON_END_ACCELERATE;
                CEventManager.dispatchEvent(this._event);
            }
            this._keysPressed.up = false;
            this._keysPressed.down = false;
            this._keysPressed.left = false;
            this._keysPressed.right = false;
        }
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

