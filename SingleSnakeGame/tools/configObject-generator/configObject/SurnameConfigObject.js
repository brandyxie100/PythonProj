/**
 * Created by malloyzhu on 2016/5/13
 */

var SurnameConfigObject = cc.Class.extend({
    _config: null,

    ctor: function (config) {
        this._config = config;
    },

    /**
     * 获取配置
     * @returns {object}
     */
    getConfig: function () {
        return this._config;
    },

    /**
     * 获取ID
     * type: INTEGER
     * @returns {*}
     */
    getID: function () {
        return this._config["ID"];
    },

    /**
     * 设置ID
     * type: INTEGER
     * @param value
     */
    setID: function (value) {
        this._config["ID"] = value;
    },

    /**
     * 获取姓
     * type: TEXT
     * @returns {*}
     */
    getSurname: function () {
        return this._config["surname"];
    },

    /**
     * 设置姓
     * type: TEXT
     * @param value
     */
    setSurname: function (value) {
        this._config["surname"] = value;
    }
});