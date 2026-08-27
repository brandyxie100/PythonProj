/**
 * Created by billbao on 2015/5/19.
 */

TimeFormatType = {hms: "hh:mm:ss", ms: "mm:ss"};

var Util = {
    /**
     * Format a number of seconds to hh:mm:ss
     *
     * @param time {integer} in seconds
     * @returns {string}
     */
    formatTime: function (time, timeFormatType) {
        var h = Math.floor(time / 3600);
        var m = Math.floor((time % 3600) / 60);
        var s = time % 60;

        timeFormatType = timeFormatType || TimeFormatType.hms;
        var result = "";
        if (timeFormatType == TimeFormatType.hms) {
            result = ( h < 10 ? ("0" + h) : h ) + ":" + ( m < 10 ? ("0" + m) : m ) + ":" + ( s < 10 ? ("0" + s) : s );
        } else if (timeFormatType == TimeFormatType.ms) {
            result = ( m < 10 ? ("0" + m) : m ) + ":" + ( s < 10 ? ("0" + s) : s );
        }
        return result;
    },

    /**
     * Read the text content from file with utf-8 encoding
     *
     * @param file {string} filepath start with "res/"
     * @returns {string}
     */
    readTxtFileSync: function (file) {
        if (cc.sys.isNative) {
            return jsb.fileUtils.getStringFromFile(file);
        } else {
            return cc.loader._loadTxtSync(cc.path.join(cc.loader.resPath, file));
        }
    },

    /*
     * Recursively merge properties of two objects
     * @param obj1 IN|OUT
     * @param obj2 IN
     * @returns {*} obj1
     */
    mergeRecursive: function (obj1, obj2) {
        for (var p in obj2) {
            try {
                // Property in destination object set; update its value.
                if (obj2[p].constructor == Object) {
                    obj1[p] = Util.mergeRecursive(obj1[p], obj2[p]);
                } else {
                    obj1[p] = obj2[p];
                }
            } catch (e) {
                // Property in destination object not set; create it and set its value.
                obj1[p] = obj2[p];
            }
        }

        return obj1;
    },

    clone: function (obj) {
        var newObj = (obj.constructor) ? new obj.constructor : {};
        for (var k in obj) {
            var copy = obj[k];
            if (((typeof copy) === "object") && copy && !(copy instanceof cc.Node)) {
                newObj[k] = Util.clone(copy);
            } else {
                newObj[k] = copy;
            }
        }
        return newObj;
    },

    /**
     * 回调函数处理
     * @param callback：回调函数
     * @param caller：函数调用对象
     * @returns {Function}
     *
     * eg:
     * var One = cc.Class.extend({
     *      setNextFunc:function(func) {
     *          this._nextFunc = func;
     *      },
     *
     *      _onNextBtnClicked:function(sender, type) {
     *          this._nextFunc();
     *          //如果有参数则直接传参数，如this._nextFunc("test1", xxx, yyy);
     *      }
     * });
     *
     * var Two = cc.Class.extend({
     *      ctor:function() {
     *          this._oneClass = new One();
     *          this._oneClass.setNextFunc(Util.handler(this._oneClassNextFunc, this));
     *      },
     *
     *      _oneClassNextFunc:function() {
     *
     *      }
     * })
     */
    handler: function (callback, caller) {
        return function () {
            callback.apply(caller, arguments);
        }
    },

    isBlankString: function (str) {
        return (!str || /^\s*$/.test(str));
    },

    endsWithString: function (str, suffix) {
        if (!Util.isBlankString(str)) {
            return str.match(suffix + "$") == suffix;
        } else {
            return false;
        }
    },

    startsWithString: function (str, prefix) {
        if (!Util.isBlankString(str)) {
            return str.indexOf(prefix) === 0;
        } else {
            return false;
        }
    },

    /**
     * 获取字符串的长度，中文算2个长度，英文算1个长度
     */
    getStringLength: function (str) {
        var cArr = str.match(/[^\x00-\xff]/ig);
        return str.length + (cArr == null ? 0 : cArr.length);
    },

    /**
     * 将第一个字母转换成大写
     */
    upperFirstLetter: function (word) {
        return word.substring(0, 1).toUpperCase() + word.substring(1);
    },

    isArray: function (object) {
        return Object.prototype.toString.call(object) === '[object Array]';
    },

    isObject: function (object) {
        return ((typeof object) === "object");
    },

    isNumber: function (object) {
        return typeof object === 'number' || Object.prototype.toString.call(object) === '[object Number]';
    },

    // 将 list 切割成 n 列的二维数组
    spliceListToNCol: function (list, nCol) {
        var result = [];
        var row = [];
        var i = 0;
        for (; i < list.length; i++) {
            row.push(list[i]);
            if ((i + 1) % nCol == 0) {
                result.push(row);
                row = [];
            }
        }

        if (i % nCol !== 0) {
            result.push(row);
        }

        return result;
    },

    /**
     * 将字符串转换为整型数组
     * @param str： 格式为 "xxx,yyy"的字符串
     * @returns {Array}
     */
    splitStringToIntArray: function (str) {
        var intArr = [];
        var strArr = str.split(",");
        for (var i in strArr) {
            intArr.push(parseInt(strArr[i]));
        }
        return intArr;
    },

    /**
     * 将字符串转换为整型数组
     * @param str： 格式为 "xxx:y,yyy:x#qqq:n,ccc:a"的字符串
     * @returns {Array}
     */
    splitStringToObjectArray: function (str) {
        var objectArr = [];
        var strArr = str.split("#");
        for (var i in strArr) {
            objectArr.push(JSON.parse(strArr[i]));
        }
        return objectArr;
    },

    getRandomBool: function () {
        var random = MathUtil.getRandom(0, 100);
        return random % 2 == 0;
    },

    registerListener: function (listenerList, eventID, eventFun, priority) {
        var bExist = false;
        for (var i in listenerList) {
            if (listenerList[i].eventID == eventID) {
                bExist = true;
                break;
            }
        }

        if (!bExist) {
            var fun = CEventManager.addEventListener(eventID, eventFun, priority);
            listenerList.push({eventID: eventID, eventFun: fun});
        }
    },

    unRegisterListener: function (listenerList, eventID) {
        for (var i in listenerList) {
            if (listenerList[i].eventID == eventID) {
                CEventManager.removeEventListener(eventID, listenerList[i].eventFun);
                return;
            }
        }
    },

    unRegisterListeners: function (listenerList) {
        for (var i in listenerList) {
            CEventManager.removeEventListener(listenerList[i].eventID, listenerList[i].eventFun);
        }
    },

    getClient: function () {
        var userAgent = navigator.userAgent;
        var isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
        var isAndroid = /Android/.test(userAgent);
        var isIOS = /iPhone|iPad|iPod/.test(userAgent);
        return {
            isMobile: isMobile,
            isAndroid: isAndroid,
            isIOS: isIOS
        }
    }
};

/**
 * A string tool to construct a string with format string.
 * for example:
 *      cc.formatStr("a: %d, b: %s", a, "b");
 * @returns {String}
 */
Util.formatString = cc.formatStr;
