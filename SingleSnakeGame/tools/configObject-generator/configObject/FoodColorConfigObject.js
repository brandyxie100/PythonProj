/**
 * Created by malloyzhu on 2016/5/13
 */

var FoodColorConfigObject = cc.Class.extend({
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
     * 获取颜色
     * type: TEXT
     * @returns {*}
     */
    getColor: function () {
        return this._config["color"];
    },

    /**
     * 设置颜色
     * type: TEXT
     * @param value
     */
    setColor: function (value) {
        this._config["color"] = value;
    }
});