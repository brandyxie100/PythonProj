/**
 * Created by malloyzhu on 2016/5/23.
 */

var StorageManager = cc.Class.extend({
    _firstStartUpGameKey: "firstStartUpGame",
    _openMusicKey: "openMusic",
    _openSoundKey: "openSound",
    _nickNameKey: "nickName",
    _leftRockerKey: "leftRocker",
    _fixedRockerKey: "fixedRocker",

    _nickName: null,
    _bOpenMusic: true,
    _bOpenSound: true,
    _bFirstStartUpGame: true,
    _bLeftRocker: true,
    _bFixedRocker: false,

    load: function () {
        this._bFirstStartUpGame = this._getData(this._firstStartUpGameKey, true);
        this._bOpenMusic = this._getData(this._openMusicKey, true);
        this._bOpenSound = this._getData(this._openSoundKey, true);
        this._nickName = this._getData(this._nickNameKey, null);
        this._bLeftRocker = this._getData(this._leftRockerKey, true);
        this._bFixedRocker = this._getData(this._fixedRockerKey, false);
    },

    getNickName: function () {
        return this._nickName;
    },

    isOpenMusic: function () {
        return this._bOpenMusic;
    },

    isOpenSound: function () {
        return this._bOpenSound;
    },

    isLeftRocker: function () {
        return this._bLeftRocker;
    },

    isFixedRocker: function () {
        return this._bFixedRocker;
    },

    onToggleMusicState: function (bOpen) {
        this._bOpenMusic = bOpen;
        this._recordData(this._openMusicKey, bOpen);
    },

    onToggleSoundState: function (bOpen) {
        this._bOpenSound = bOpen;
        this._recordData(this._openSoundKey, bOpen);
    },

    onToggleLeftRockerState: function (bOpen) {
        this._bLeftRocker = bOpen;
        this._recordData(this._leftRockerKey, bOpen);
    },

    onToggleFixedRockerState: function (bOpen) {
        this._bFixedRocker = bOpen;
        this._recordData(this._fixedRockerKey, bOpen);
    },

    recordNickName: function (nickName) {
        if (typeof nickName === 'string' && 0 != nickName.length && nickName != this._nickName) {
            this._nickName = nickName;
            this._recordData(this._nickNameKey, nickName);
        }
    },

    _getData: function (key, defaultValue) {
        var valStr = cc.sys.localStorage.getItem(key);  // get null if that key doesn't exists, otherwise string
        var val = defaultValue;

        try {
            if (valStr && valStr != "") {
                val = JSON.parse(valStr);   // casting to Number, Boolean, Array, Object if possible
            }
        }
        catch (err) {
            val = valStr;   // could be a plain String type
        }

        return val;
    },

    _recordData: function (key, value) {
        cc.sys.localStorage.setItem(key, JSON.stringify(value));
    },

    isFirstStartUpGame: function () {
        return this._bFirstStartUpGame;
    },

    recordFirstStartedUpGame: function () {
        this._bFirstStartUpGame = false;
        this._recordData(this._firstStartUpGameKey, false);
    }
});

StorageManager.GetInstance = function () {
    if (null == StorageManager._instance) {
        StorageManager._instance = new StorageManager();
    }
    return StorageManager._instance;
};

var storageManager = StorageManager.GetInstance();
