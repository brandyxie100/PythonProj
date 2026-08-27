/**
 * Created by malloyzhu on 2016/4/21.
 */

var FoodLayer = cc.Layer.extend({
    _foodViewBatchNode: null,
    _mapSize: null,
    _foodPool: null,
    _movableFoodPool: null,
    _colorList: null,
    _listenerList: null,
    _opacityIncrement: null,
    _foodPoolCount: 15,
    _movableFoodPoolCount: 5,
    _foodInViewPortMap: null,
    _movableFoodInViewPortMap: null,
    _minOpacity: 76,
    _maxOpacity: 255,

    ctor: function (mapSize) {
        this._super();

        this._foodPool = [];
        this._movableFoodPool = [];
        this._colorList = [];
        this._listenerList = [];
        this._foodInViewPortMap = {};
        this._movableFoodInViewPortMap = {};
        this._opacityIncrement = (this._maxOpacity - this._minOpacity) / (35 * 0.5); //frameCount * changeTime

        this._mapSize = mapSize;
        this.setContentSize(mapSize);

        this._foodViewBatchNode = new cc.SpriteBatchNode(res.food_png, this._foodPoolCount * 4);
        this.addChild(this._foodViewBatchNode);

        this._initColorList();
        this._initFoodPool();
        this._initViewPortFoodList();
    },

    _initViewPortFoodList: function () {
        var foodsData = dataManager.getInitFoods();//当前视野食物数据，由登录时服务器返回
        for (var i in foodsData) {
            this._pushToFoodInViewPortList(foodsData[i]);
        }
    },

    onEnter: function () {
        this._super();
        Util.registerListener(this._listenerList, CEventType.UPDATE_GLOBAL_INFO, this._onUpdateServerInfo.bind(this));
        Util.registerListener(this._listenerList, CEventType.UPDATE_EAT_FOOD, this._onFoodsEaten.bind(this));
        Util.registerListener(this._listenerList, CEventType.SNAKE_REVIVE, this._onSnakeRevive.bind(this));
    },

    _onSnakeRevive: function () {
        for (var i in this._foodInViewPortMap) {
            this._pushToFoodPool(this._foodInViewPortMap[i]);
        }

        this._foodInViewPortMap = {};
        var foodsData = dataManager.getInitFoods();//当前视野食物数据
        for (var i in foodsData) {
            this._pushToFoodInViewPortList(foodsData[i]);
        }
    },

    _pushToFoodInViewPortList: function (foodData) {
        if (foodData.foodType == PDataDef.FoodType.movable) {
            return;
        }

        var food = this._foodPool.pop();
        if (null == food) {
            food = this._createFood();
            this.addChild(food);
        }

        food.updateFoodStructure(foodData, this._colorList);
        food.updateVisible(true);
        food.updateScale();
        food.updateOpacity();
        food.updatePosition();
        food.updateColor();
        this._foodInViewPortMap[food.getId()] = food;
        return food;
    },

    onExit: function () {
        this._super();
        Util.unRegisterListeners(this._listenerList);
    },

    _onFoodsEaten: function () {
        var eatenFoods = dataManager.getEatenFoods();
        for (var i in eatenFoods) {
            var snakeId = eatenFoods[i].snakeId;
            var foodIdList = eatenFoods[i].eatFoods;
            this._eatFood(snakeId, foodIdList);

            //I eat food here
            if (MY_SNAKE_ID != snakeId /*&& foodIdList.length > 1*/) {
                continue;
            }
            MusicManager.playEffect(MusicEffectFiles.Audio_eat);

            //send notice message
            var data = dataManager.getMainPlayerData();
            var energy = data.energy;
            //notice guide
            if (ALREADY_SHOW_ACC) {
                return;
            }
            if (energy > 22) {
                var time = 3.5;
                playerManager.notifyCanAcc(time);

                ALREADY_SHOW_ACC = true;
            }
        }
    },

    _eatFood: function (snakeId, foodIdList) {
        var snakePosition = playerManager.getPlayerPositionByID(snakeId);
        var foodId;
        var food;
        for (var j in foodIdList) {
            foodId = foodIdList[j];
            food = this._foodInViewPortMap[foodId];
            if (null != food) {
                food.eaten(snakePosition || food.getPosition());
                delete this._foodInViewPortMap[foodId];
            } else {
                food = this._movableFoodInViewPortMap[foodId];
                if (null != food) {
                    food.eaten(snakePosition || food.getPosition());
                    this._removeFromMovableFoodPool(food);
                    delete this._movableFoodInViewPortMap[foodId];
                }
            }
        }
    },

    _removeFromMovableFoodPool: function (food) {
        for (var i in this._movableFoodPool) {
            if (this._movableFoodPool[i] == food) {
                this._movableFoodPool.splice(i, 1);
                return;
            }
        }
    },

    _initColorList: function () {
        var foodColorConfigs = ConfigLoader.getFoodColorConfigs();
        for (var i in foodColorConfigs) {
            this._colorList.push(cc.hexToColor(foodColorConfigs[i].color));
        }
    },

    _initFoodPool: function () {
        for (var i = 0; i < this._foodPoolCount; i++) {
            var food = this._createFood();
            this.addChild(food);
            this._pushToFoodPool(food);
        }

        for (var i = 0; i < this._movableFoodPoolCount; i++) {
            var food = this._createMovableFood();
            this.addChild(food);
            this._pushToFoodPool(food);
        }
    },

    _pushToFoodPool: function (food) {
        food.updateVisible(false);
        if (food.getType() != PDataDef.FoodType.movable) {
            this._foodPool.push(food);
        } else {
            this._movableFoodPool.push(food);
        }
    },

    _createFood: function () {
        var foodStructure = this._createDefaultFoodStructure();
        var food = new Food(foodStructure, this._foodViewBatchNode);
        food.setOpacityIncrement(this._opacityIncrement);
        food.setMaxOpacity(this._maxOpacity);
        food.setMinOpacity(this._minOpacity);
        food.setEatenActionCompleteCallBack(this._onEatenActionComplete.bind(this));
        food.finish();
        return food;
    },

    _createMovableFood: function () {
        var foodStructure = this._createDefaultFoodStructure();
        var food = new MovableFood(foodStructure, this._foodViewBatchNode);
        food.setType(PDataDef.FoodType.movable);
        food.setOpacityIncrement(this._opacityIncrement);
        food.setMaxOpacity(this._maxOpacity);
        food.setMinOpacity(this._minOpacity);
        food.setEatenActionCompleteCallBack(this._onEatenActionComplete.bind(this));
        food.finish();
        return food;
    },

    _onEatenActionComplete: function (food) {
        this._pushToFoodPool(food);
    },

    _onUpdateServerInfo: function () {
        //var time = Date.now();
        //计算视野大小
        var centerPosition;
        if (playerManager.getMainPlayer()) {
            centerPosition = playerManager.getViewPointPos();
            this._lastCenterPos = centerPosition;
        } else {
            centerPosition = this._lastCenterPos;
        }
        var offset = 60;
        var width = cc.winSize.width / GAME_MAP_SCALE;
        var height = cc.winSize.height / GAME_MAP_SCALE;
        var x = centerPosition.x - width / 2 - offset;
        var y = centerPosition.y - height / 2 - offset;
        var viewPort = cc.rect(x, y, width + offset * 2, height + offset * 2);

        //裁剪非移动型食物
        var food;
        var foodPos;
        var delNow;
        var dis = Math.round(20 / GAME_MAP_SCALE);
        for (var i in this._foodInViewPortMap) {
            //在屏幕中，只更新透明度
            food = this._foodInViewPortMap[i];
            foodPos = food.getPosition();
            //如果是尸体食物而且离蛇头很近那么直接删除
            delNow = false;
            if (Math.abs(foodPos.x - centerPosition.x) < dis && Math.abs(foodPos.y - centerPosition.y) < dis) {
                delNow = true;
            }
            if (cc.rectContainsPoint(viewPort, foodPos) && !delNow) {
                food.updateOpacity();
            } else {
                this._pushToFoodPool(food);
                delete this._foodInViewPortMap[i];
            }
        }

        //从增量数据中过滤相同id的食物，筛选出移动型食物数据，并将非移动型食物加到视野中
        var moveTypeFoodsData = [];
        var incrementFoodsDataInViewPort = dataManager.getFoods();
        for (var i = 0, len = incrementFoodsDataInViewPort.length; i < len; i++) {
            //过滤掉相同id的食物
            var bExist = false;
            var foodData = incrementFoodsDataInViewPort[i];
            if (foodData.foodType != PDataDef.FoodType.movable) {
                var food = this._foodInViewPortMap[foodData.foodId];
                if (null != food) {
                    bExist = true;
                    console.log("repeat foodId : " + food.getId());
                }
            }
            if (bExist) {
                continue;
            }

            if (foodData.foodType != PDataDef.FoodType.movable) {
                this._pushToFoodInViewPortList(foodData);
            } else {
                moveTypeFoodsData.push(foodData);
            }
        }

        this._movableFoodInViewPortMap = {};
        var i = 0;
        for (; i < moveTypeFoodsData.length; i++) {
            var food = this._movableFoodPool[i];
            if (null == food) {
                food = this._createMovableFood();
                this.addChild(food);
                this._movableFoodPool.push(food);
            }
            food.updateFoodStructure(moveTypeFoodsData[i], this._colorList);
            food.updateVisible(true);
            food.updateScale();
            food.updateOpacity();
            food.updateColor();
            food.updatePosition();
            this._movableFoodInViewPortMap[food.getId()] = food;
        }

        for (; i < this._movableFoodPool.length; i++) {
            this._movableFoodPool[i] && this._movableFoodPool[i].updateVisible(false);
        }
        //console.log("food update server: cost time= " + (Date.now() - time));
    },

    _createDefaultFoodStructure: function () {
        return new FoodStructure(0, 5, null, 0, 0, 0, 0);
    }
});
