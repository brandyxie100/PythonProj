'use strict'

var configGrow = require("./config_grow");

class ConfigMgr {
    constructor() {
        this.dataStore = [];
        this.dataAI = [];
    }

    init() {
        this.loadConfigGrow();
    }

    loadConfigGrow() {
        var jsonData = configGrow.config_grow;
        var level = null;
        var data = null;
        for (var i = 0; i < jsonData.length; i++) {
            level = parseInt(jsonData[i].level);
            data = jsonData[i];
            if (data) {
                data = {
                    level: parseInt(data.level),
                    energy: parseFloat(data.energy),
                    length: parseInt(data.length),
                    width: parseInt(data.width),
                    speed: parseInt(data.speed)
                };
            }
            this.dataStore[level] = data;
        }

        var robotData = configGrow.config_robot;
        var value = null;
        for (var i = 0; i < robotData.length; i++) {
            value = robotData[i];
            if (value) {
                value = {
                    length: parseInt(value.length),
                    dodgeInterval: parseFloat(value.dodgeInterval),
                    accProp: parseInt(value.accProp),
                };
            }
            this.dataAI[i] = value;
        }
    }

    getData(level) {
        return this.dataStore[level];
    }

    getAIData(length) {
        var data = null;
        var total = this.dataAI.length - 1;
        for (var i = 0; i < total; i++) {
            data = this.dataAI[i];
            if (data.length <= length && length < this.dataAI[i + 1].length) {
                //console.log("getAIData: length= ", length);
                //console.log("getAIData: i= ", i);
                return data;
            }
        }
        data = this.dataAI[total - 1];
        if (data && data.length < length && length < this.dataAI[total].length) {
            //console.log("getAIData: i= ", total);
            return data;
        }
        data = this.dataAI[total];
        if (data && length >= data.length) {
            //console.log("getAIData: i= ", total);
            return data;
        }

        return null;
    }

    findCeilData(level, energy) {
        var curData = this.getData(level),
            retData = null;

        while (curData && curData.energy <= energy) {
            retData = curData;
            curData = this.getData(++level);
        }

        return retData;
    }

    findFloorData(level, energy) {
        var curData = this.getData(level),
            retData = null;

        while (curData && curData.energy > energy) {
            curData = this.getData(--level);
            retData = curData;
        }

        return retData;
    }
}

module.exports = new ConfigMgr();
