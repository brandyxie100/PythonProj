/**
 * Created by alexgan on 2016/5/5.
 */

module.exports = {
    /* 地图配置 */
    "map-size": 6000,             // 地图长宽
    "map-radius": 2800,           // 地图半径
    "map-border": 200,            // 地图边界
    "view-radius": 520,           // 默认视野
    "born-area": 1500,            // 蛇出生范围(按地图中心点计算的正方形)
    "food-area": 2600,            // 食物刷新半径(以地图中心点计算的圆)
    "food-block-num": 100,        // 地图食物区块(N*N)
    "max-player-num": 60,         // 如果房间达到此人数，通知前端重新选房间

    /* 食物配置 */
    "food-colors": 23,            // 食物颜色数量
    "food-size": [0.5, 0.6],      // 死亡食物随机大小范围(乘以蛇的宽度)
    "food-gap-rat": 1.2,          // 死亡食物间距比率(乘以蛇的宽度)
    "food-pos-offset": 20,        // 死亡食物位置偏移(正负范围随机)
    "food-depreciate": 1,         // 死亡食物能量点折损率(乘以蛇的能量值)
    "start-normal-food": 350,     // 普通食物初始个数（成长型和非成长型）
    "max-normal-food": 400,       // 普通食物最大个数（成长型和非成长型）
    "growing-food-portion": 0.65, // 普通食物成长型能量点的占比
    "start-movable-food": 6,      // 移动食物初始个数

    /* 蛇的配置 */
    "snake_speed": 390,           // 蛇的初始移动速度
    "snake-length": 126,          // 蛇的初始长度
    "snake-width": 30,            // 蛇的初始宽度
    "snake-energy": 10,           // 蛇的初始能量值
    "snake-nodes": 15,            // 蛇的初始节点数
    "accel-energy": 20,           // 蛇加速需要能量值
    "energy-dec": 10,             // 加速状态下，能量每秒减少多少点
    "view-offset": 60,            // 视野扩展值
    "snake-skinId": 8,            // 蛇皮肤ID随机范围

    /* 碰撞相关 */
    "snake-head-extra-size": 25,    // 蛇头增加的热区大小
    "move-food-extra-size": 200,    // 移动型食物判断距离
    "snake-born-god-time": 2.8,       // 蛇出生之后无敌时间(秒)

    /* AI */
    "robot-snake-max-count": 22,    // 在蛇总数小于该值的时候才会生成AI蛇
    "robot-snake-rotate-time": 2,   // AI蛇转向的平均间隔(秒)，即平均几秒AI蛇会随机转弯
    "robot-snake-find-food": 0.5,   // AI蛇找食物的平均间隔(秒)
    "robot-live-range": 2500,       // AI蛇活动范围(距离地图中心点的半径)

    /* 公告板 */
    "multi_kill_time": 9000,       // 连续击杀时间间隔(毫秒)
    "multi_kill_count": 2,          // 连续击杀次数要求(最低次数要求)
    "total_kill_count": "100,200,300,400,500,600", // 单局杀戮次数累计

    /* 杂项 */
    "frame": 30,
    "client-version": "2.0.0",

    /* AI 昵称 */
    "AI_NAME": ['尼古拉赵四', '麻辣小龙侠', '二侠', 'fatfour', '坑爹娃', '多边形杀手', '钢弹', '愤怒的白条', 'patton', 'hmm', '大杀特杀', '阿迪达斯', '宝马740', '眼前的苟且', '可口可乐', '城会玩', '营养快线', '一起污', '撩妹王', '东莞一条龙', '我的天坑', '起来嗨', '在下坂本', '你咋不上天', '风骚小秘书', '送一血', '同老板', 'tomson', '军长', '暴力龙', '艾利克斯●干', '一万元', '布兰迪●谢', '阿童木', '一哥老撸', '奎爷', '摄影师乔', '昵称太长', '古月君', '忘了叔', '羔羊', '奶爸', '大瑾', '水哥', '猫王', '廖大师', '前卫男', 'alibaba', '弟子囧', 'ponymama', 'πboy', '宋价格', '于布斯', '爱疯随苦力', 'miwa哇', '菲比陈', 'bbbbbb', '牛油果', '脸谱', '日川钢板', '爱新觉罗', '路易十四']
};
