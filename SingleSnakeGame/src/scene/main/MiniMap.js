/**
 * Created by malloyzhu on 2016/4/26.
 */

var MiniMap = cc.Node.extend({
    _listenerList: null,
    _pointDrawNode: null,
    _scale: null,
    _selfSnakeColor: null,
    _otherSnakeColor: null,
    _firstSnakeColor: null,

    ctor: function (mapSize) {
        this._super();

        this._listenerList = [];

        var radarSprite = new cc.Sprite();
        radarSprite.initWithSpriteFrameName("icon_radar.png");
        var size = radarSprite.getContentSize();
        radarSprite.setPosition(size.width / 2, size.height / 2);
        this.addChild(radarSprite);

        this.setContentSize(radarSprite.getContentSize());
        this.setAnchorPoint(0.5, 0.5);

        var diff = 22 * 2;
        var drawNodeParent = new cc.Node();
        drawNodeParent.setContentSize(size.width - diff, size.height - diff);
        drawNodeParent.setAnchorPoint(0.5, 0.5);
        drawNodeParent.setPosition(size.width / 2, size.height / 2);
        this.addChild(drawNodeParent);
        this._scale = mapSize.width / drawNodeParent.getContentSize().width;

        var drawNode = new cc.DrawNode();
        drawNodeParent.addChild(drawNode);
        this._pointDrawNode = drawNode;

        this._selfSnakeColor = cc.hexToColor("#9cff00");
        this._otherSnakeColor = cc.hexToColor("#ff8062");
        this._firstSnakeColor = cc.hexToColor("#ff0000");
    },

    onEnter: function () {
        this._super();
        Util.registerListener(this._listenerList, CEventType.UPDATE_RADAR_INFO, this._onUpdateRadarInfo.bind(this));
    },

    onExit: function () {
        this._super();
        Util.unRegisterListeners(this._listenerList);
    },

    _getPointPosition: function (position) {
        return cc.p(position.x / this._scale, position.y / this._scale);
    },

    _onUpdateRadarInfo: function () {
        this._pointDrawNode.clear();
        //var snakesPosition = dataManager.getRankList();
        //if (0 != snakesPosition.length) {
        //    var pointPosition = this._getPointPosition(cc.p(snakesPosition[0].position.xPos, snakesPosition[0].position.yPos));
        //    this._pointDrawNode.drawDot(pointPosition, 3, this._firstSnakeColor);
        //}

        var snakesPosList = dataManager.getRadarInfo();
        var pos;
        var pointPosition;
        for (var i in snakesPosList) {
            pos = snakesPosList[i];
            pointPosition = this._getPointPosition(cc.p(pos.xPos, pos.yPos));
            if (Math.random() * 10 < 1) {
                //console.log("not draw");
            } else {
                this._pointDrawNode.drawDot(pointPosition, 3, this._otherSnakeColor);
            }
        }

        if (null != playerManager.getMainPlayer()) {
            if (!playerManager.getMainPlayer().isDied()) {
                pointPosition = this._getPointPosition(playerManager.getViewPointPos());
                this._pointDrawNode.drawDot(pointPosition, 4, this._selfSnakeColor);
            } else {
                this._pointDrawNode.drawDot(cc.p(0, 0), 4, this._selfSnakeColor);
            }
        } else {
            this._pointDrawNode.drawDot(cc.p(0, 0), 4, this._selfSnakeColor);
        }
    }
});
