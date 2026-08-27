/**
 * Created by malloyzhu on 2016/6/15.
 */

var MapBorder = cc.Layer.extend({
    ctor: function (mapSize) {
        this._super();

        var drawNode = new cc.DrawNode();
        var halfMapWidth = mapSize.width / 2;
        var halfMapHeight = mapSize.height / 2;
        var radius = Math.sqrt(halfMapWidth * halfMapWidth + halfMapHeight * halfMapHeight);
        var lineWidth = radius - halfMapWidth + mapBorder;
        drawNode.drawCircle(cc.p(halfMapWidth, halfMapHeight), radius + 10, 0, 200, false, lineWidth * 2, cc.color(25, 14, 38, 255));
        this.addChild(drawNode);

        var circle = new cc.DrawNode();
        lineWidth = 60;
        circle.drawCircle(cc.p(halfMapWidth, halfMapHeight), 2800 + 32, 0, 200, false, lineWidth, cc.color(178, 34, 34, 255));
        //console.log("line width= " + lineWidth);
        //console.log("radius width= " + radius);
        this.addChild(circle);
    }
});
