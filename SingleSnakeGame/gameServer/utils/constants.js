/*  
 * Class:         Constants
 * Description:   Just an collection of some constant values like max values and packet types.
 * Created:       13.04.2016
 * Last change:   14.04.2016
 * Collaborators: circa94, Kogs
 */

'use strict';

const INT24MAX = 16777215;
const INT16MAX = 65535;
const INT8MAX = 255;

module.exports = {
    INT24MAX: INT24MAX,
    INT16MAX: INT16MAX,
    INT8MAX: INT8MAX,

    MessageType: {
        // client->server (request)
        PING_REQUEST: 1,
        LOGIN_REQUEST: 2,
        MOVE_SNAKE: 3,
        CHANGE_SNAKE_SPEED: 4,

        // server->client (response)
        PING_RESPONSE: 101,
        LOGIN_RESPONSE: 102,
        REVIVE_RESPONSE: 103,
        ERROR_RESPONSE: 104,

        // server->client (push)
        UPDATE_RANK_LIST: 201,
        UPDATE_GLOBAL_INFO: 202,
        UPDATE_EAT_FOOD: 203,
        UPDATE_SNAKE_DEATH: 204,
        UPDATE_SNAKE_SUICIDE: 205,
        TIME_OVER: 206,
        UPDATE_RADAR_INFO: 207,
        UPDATE_INCREMENT_INFO: 208,
        UPDATE_SELF_RANK: 209,
        UPDATE_CALL_BOARD: 210
    },

    ErrorCode: {
        VERSION_TOO_LOW: 1,
        INVALID_NICK_NAME: 2,
        ROOM_IS_FULL: 3,
        PLATFORM_NOT_SUPPORT: 4
    },

    StatusFlag: {
        STATUS_ACCELERATE: 0,
        STATUS_PROTECTION: 1
    },

    PlatformType: {
        PURE_IOS: 1,
        PURE_ANDROID: 2,
        MIAOWAN_IOS: 3,
        MIAOWAN_ANDROID: 4,
        PC_WEB: 5,
        MOBILE_WEB: 6
    },

    BoardInfoType: {
        KILL_TOP_THREE: 1,
        MULTI_KILL: 2,
        TOTAL_KILL: 3,
        REVENGE_KILL: 4
    },

    BoardTopKill: {
        KILL_FIRST: 1,
        KILL_SECOND: 2,
        KILL_THIRD: 3
    },

    BoardTotalKill: {
        DA_SHA_TE_SHA: 1,
        JIE_JIN_BAO_ZOU: 2,
        WU_REN_KE_DANG: 3,
        ZHU_ZAI_BI_SAI: 4,
        JIE_JIN_SHEN_LE: 5,
        CAO_SHEN: 6
    }
};