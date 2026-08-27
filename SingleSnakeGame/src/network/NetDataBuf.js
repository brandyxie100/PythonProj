/**
 * Created by billbao on 2016/4/22.
 */

var NetDataBuf = {
    isInit: false,     //数据是否被初始化
    isLogin: false,     //是否登录
    isSelfDead: false,      //自己是否死亡
    isTimeOver: false,      //时间是否到了
    //isNewGlobalInfo: false,     //globalinfo是否是新数据
    endTime: 0,     //结束时间
    leftTime: 0,        //剩余时间
    nickName: "",       //玩家的名字
    initFoods: [],      //初始化全量食物数据数组
    globalInfo: {},       //（PDataDef.GlobalInfo对象）全量游戏数据
    eatenFoods: [],         //(PDataDef.EatFoodInfo对象数组)被吃的食物
    snakeKillInfo: [],      //(PDataDef.SnakeKillInfo对象数组)蛇死亡数据
    radarInfo: [],      //(PDataDef.RadarInfo对象)雷达信息
    playersNum: 0,      //房间里面的游戏玩家数量
    userRankList: [],       //（PDataDef.UserRankInfo对象数组）房间里面的玩家排行数据
    myRankInfo: {},     //我的排行信息
    myRank: 1          //我的排行名次
};