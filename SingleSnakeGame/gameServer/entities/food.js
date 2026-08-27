/*  
 * Class:         Food
 * Description:   Entity class for food in the game
 * Created:       15.04.2016
 * Last change:   15.04.2016
 * Collaborators: circa94
 */
'use strict';
var food_id = 1;

class Food {
    constructor(type, x, y, radius, color, energy) {
        this.foodId = food_id;
        food_id += 2;
        this.foodType = type;
        this.radius = radius;
        this.color = color;
        this.energy = energy;
        this.velocity = {x: 0, y: 0};
        this.position = {xPos: x, yPos: y};
    }
}
;


Food.Type = {
    BASIC: 1,           // 基础型
    GROWING: 2,         // 基础成长型
    MOVABLE: 3,         // 移动AI食物
    AFTER_SPEEDUP: 4,   // 加速后残留
    AFTER_DEAD: 5       // 死亡后残留
};

Food.resetId = function () {
    food_id = 1;
};

module.exports = Food;
