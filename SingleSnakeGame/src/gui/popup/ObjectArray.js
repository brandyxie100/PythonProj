/**
 * Created by malloyzhu on 2015/7/9.
 */

var ObjectArray = cc.Class.extend({
    _array: null,

    ctor: function () {
        this._array = [];
    },

    addObject: function (object) {
        if (null == object) {
            return;
        }
        this._retainObject(object);
        this._array.push(object);
    },

    getObjectByIndex: function (index) {
        if (!this._checkIndex(index)) {
            return null;
        }
        return this._array[index];
    },

    removeObject: function (object) {
        if (null == object) {
            return;
        }
        var index = this._array.indexOf(object);
        if (index > -1) {
            this._array.splice(index, 1);
            this._releaseObject(object);
        } else {
            console.log("object is no in array");
        }
    },

    removeObjectByIndex: function (index) {
        if (!this._checkIndex(index)) {
            return;
        }
        var object = this._array.splice(index, 1);
        this._releaseObject(object);
    },

    removeFirstObject: function () {
        if (this.isEmpty()) {
            return;
        }
        var object = this._array.shift();
        this._releaseObject(object);
    },

    removeLastObject: function () {
        if (this.isEmpty()) {
            return;
        }
        var object = this._array.pop();
        this._releaseObject(object);
    },

    removeAllObject: function () {
        for (var i in this._array) {
            var object = this._array.splice(i, 1);
            this._releaseObject(object);
        }
        this._array = [];
    },

    getFirstObject: function () {
        var bEmpty = this.isEmpty();
        return (bEmpty ? null : this._array[0]);
    },

    getLastObject: function () {
        var bEmpty = this.isEmpty();
        return (bEmpty ? null : this._array[this._array.length - 1]);
    },

    isEmpty: function () {
        return (0 == this._array.length);
    },

    size: function () {
        return this._array.length;
    },

    _checkIndex: function (index) {
        if (index < 0) {
            //console.log("index must be greater than 0");
            return false;
        }
        var length = this._array.length;
        if (index >= length) {
            //console.log("index must be less then array length");
            return false;
        }
        return true;
    },

    _retainObject: function (object) {
        if (object && object.retain) {
            object.retain();
        } else if (Util.isArray(object) || Util.isObject(object)) {
            for (var i in object) {
                this._retainObject(object[i]);
            }
        }
    },

    _releaseObject: function (object) {
        if (object && object.release) {
            object.release();
        } else if (Util.isArray(object) || Util.isObject(object)) {
            for (var i in object) {
                this._releaseObject(object[i]);
            }
        }
    }
});

