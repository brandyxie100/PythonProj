/**
 * Created by malloyzhu on 2016/5/18.
 * Keyboard: Arrow keys steer, A (or Space) boosts.
 *
 * Cocos2d-JS binds keydown to the canvas and then stopPropagation().
 * Canvas is not focusable by default, so those events never fire.
 * Listen on document in capture phase so keys work without canvas focus
 * and are not swallowed by the canvas handler.
 */

var SnakeMoveController = cc.Class.extend({
    _viewportOffsetPosition: null,
    _keysPressed: null,
    _isKeyboardInit: false,
    _onKeyDown: null,
    _onKeyUp: null,
    _onBlur: null,

    ctor: function () {
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
        this._onKeyDown = function (e) {
            self._applyKey(e, true);
        };
        this._onKeyUp = function (e) {
            self._applyKey(e, false);
        };
        this._onBlur = function () {
            self.reset();
        };

        if (typeof document !== "undefined" && document.addEventListener) {
            document.addEventListener("keydown", this._onKeyDown, true);
            document.addEventListener("keyup", this._onKeyUp, true);
        }
        if (typeof window !== "undefined" && window.addEventListener) {
            window.addEventListener("blur", this._onBlur, false);
        }

        this._focusGameCanvas();
    },

    _focusGameCanvas: function () {
        var canvas = (typeof cc !== "undefined" && cc._canvas) ? cc._canvas : document.getElementById("gameCanvas");
        if (!canvas) {
            return;
        }
        canvas.setAttribute("tabindex", "1");
        canvas.style.outline = "none";
        var focusCanvas = function () {
            canvas.focus();
        };
        canvas.addEventListener("mousedown", focusCanvas, false);
        canvas.addEventListener("touchstart", focusCanvas, false);
        focusCanvas();
    },

    /**
     * Map a DOM keyboard event to steer / boost. Returns true if it is a game key.
     */
    _classifyKey: function (e) {
        var keyCode = e.keyCode || e.which;
        var code = e.code || "";
        var key = e.key || "";

        if (keyCode === 38 || code === "ArrowUp" || key === "ArrowUp") {
            return "up";
        }
        if (keyCode === 40 || code === "ArrowDown" || key === "ArrowDown") {
            return "down";
        }
        if (keyCode === 37 || code === "ArrowLeft" || key === "ArrowLeft") {
            return "left";
        }
        if (keyCode === 39 || code === "ArrowRight" || key === "ArrowRight") {
            return "right";
        }
        if (keyCode === 65 || code === "KeyA" || key === "a" || key === "A") {
            return "acc";
        }
        if (keyCode === 32 || code === "Space" || key === " " || key === "Spacebar") {
            return "acc";
        }
        return null;
    },

    _applyKey: function (e, isDown) {
        var action = this._classifyKey(e);
        if (!action) {
            return;
        }

        if (e.preventDefault) {
            e.preventDefault();
        }
        if (e.stopPropagation) {
            e.stopPropagation();
        }

        if (this._keysPressed[action] === isDown) {
            return;
        }
        this._keysPressed[action] = isDown;

        if (action === "acc") {
            if (isDown) {
                this._startAccelerate();
            } else {
                this._endAccelerate();
            }
            return;
        }

        this._tickKeyboardSteer();
    },

    _startAccelerate: function () {
        var mainPlayer = (typeof playerManager !== "undefined") ? playerManager.getMainPlayer() : null;
        if (mainPlayer) {
            mainPlayer.onAccelerateStart();
        } else if (typeof NetProxy !== "undefined") {
            NetProxy.ChangeSnakeSpeed(1);
        }
    },

    _endAccelerate: function () {
        if (typeof NetProxy !== "undefined") {
            NetProxy.ChangeSnakeSpeed(2);
        }
        var mainPlayer = (typeof playerManager !== "undefined") ? playerManager.getMainPlayer() : null;
        if (mainPlayer) {
            mainPlayer.onAccelerateEnd();
        }
    },

    _tickKeyboardSteer: function () {
        if (!this._keysPressed) {
            return;
        }
        if (typeof NetProxy === "undefined" || !NetProxy.MoveSnake) {
            return;
        }
        if (typeof playerManager !== "undefined" && !playerManager.getMainPlayer()) {
            return;
        }

        var dirX = 0;
        var dirY = 0;
        if (this._keysPressed.up) {
            dirY += 1;
        }
        if (this._keysPressed.down) {
            dirY -= 1;
        }
        if (this._keysPressed.left) {
            dirX -= 1;
        }
        if (this._keysPressed.right) {
            dirX += 1;
        }

        if (dirX === 0 && dirY === 0) {
            return;
        }

        NetProxy.MoveSnake(cc.p(dirX, dirY));
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
        if (!this._keysPressed) {
            return;
        }
        if (this._keysPressed.acc) {
            this._keysPressed.acc = false;
            this._endAccelerate();
        }
        this._keysPressed.up = false;
        this._keysPressed.down = false;
        this._keysPressed.left = false;
        this._keysPressed.right = false;
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
