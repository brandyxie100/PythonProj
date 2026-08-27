/**
 * Created by malloyzhu on 2016/5/13
 */

var NameConfigObject = cc.Class.extend({
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
     * 获取名
     * type: TEXT
     * @returns {*}
     */
    getName: function () {
        return this._config["name"];
    },

    /**
     * 设置名
     * type: TEXT
     * @param value
     */
    setName: function (value) {
        this._config["name"] = value;
    }
});