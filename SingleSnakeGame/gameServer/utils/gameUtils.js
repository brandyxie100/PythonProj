/*  
 * Class:         gameUtils
 * Description:   Helper class for some game operations
 * Created:       15.04.2016
 * Last change:   15.04.2016
 * Collaborators: circa94
 */

'use strict';

var consts = require("./constants");
var mathUtils = require("./mathUtils");
var settings = require("./settings");

var g_mapRadius = settings.readSetting("map-radius");
var g_bornArea = settings.readSetting("born-area");
var CLIENT_VERSION = settings.readSetting("client-version");
var TOTAL_KILL_COUNT = settings.readSetting("total_kill_count");

module.exports = {
    getRandomSpawnPoint: function () {
        return {
            x: mathUtils.getRandomInt(g_mapRadius - g_bornArea, g_mapRadius + g_bornArea),
            y: mathUtils.getRandomInt(g_mapRadius - g_bornArea, g_mapRadius + g_bornArea)
        };
    },

    getInterpolatePoints: function (keyNodes, stride) {
        var resultNodes = [];
        var len = keyNodes.length;

        if (len == 0)
            return resultNodes;

        // 插入第一个点
        resultNodes.push({xPos: keyNodes[0].xPos, yPos: keyNodes[0].yPos});
        // console.info("PushNode (%d,%d)", keyNodes[0].xPos, keyNodes[0].yPos);

        for (var i = 1; i < len; i++) {
            var node1 = keyNodes[i - 1];
            var node2 = keyNodes[i];
            var dist = Math.sqrt(Math.pow((node1.xPos - node2.xPos), 2) + Math.pow((node1.yPos - node2.yPos), 2));

            if (dist < stride) {
                // 忽略距离过小的点
                for (var j = i + 1; j < len; j++) {
                    node2 = keyNodes[j];
                    dist = Math.sqrt(Math.pow((node1.xPos - node2.xPos), 2) + Math.pow((node1.yPos - node2.yPos), 2));
                    if (dist >= stride) {
                        // console.info("Skip nodes from [%d] to [%d]", i, j);
                        i = j;
                        break;
                    }
                }

                // 如果最后一个点间隔也过小，保留最后一个点
                if (j == len) {
                    node2 = keyNodes[len - 1];
                }
            }

            if (dist > stride) {
                var count = Math.ceil((dist - stride) / stride);
                // console.info("add %d nodes between %d [%d,%d] and %d [%d,%d]", count, i, node1.xPos, node1.yPos, i + 1,
                //    node2.xPos, node2.yPos);
                for (var c = 1; c <= count; c++) {
                    var angle = Math.atan2(node2.yPos - node1.yPos, node2.xPos - node1.xPos);
                    var detalY = stride * Math.sin(angle) * c;
                    var detalX = stride * Math.cos(angle) * c;
                    // console.info("------add (%d,%d)", node1.xPos + detalX, node1.yPos + detalY);
                    resultNodes.push({xPos: node1.xPos + detalX, yPos: node1.yPos + detalY});
                }
            }

            resultNodes.push({xPos: node2.xPos, yPos: node2.yPos});
            // console.info("PushNode (%d,%d)", node2.xPos, node2.yPos);
        }
        // console.info("interpolate from [%d] to [%d] Points", keyNodes.length, resultNodes.length);

        return resultNodes;
    },

    //compareVersion: function (curVersion) {
    //curVersion = curVersion || "1.0.0";
    //var minClientVersion = CLIENT_VERSION.split('.');
    //var curClientVersion = curVersion.split('.');
    //if (curClientVersion.length < minClientVersion.length) {
    //    return false;
    //}
    //
    //for (var i = 0; i < minClientVersion.length; i++) {
    //    if (parseInt(curClientVersion[i]) < parseInt(minClientVersion[i])) {
    //        return false;
    //    }
    //}
    //
    //    return true;
    //},

    getKillLevel: function (level) {
        if (!level) {
            return 0;
        }

        var killCounts = TOTAL_KILL_COUNT.split(',');

        if (level > 0 && level <= killCounts.length) {
            return parseInt(killCounts[level - 1]);
        }

        return 0;
    }
};
