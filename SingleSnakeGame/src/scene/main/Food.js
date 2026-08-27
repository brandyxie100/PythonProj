/**
 * Created by malloyzhu on 2016/6/12.
 */

var Food = cc.Node.extend({
    _views: null,
    _foodStructure: null,
    _point1View: null,
    _point2View: null,
    _point3View: null,
    _bEatenAction: null,
    _eatenActionCompleteCallBack: null,
    _batchNode: null,
    _opacityCoefficient: 1,
    _opacityIncrement: null,
    _minOpacity: null,
    _maxOpacity: null,

    ctor: function (foodStructure, batchNode) {
        this._super();

        this._views = [];
        this._batchNode = batchNode;
        this._foodStructure = foodStructure;
        this._bEatenAction = false;

        this._initPoint1View();
        this._initPoint2View();
        this._initPoint3View();
    },

    finish: function () {
        this._point3View.setOpacity(MathUtil.getRandom(this._minOpacity, this._maxOpacity));
        this.updateOpacity();
    },

    updateFoodStructure: function (foodData, colorList) {
        this._foodStructure.id = foodData.foodId;
        this._foodStructure.radius = foodData.radius;
        this._foodStructure.color = colorList[foodData.color];
        this._foodStructure.originalX = foodData.position.xPos;
        this._foodStructure.originalY = foodData.position.yPos;
        this._foodStructure.type = foodData.foodType;
    },

    _isOpenEffect: function () {
        if (this._foodStructure.type == PDataDef.FoodType.accelerateResidual) {
            return false;
        }
        return this._foodStructure.radius * GAME_MAP_SCALE > 8;
    },

    updatePosition: function () {
        this._updateViewsPosition(this._foodStructure.originalX, this._foodStructure.originalY);
        this.setPosition(this._foodStructure.originalX, this._foodStructure.originalY);
    },

    updateColor: function () {
        this._point1View.setColor(this._foodStructure.color);
        this._point3View.setColor(this._foodStructure.color);
    },

    updateScale: function () {
        var foodWidth = this._foodStructure.radius * 2;
        var scale1 = foodWidth / this._point1View.getContentSize().width;
        this._point1View.setScale(scale1);

        if (this._isOpenEffect()) {
            var scale2 = foodWidth / this._point2View.getContentSize().width;
            scale2 = this._foodStructure.type != PDataDef.FoodType.deathResidual ? scale2 * 1.3 : scale2 * 1.8;
            this._point2View.setScale(scale2);

            var scale3 = foodWidth / this._point3View.getContentSize().width * 2.5;
            this._point3View.setScale(scale3);
        }
    },

    updateVisible: function (bValue) {
        this.setVisible(bValue);
        if (bValue === true && !this._isOpenEffect()) {
            this._point2View.setVisible(false);
            this._point3View.setVisible(false);
        }
    },

    updateOpacity: function () {
        var opacity = this._getOpacity();

        var point2Opacity = this._foodStructure.type != PDataDef.FoodType.deathResidual ? opacity : 255;
        this._point2View.setOpacity(point2Opacity);

        var point3Opacity = this._isOpenEffect() ? opacity : 255;
        this._point3View.setOpacity(point3Opacity);
    },

    _getOpacity: function () {
        var opacity = this._point3View.getOpacity();
        if (opacity >= this._maxOpacity) {
            this._opacityCoefficient = -1;
        }

        if (opacity <= this._minOpacity) {
            this._opacityCoefficient = 1;
        }

        opacity += (this._opacityIncrement * this._opacityCoefficient);

        if (opacity > this._maxOpacity) {
            opacity = this._maxOpacity;
        }

        if (opacity < this._minOpacity) {
            opacity = this._minOpacity;
        }

        return opacity;
    },

    setOpacityIncrement: function (value) {
        this._opacityIncrement = value;
    },

    setMaxOpacity: function (value) {
        this._maxOpacity = value;
    },

    setMinOpacity: function (value) {
        this._minOpacity = value;
    },

    _initPoint1View: function () {
        var view = new cc.Sprite();
        this._views.push(view);
        view.initWithSpriteFrameName("point1.png");
        this._batchNode.addChild(view, 2);
        this._point1View = view;
    },

    _initPoint2View: function () {
        var view = new cc.Sprite();
        this._views.push(view);
        view.initWithSpriteFrameName("point2.png");
        this._batchNode.addChild(view, 3);
        this._point2View = view;
    },

    _initPoint3View: function () {
        var view = new cc.Sprite();
        this._views.push(view);
        view.initWithSpriteFrameName("point3.png");
        this._batchNode.addChild(view, 1);
        this._point3View = view;
    },

    eaten: function (targetPosition) {
        this._recordScale();
        this.setScale(1);
        this._bEatenAction = true;
        var distance = cc.pDistance(targetPosition, this.getPosition());
        var interval = distance / 200; // speed 200
        var moveAction = new cc.MoveTo(interval, targetPosition);
        var scaleAction = new cc.ScaleTo(interval / 1.5, 0);
        var spawnAction = new cc.Spawn(moveAction, scaleAction);
        var callback = new cc.CallFunc(this._onEatenActionComplete, this);
        var action = new cc.Sequence(spawnAction, callback);
        this.stopAllActions();
        this.runAction(action);
        this.scheduleUpdate();
    },

    runBornAction: function () {
        this._recordScale();
        this.setScale(0);
        var scaleAction = new cc.ScaleTo(0.5, 1);
        var callback = new cc.CallFunc(this._onBornActionComplete, this);
        var action = new cc.Sequence(scaleAction, callback);
        this.stopAllActions();
        this.runAction(action);
        this.scheduleUpdate();
    },

    _onBornActionComplete: function () {
        this.unscheduleUpdate();
    },

    update: function (dt) {
        var position = cc.sys.isNative ? this.getPosition3D() : this.getPosition();
        this._updateViewsPosition(position.x, position.y);
        this._updateViewsScaleOnScaleAction(this.getScale());
    },

    _updateViewsPosition: function (positionX, positionY) {
        for (var i in this._views) {
            this._views[i].setPosition(positionX, positionY);
        }
    },

    _updateViewsScaleOnScaleAction: function (value) {
        for (var i in this._views) {
            var originalScale = this._views[i].getUserData();
            var scale = originalScale * value;
            this._views[i].setScale(scale);
        }
    },

    _recordScale: function () {
        for (var i in this._views) {
            this._views[i].setUserData(this._views[i].getScale());
        }
    },

    _onEatenActionComplete: function () {
        this._bEatenAction = false;
        this._eatenActionCompleteCallBack && this._eatenActionCompleteCallBack(this);
        this.unscheduleUpdate();
    },

    setVisible: function (bValue) {
        this._super(bValue);
        for (var i in this._views) {
            this._views[i].setVisible(bValue);
        }
    },

    getId: function () {
        return this._foodStructure.id;
    },

    setType: function (type) {
        this._foodStructure.type = type;
    },

    getType: function () {
        return this._foodStructure.type;
    },

    setEatenActionCompleteCallBack: function (fun) {
        this._eatenActionCompleteCallBack = fun;
    }
});

var MovableFood = Food.extend({
    _initPoint3View: function () {
        var view = new cc.Sprite();
        this._views.push(view);
        view.initWithSpriteFrameName("point4.png");
        this._batchNode.addChild(view, 1);
        this._point3View = view;
    },

    updateVisible: function (bValue) {
        this.setVisible(bValue);
    },

    updateScale: function () {
        var foodWidth = this._foodStructure.radius * 2;
        var scale1 = foodWidth / this._point1View.getContentSize().width;
        this._point1View.setScale(scale1);

        var scale2 = foodWidth / this._point2View.getContentSize().width;
        this._point2View.setScale(scale2 * 1.6);

        this._point3View.setScale(1);
    },

    updateColor: function () {
        this._point1View.setColor(this._foodStructure.color);
        this._point3View.setColor(this._foodStructure.color);
    },

    updateOpacity: function () {
        var opacity = this._getOpacity();
        this._point2View.setOpacity(opacity);
        this._point3View.setOpacity(opacity);
    }
});

var FoodStructure = function (id, radius, color, energy, positionX, positionY, type) {
    this.id = id;
    this.radius = radius;
    this.color = color;
    this.energy = energy;
    this.originalX = positionX;
    this.originalY = positionY;
    this.type = type;
};
