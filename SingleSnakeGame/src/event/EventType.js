/**
 * Created by billbao on 2016/4/21.
 */

var CEventType = {
    NONE: "none",
    INIT_GAME: "INIT_GAME",     //初始化游戏（登陆以后返回的消息）
    SNAKE_REVIVE: "SNAKE_REVIVE",       //蛇复活
    UPDATE_GLOBAL_INFO: "UPDATE_GLOBAL_INFO",       //更新全量游戏信息
    UPDATE_EAT_FOOD: "UPDATE_EAT_FOOD",         //更新被吃食物
    UPDATE_RANK: "UPDATE_RANK",         //更新房间排行榜
    UPDATE_SELF_RANK: "UPDATE_SELF_RANK",       //更新自己的排行
    UPDATE_SNAKE_DEATH: "UPDATE_SNAKE_DEATH",       //更新蛇死亡信息
    UPDATE_SNAKE_SUICIDE: "UPDATE_SNAKE_SUICIDE",    //更新蛇撞墙
    UPDATE_RADAR_INFO: "UPDATE_RADAR_INFO",     //更新雷达信息
    NET_WORK_ERR: "NET_WORK_ERR",        //网络出错
    SENSITIVE_NICK_NAME: "SENSITIVE_NICK_NAME",       //敏感名字
    TIME_OVER: "TIME_OVER",         //时间到
    REFRESH_NET_STATISTICS: "REFRESH_NET_STATISTICS", //刷新网络数据统计
    RESIZE_WINDOW: "RESIZE_WINDOW",         //窗口改变
    ON_START_ACCELERATE: "ON_START_ACCELERATE",       //开始加速
    ON_END_ACCELERATE: "ON_END_ACCELERATE",           //结束加速
    ON_ACC_BTN_NOTICE: "ON_ACC_BTN_NOTICE",           //按钮可以加速提示
    EXCEED_FRIEND_NOTICE: "EXCEED_FRIEND_NOTICE",     //超越提示
    ON_START_GAME_EVENT:"ON_START_GAME_EVENT",        //开始游戏请求

    ON_SNAKES_MOVE: "on_snake_move",  //蛇移动
    ON_SNAKE_RECOVERY: "on_snake_recovery" //game restart
};