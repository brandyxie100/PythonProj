/**
 * Created by alexgan on 2016/5/20.
 */

var isDebug = false;

var Logger = {
    info: function (msg) {
        console.info(new Date().toISOString() + " info: " + msg);
    },

    debug: function (msg) {
        if (isDebug) {
            console.debug(new Date().toISOString() + " debug: " + msg);
        }
    },

    error: function (msg) {
        console.error(new Date().toISOString() + " error: " + msg);
    },

    isDebugEnabled: function () {
        return isDebug;
    },

    setDebug: function (debug) {
        isDebug = debug;
    },

    printArrayInfo: function (incoming, array) {
        this._printArray(array, this.info, this.info);
    },

    printArrayError: function (incoming, array) {
        this._printArray(array, this.error, this.error);
    },

    printArrayDebug: function (incoming, array) {
        if (isDebug) {
            this._printArray(incoming, array, this.debug);
        }
    },

    _printArray: function (incoming, array, func) {
        var s = (incoming ? "<--" : "-->") + " Data: [";
        for (var i = 0; i < array.byteLength; i++) {
            s += array[i] + (i + 1 < array.byteLength ? "," : "");
        }
        s += "]";
        func(s);
    }
};