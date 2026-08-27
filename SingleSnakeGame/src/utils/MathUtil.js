/**
 * Created by malloyzhu on 2016/4/22.
 */

var MathUtil = {
    _table: [],

    init: function () {
        for (var angle = 0; angle <= 360; angle++) {
            var sin = Math.sin(2 * Math.PI / 360 * angle);
            var cos = Math.cos(2 * Math.PI / 360 * angle);
            this._table.push({sin: sin, cos: cos});
        }
    },

    getSin: function (angle) {
        var targetAngle = this._correctAngle(angle);
        return this._table[targetAngle].sin;
    },

    getCos: function (angle) {
        var targetAngle = this._correctAngle(angle);
        return this._table[targetAngle].cos;
    },

    _correctAngle: function (angle) {
        var targetAngle = Math.round(angle) % 360;
        targetAngle = targetAngle >= 0 ? targetAngle : (360 + targetAngle);
        return targetAngle;
    },

    getRandom: function (min, max) {
        var range = max - min;
        var rand = Math.random();
        return (min + Math.round(rand * range));
    },

    /**
     * 将浮点数四舍五入，取小数点后1位
     * @param x
     * @returns {Number}
     */
    toDecimal: function (x) {
        var f = parseFloat(x);
        if (isNaN(f)) {
            return;
        }
        f = Math.round(x * 10) / 10;
        return f;
    },

    toDecimal_3: function (x) {
        var f = parseFloat(x);
        if (isNaN(f)) {
            return;
        }
        f = Math.round(x * 1000) / 1000;
        return f;
    },

    toPercent: function(x){
        var f = parseFloat(x);
        if (isNaN(f)) {
            return;
        }
        f = Math.round(x * 10000) / 100;
        return f + "%";
    },

    byteToKByte: function (num) {
        var kb = Math.round(num / 1024 * 1000) / 1000;
        return kb;
    },

    kByteToMByte: function (num) {
        var kb = Math.round(num / 1024 * 100) / 100;
        return kb;
    }
};

MathUtil.init();
