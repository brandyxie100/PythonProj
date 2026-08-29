/**
 * Created by brandyxie
 * 20160405.
 */

var LAYER_DEF = {};
LAYER_DEF.BACKGROUND = 0;  //background layer
LAYER_DEF.FOOD_BALL = 1;   //food layer
LAYER_DEF.PLAYER_SNAKE_SHADE = 2;
LAYER_DEF.PLAYER_SNAKE_BODY = 3;
LAYER_DEF.PLAYER_SNAKE_SKIN = 4;
LAYER_DEF.PLAYER_SNAKE_EFFECT = 5;
LAYER_DEF.PLAYER_SNAKE_HEAD = 6;  //player snake layer
LAYER_DEF.WINDOW = 150;  //window zorder

LAYER_DEF.UI_MAINGAME_LAYER = 0;  //main game layer骢fig
LAYER_DEF.UI_LAYER = 1;  //ui layer

var mapBorder = 200; // min y
var mapRadius = 2900;
var mapSize = cc.size(mapBorder * 2 + mapRadius, mapBorder * 2 + mapRadius);

var bUseRocker = true/*cc.sys.isNative ? true : cc.sys.isMobile*/;
var ALREADY_SHOW_ACC = false;

var MAX_SPRITE_BATCH_NUM = 10; //maximum created number every time
var SPEED_DEFAULT = 210;

var ORIGINAL_ENERGY = 20;  //energy value, defined by server
var ORIGINAL_WIDTH = 26; //defined by server
var PIC_SCALE_SIZE = 100; //defined by server

var GAME_MAP_ORIGINAL_SCALE = 0.9; //the scale when games start
var GAME_MAP_SCALE = 1; //current scale

var MY_SNAKE_ID = 0;
var MY_SKIN_ID = 9;

var HALF_PAI = Math.PI * 100 / 2 * 0.01;
var REVERSE_PAI = 100 / Math.PI * 0.01;

var gGameTime = 5; //time for game room (minutes per round)

var LOGIN_REQUEST_DATA = {
    GAME_START: false,
    USER_NAME: "",
    USER_LENGTH: "",
    RANK_LIST: null
};

//game logic events define
var GameEvent = {
    GAME_EVENT_SETUP: "SETUP",
    GAME_EVENT_KICK: "KILL",
    GAME_EVENT_DEATH: "DEATH",
    GAME_EVENT_CONNECT: "CONNECT",
    GAME_EVENT_DISCONNECT: "DISCONNECT"
};

GameEvent.CallFunc = function (func, caller) {
    return function () {
        func.apply(caller, arguments);
    }
};
