/**
 * Created by billbao on 2015/7/14.
 */


var GameCommonDef = {};


GameCommonDef.DESIGN_RESOLUTION_SIZE = cc.size(1334, 750);
GameCommonDef.RESOLUTION_POLICY = cc.ResolutionPolicy.FIXED_HEIGHT;
GameCommonDef.lastFrameSize = cc.size(0, 0);
GameCommonDef.orientation = 0;      //0表示横屏，1表示竖屏


//Layer的ZOrder定义
GameCommonDef.LAYER_Z_ORDER_BG = 0;     //背景层
GameCommonDef.LAYER_Z_ORDER_MAIN_UI = 5;      //主界面ui
GameCommonDef.LAYER_Z_ORDER_EFFECT = 60;    //特效层
GameCommonDef.LAYER_Z_ORDER_POP_UP = 101;      //弹出框ui

GameCommonDef.LAYER_Z_ORDER_WINDOW_MASK = 106;
GameCommonDef.LAYER_Z_ORDER_TIP_UI = 107;      //浮窗ui

