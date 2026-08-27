/*  
 * Class:         mathUtils
 * Description:   Helper class for some math operations.
 * Created:       14.04.2016
 * Last change:   14.04.2016
 * Collaborators: circa94, Kogs
*/

'use strict';

module.exports = {
    getRandomInt: function (min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    },

    almostEqual: function (v1, v2, epsilon) {
        if (epsilon == null) {
            epsilon = 0.01;
        }
        return Math.abs(v1 - v2) < epsilon;
    },

    floatToFixed1: function(num) {
        return Math.round(num * 10) / 10;
    },

    floatToFixed2: function(num) {
        return Math.round(num * 100) / 100;
    }
};