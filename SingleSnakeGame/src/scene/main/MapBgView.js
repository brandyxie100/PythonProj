/**
 * Created by malloyzhu on 2016/4/21.
 */

var MapBgView = cc.Layer.extend({
    _gridsData: null,
    _gridsSpritePool: null,
    _gridBatchNode: null,

    ctor: function (mapSize) {
        this._super();

        var gridSprite = new cc.Sprite(res.bg_jpg);
        var gridHeight = gridSprite.getContentSize().height;
        var gridWidth = gridSprite.getContentSize().width;
        var mapWidth = mapSize.width;
        var mapHeight = mapSize.height;
        var maxRow = Math.ceil(mapHeight / gridHeight);
        var maxCol = Math.ceil(mapWidth / gridWidth);

        var gridBatchNode = new cc.SpriteBatchNode(res.bg_jpg, maxRow * maxCol);
        this.addChild(gridBatchNode);
        this._gridBatchNode = gridBatchNode;

        this._gridsData = [];
        for (var row = 0; row < maxRow; row++) {
            this._gridsData[row] = [];
            for (var col = 0; col < maxCol; col++) {
                this._gridsData[row][col] = {position: cc.p(col * gridWidth, row * gridHeight)};
            }
        }

        this._gridsSpritePool = [];
        var viewportWidth = cc.winSize.width;
        var viewportHeight = cc.winSize.height;
        var viewportRow = Math.ceil(viewportHeight / gridHeight);
        var viewportCol = Math.ceil(viewportWidth / gridWidth);
        for (var row = 0; row < viewportRow; row++) {
            for (var col = 0; col < viewportCol; col++) {
                this._createGridSprite();
            }
        }
    },

    _createGridSprite: function () {
        var gridSprite = new cc.Sprite(res.bg_jpg);
        gridSprite.setAnchorPoint(0, 0);
        this._gridBatchNode.addChild(gridSprite);
        this._gridsSpritePool.push(gridSprite);
        return gridSprite;
    },

    setPosition: function (x, y) {
        this._super(x, y);
        this._updateGridSprites();
    },

    setScale: function (scale) {
        this._super(scale);
        this._updateGridSprites();
    },

    _updateGridSprites: function () {
        var scale = this.getScale();
        var viewportWidth = cc.winSize.width * scale;
        var viewportHeight = cc.winSize.height * scale;
        var gridSpriteWidth = this._gridsSpritePool[0].getContentSize().width * scale;
        var gridSpriteHeight = this._gridsSpritePool[0].getContentSize().height * scale;
        var rowCount = Math.ceil(viewportHeight / gridSpriteHeight) + 1;
        var colCount = Math.ceil(viewportWidth / gridSpriteWidth) + 1;
        var position = this.getPosition();
        var gridX = parseInt(Math.abs(position.x) / gridSpriteWidth);
        var gridY = parseInt(Math.abs(position.y) / gridSpriteHeight);

        var startRow = gridY - rowCount;
        if (startRow < 0) {
            startRow = 0;
        }

        var endRow = gridY + rowCount;
        if (endRow > this._gridsData.length - 1) {
            endRow = this._gridsData.length - 1;
        }

        var startCol = gridX - colCount;
        if (startCol < 0) {
            startCol = 0;
        }

        var endCol = gridX + colCount;
        if (endCol > this._gridsData[0].length - 1) {
            endCol = this._gridsData[0].length - 1;
        }

        var index = 0;
        for (var row = startRow; row <= endRow; row++) {
            for (var col = startCol; col <= endCol; col++) {
                if (null != this._gridsData[row]) {
                    var data = this._gridsData[row][col];
                    if (null != data) {
                        var gridSprite = null != this._gridsSpritePool[index] ? this._gridsSpritePool[index] : this._createGridSprite();
                        gridSprite.setPosition(data.position);
                        index++;
                    }
                }
            }
        }
    }
});
