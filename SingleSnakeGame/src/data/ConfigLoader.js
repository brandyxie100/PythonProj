/**
 * Created by malloyzhu on 2016/2/4.
 */

var ConfigLoader = {
    _foodColorConfigs: null,

    load: function () {
        this._foodColorConfigs = config_foodColor;
    },

    getFoodColorConfigs: function () {
        return this._foodColorConfigs;
    },

    _getConfigByID: function (configs, ID) {
        for (var i in configs) {
            if (configs[i].ID == ID) {
                return Util.clone(configs[i]);
            }
        }
        console.log("config is null");
        return null;
    }
};
