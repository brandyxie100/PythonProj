/**
 * 20160329
 * created by brandyxie
 */

var Snake = cc.Node.extend({
    _id: 0,
    _skinID: 0,
    _name: null,
    _headPos: null,
    _direction: null,
    _radius: 0,
    _angle: 0,
    _isAccState: false,
    //_opacity: 255,
    _bodyColor: null,
    _lightColor: null,
    _scale: null,
    _isDied: null,
    _protectState: null,
    _isPlaying: null,
    _animatNode: null,
    _isAngryState: false,

    _header: null,
    _headerAngry: null,
    _nameCtrl: null,
    _tailSprite: null,
    _effectLine: null,
    _shadeLine: null,
    _drawArray: null,
    _drawCircleArray: null,
    _bodySkinBatchNode: null,
    _headFaceBatchNode: null,
    skinTrangleRes: null,
    skinCircleRes: null,

    _cacheBodyPoints: null,
    _useAnti: false,
    _skinID: 0,

    _speedX: 0,
    _speedY: 0,

    ctor: function () {
        this._super();

        this._headPos = cc.p(0, 0);
        this._direction = cc.p(0, 0);
        this._cacheBodyPoints = [];
        this._drawArray = [];
        this._drawCircleArray = [];
        this._isDied = false;
        this._isAnimPlayed = false;
        this._isAnimPlaying = false;

        //create body draw
        this._effectLine = new cc.DrawNode();
        this._shadeLine = new cc.DrawNode();
        this.addChild(this._effectLine, LAYER_DEF.PLAYER_SNAKE_EFFECT);
        this.addChild(this._shadeLine, LAYER_DEF.PLAYER_SNAKE_SHADE);

        //add name control
        this._nameCtrl = new ccui.Text();
        this._nameCtrl.setFontSize(18);
        this._nameCtrl.setFontName("Arial Bold");
        this._nameCtrl.setColor(cc.color(255, 255, 255, 250));
        this._nameCtrl.setAnchorPoint(0.5, 0.5);
        this._nameCtrl.setPosition(-60, -80);
        this._nameCtrl.ignoreContentAdaptWithSize(true);
        this.addChild(this._nameCtrl, LAYER_DEF.FOOD_BALL);

        //create sprite batch for body skin
        this._bodySkinBatchNode = new cc.SpriteBatchNode(res.snake_png);
        this.addChild(this._bodySkinBatchNode, LAYER_DEF.PLAYER_SNAKE_BODY);
        this._bodySkinBatchNode.setAnchorPoint(0.5, 0.5);
        this._bodySkinBatchNode.setPosition(0, 0);

        //create light point
        //this._tailSprite = new cc.Sprite();
        //this._tailSprite.setAnchorPoint(0.5, 0.5);
        //this._tailSprite.initWithSpriteFrameName("tail_9.png");
        //this._bodySkinBatchNode.addChild(this._tailSprite, LAYER_DEF.PLAYER_SNAKE_EFFECT);
        //if (cc.sys.isNative || cc._renderType === cc.game.RENDER_TYPE_WEBGL) {
        //    console.log("cc._renderType === cc.game.RENDER_TYPE_WEBGL");
        //    var texture = this._bodySkinBatchNode.getTexture();
        //    texture.setAliasTexParameters();
        //}
        //gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        //gl.enable(gl.BLEND);
        //this._bodyDrawNode.setBlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

        //设置抗锯齿属性
        //this._texture = cc.textureCache.addImage(fileImage);
        //this._texture.setAliasTexParameters();

        //是否是低配置
        //var isLowConfig = false;
        //this.mFPSCount++;
        //this.lowFPSCount;
        //var fps = cc.director.getAnimationInterval();
        //if (fps < 19) {
        //    this.lowFPSCount++;
        //}
        //if (this.mFPSCount >= 200) { //about 6 seconds
        //    if (this.lowFPSCount > 100) {
        //        isLowConfig = true;
        //    }
        //
        //    this.mFPSCount = 0; // Reset
        //    this.lowFPSCount = 0; // Reset
        //}

        //if (cc.sys.os === cc.sys.OS_IOS || cc._renderType !== cc.game.RENDER_TYPE_CANVAS) {
        this._useAnti = true;
        //console.log("cc._renderType !== cc.game.RENDER_TYPE_CANVAS");
        //} else {
        //    this._useAnti = false;
        //console.log("cc._renderType == cc.game.RENDER_TYPE_CANVAS");
        //}
    },

    destroy: function () {
        //cc.director.getScheduler().unschedule(this.animateFadeOut, this);
        if (this._eyesR) {
            this._eyesR.release();
        }
        if (this._eyesL) {
            this._eyesL.release();
        }
        if (this._drawArray) {
            for (var i in this._drawArray) {
                this._drawArray[i].removeFromParent(true);
            }
        }
        if (this._drawCircleArray) {
            for (var i in this._drawCircleArray) {
                this._drawCircleArray[i].removeFromParent(true);
            }
        }
        if (this._shadeLine) {
            this._shadeLine.removeFromParent(true);
        }
        if (this._effectLine) {
            this._effectLine.clear();
            this._effectLine.removeFromParent(true);
        }
        if (this._nameCtrl) {
            this._nameCtrl.removeFromParent(true);
        }
        if (this._bodySkinBatchNode) {
            this._bodySkinBatchNode.removeAllChildren(true);
            this._bodySkinBatchNode.removeFromParent(true);
        }

        this._drawArray = null;
        this._drawCircleArray = null;
        this._effectLine = null;
        this._shadeLine = null;
        this._nameCtrl = null;
        this._bodySkinBatchNode = null;
    },

    setPlayerData: function (data) {
        if (0 == data.increment) {
            this._skinID = data.skinId;
            this._name = data.name;
        }
        if (data.width) {
            this._radius = data.width;
        }
        if (data.energy) {
            this._energy = data.energy;
        }
        this._id = data.snakeId;
        this._headPos.x = data.bodyPoints[0].xPos;
        this._headPos.y = data.bodyPoints[0].yPos;
        this._direction.x = data.dirPos.xPos;
        this._direction.y = data.dirPos.yPos;

        this._protectState = data.statusFlag & 2; //0 for no protect, 1 for yes
        if (this._isAccState && this._energy < ORIGINAL_ENERGY) {
            this.onAccelerateEnd();
        }
        this._isAccState = data.statusFlag & 1;
    },

    //create snake head
    addSnakeHead: function (skinID) {
        //update data
        this._angle = (-90 - Math.round(Math.atan2(this._direction.y, this._direction.x) * 180 / Math.PI)); //-90 for x ->
        this._scale = Math.round(this._radius * 100 / PIC_SCALE_SIZE) * 0.01; //PIC_SCALE_SIZE is real width of png

        var index = (skinID % 3) + 1;
        var indexAngry = 100;
        //add new skin
        if (skinID > 8) {
            index = skinID;
            indexAngry = 100 + skinID - 8;
        }
        var headRes = "Face_" + index + ".png";
        var headResAngry = "Face_" + indexAngry + ".png";
        var spriteAngry = new cc.Sprite();
        spriteAngry.initWithSpriteFrameName(headResAngry);
        spriteAngry.setAnchorPoint(0.5, 0.5);
        this._headerAngry = spriteAngry;
        playerManager.addSpriteToBatch(this._headerAngry);

        var sprite = new cc.Sprite();
        sprite.initWithSpriteFrameName(headRes);
        sprite.setAnchorPoint(0.5, 0.5);
        this._header = sprite;
        playerManager.addSpriteToBatch(this._header);

        //set head face position
        var viewPos = playerManager.getViewPointPos();
        this._header.setPosition(this._headPos.x - viewPos.x, this._headPos.y - viewPos.y);
        this._headerAngry.setPosition(this._headPos.x - viewPos.x, this._headPos.y - viewPos.y);

        //add new skin tail
        if (skinID > 8) {
            var tailRes = "tail_" + skinID + ".png";
            this._tailSprite = new cc.Sprite();
            this._tailSprite.setAnchorPoint(0.5, 0.5);
            this._tailSprite.initWithSpriteFrameName(tailRes);
            this._bodySkinBatchNode.addChild(this._tailSprite, LAYER_DEF.PLAYER_SNAKE_EFFECT);
        } else {
            //add eyes
            var eyeRes = "eye.png";
            this._eyesR = new cc.Sprite();
            this._eyesR.initWithSpriteFrameName(eyeRes);
            this._eyesR.setAnchorPoint(0.5, 0.5);
            this._header.addChild(this._eyesR);
            this._eyesL = new cc.Sprite();
            this._eyesL.initWithSpriteFrameName(eyeRes);
            this._eyesL.setAnchorPoint(0.5, 0.5);
            this._header.addChild(this._eyesL);
            this._eyesR.retain();
            this._eyesL.retain();
        }
        this._isAngryState = true; //need fresh at first
        this.setEyesIsAngry(false);

        //add name
        if (this._id == MY_SNAKE_ID) {
            this._name = LOGIN_REQUEST_DATA.USER_NAME;
        } else {
            //modify name here
            var rand = Math.round(cc.random0To1() * 10) % 3; //30%
            var len = LOGIN_REQUEST_DATA.RANK_LIST.length;
            if (0 == rand && len > 1) {
                rand = Math.floor(cc.random0To1() * 200 % len);
                var tmp = LOGIN_REQUEST_DATA.RANK_LIST[rand];
                if (tmp.nickName != LOGIN_REQUEST_DATA.USER_NAME) {
                    this._name = tmp.nickName;
                }
            }
        }
        if (this._name && this._name.length > 0) {
            this._nameCtrl.setString(this._name);
        }

        this._accOpacity = 255;
        //this._opacity = 0;
        //this._addDie = 40;
    },

    createSnakeSkinNode: function (skinTrangleRes, skinCircleRes, addNum) {
        var sprite = null;
        for (var i = 0; i < addNum; ++i) {
            //add circles
            //cannot hide sprite here, or some part of body will be invisible
            sprite = new cc.Sprite();
            sprite.initWithSpriteFrameName(skinCircleRes);
            sprite.setScale(this._scale);
            sprite.setAnchorPoint(0.5, 0.5);

            this._drawCircleArray.unshift(sprite); //add to head for higher level
            this._bodySkinBatchNode.addChild(sprite, LAYER_DEF.PLAYER_SNAKE_SKIN);

            //add rectangle skin
            sprite = new cc.Sprite();
            sprite.initWithSpriteFrameName(skinTrangleRes);
            sprite.setScale(this._scale);
            sprite.setAnchorPoint(0, 0.5);
            this._drawArray.unshift(sprite);
            this._bodySkinBatchNode.addChild(sprite, LAYER_DEF.PLAYER_SNAKE_SKIN);
        }
    },

    //create snake body
    createSnake: function (data) {
        //var startTime = Date.now();
        //save whole data
        this.setPlayerData(data);
        //set snake position
        this.setPosition(this._headPos);

        var skinID = 1;
        if (this._id == MY_SNAKE_ID) {
            if (cc._renderType === cc.game.RENDER_TYPE_WEBGL) {
                skinID = 9 + Math.round(Math.random() * 10) % 2; //default skin for myself
            } else {
                skinID = 10;
            }
        } else if (data.skinId) {
            skinID = data.skinId;
        }
        switch (skinID) {
            case 1: //red
                this._bodyColor = cc.color(251, 151, 127, 255);
                this._lightColor = cc.color(255, 197, 183, 255);
                break;
            case 2: //yellow
                this._bodyColor = cc.color(244, 219, 88, 255);
                this._lightColor = cc.color(251, 255, 127, 255);
                break;
            case 3: //green
                this._bodyColor = cc.color(124, 199, 48, 255);
                this._lightColor = cc.color(186, 255, 105, 255);
                break;
            case 4: //purple
                this._bodyColor = cc.color(182, 123, 225, 255);
                this._lightColor = cc.color(229, 179, 255, 255);
                break;
            case 5: //blue blue
                this._bodyColor = cc.color(104, 230, 214, 255);
                this._lightColor = cc.color(168, 247, 242, 255);
                break;
            case 6: //orange
                this._bodyColor = cc.color(243, 199, 114, 255);
                this._lightColor = cc.color(251, 236, 175, 255);
                break;
            case 7: //white blue
                this._bodyColor = cc.color(157, 183, 245, 255);
                this._lightColor = cc.color(207, 223, 251, 255);
                break;
            case 8: //sky blue
                this._bodyColor = cc.color(168, 247, 242, 255);
                this._lightColor = cc.color(83, 210, 236, 255);
                break;
            case 9: //Rosy brown
                this._bodyColor = cc.color(128, 128, 128, 255);
                this._lightColor = cc.color(255, 228, 225, 255);
                break;
            case 10: //white
                this._bodyColor = cc.color(250, 250, 250, 255);
                this._lightColor = cc.color(255, 228, 225, 255);
                break;
            default : //red
                this._bodyColor = cc.color(251, 151, 127, 255);
                this._lightColor = cc.color(255, 197, 183, 255);
                break;
        }
        //add snake head
        this._skinID = skinID;
        this.addSnakeHead(skinID);

        //create body skin
        this.skinTrangleRes = "skin_t_" + skinID + ".png";
        this.skinCircleRes = "skin_r_" + skinID + ".png";
        //create snake body
        var length = data.bodyPoints.length - 1;
        length = length > MAX_SPRITE_BATCH_NUM ? MAX_SPRITE_BATCH_NUM : length;
        this.createSnakeSkinNode(this.skinTrangleRes, this.skinCircleRes, length);

        //save body points
        var bodyPos;
        this._cacheBodyPoints.splice(0);
        for (var i in data.bodyPoints) {
            bodyPos = data.bodyPoints[i];
            this._cacheBodyPoints.push(cc.p(bodyPos.xPos, bodyPos.yPos));
        }

        //var time = (Date.now() - this._startTime);
        //if (time > 4) {
        //    console.log("createSnake length: " + length);
        //    console.log("createSnake use time is: " + time + "ms");
        //}
    },

    updateSnakePos: function (data) {
        this._startTime = Date.now();
        if (this._isDied || !this.isVisible()) {
            return;
        }
        //use increment data or not
        this.setPlayerData(data);

        //update head
        this.updateSnakeHead();

        var newLength = data.bodyPoints.length; //node number
        var index = newLength - 1;
        if (this._animatNode) {
            //set the last body point
            var localPos = cc.p(data.bodyPoints[index].xPos - this._headPos.x, data.bodyPoints[index].yPos - this._headPos.y);
            //set the first body point
            var headLocal = cc.p(data.bodyPoints[0].xPos - this._headPos.x, data.bodyPoints[0].yPos - this._headPos.y);

            this._animatNode.setPosition((localPos.x * 0.9 + headLocal.x) / 2, (localPos.y * 0.9 + headLocal.y) / 2);
        }

        //update whole data
        if (0 == data.increment) {
            var bodyPos;
            this._cacheBodyPoints.splice(0);
            for (var i in data.bodyPoints) {
                bodyPos = data.bodyPoints[i];
                this._cacheBodyPoints.push(cc.p(bodyPos.xPos, bodyPos.yPos));
                //console.log("this._cacheBodyPoints.push");
            }

            this.updateSnakeBody(this._cacheBodyPoints);
        }
        else {
            //update increase data
            this.updateCacheBodyPoints(data);
        }

        //var time = (Date.now() - this._startTime);
        //if (time > 7) {
        //console.log("updateSnakeBody: total use time is: " + time + "ms");
        //}
    },

    updateCacheBodyPoints: function (dataIncr) {
        var num = dataIncr.bodyPoints.length; //node number

        //only need update head and tail
        var headNode = dataIncr.bodyPoints[0];
        var tailNode = dataIncr.bodyPoints[num - 1];

        //update the first node
        var currNodePos = cc.p(headNode.xPos, headNode.yPos);
        var addNum = headNode.addNode;
        if (addNum > 0) { //need add new
            //console.log("headNode.addNode = " + addNum);
            this._cacheBodyPoints.unshift(currNodePos);
        }
        else //just update position
        {
            this._cacheBodyPoints.splice(0, 1, currNodePos);
        }

        //update the tail node
        currNodePos = cc.p(tailNode.xPos, tailNode.yPos);
        addNum = tailNode.addNode;
        if (addNum < 0) { //need delete the old one
            //console.log("tailNode.addNode = " + addNum);
            addNum = -addNum;
            for (var i = 0; i < addNum; ++i) {
                this._cacheBodyPoints.pop();
            }
        }
        var length = this._cacheBodyPoints.length;
        this._cacheBodyPoints.splice(length - 1, 1, currNodePos);
        //console.log("cacheBodyPoints.length = " + length);

        //if there is a error
        if ((length <= 3) && (length != dataIncr.increment)) { //need be fixed later
            this._cacheBodyPoints.splice(0);
            var pos = null;
            var len = dataIncr.bodyPoints.length;
            for (var i = 0; i < len; ++i) {
                pos = dataIncr.bodyPoints[i];
                this._cacheBodyPoints.push(cc.p(pos.xPos, pos.yPos));
            }
            //console.log("ERROR:: current key num = " + dataIncr.increment);
            console.log("ERROR:: localKeyNum != serverkeyNum ********************");
        }

        //redraw body
        this.updateSnakeBody(this._cacheBodyPoints);
    },

    updateSnakeBody: function (bodyPointArray) {
        //this._startTime = Date.now();

        //count some points of snake body
        var newLength = bodyPointArray.length; //node number
        var len = this._drawCircleArray.length;
        var addSpriteNum = newLength - len;
        if (addSpriteNum > 0) { //create new sprite
            addSpriteNum = addSpriteNum > MAX_SPRITE_BATCH_NUM ? MAX_SPRITE_BATCH_NUM : addSpriteNum;
            this.createSnakeSkinNode(this.skinTrangleRes, this.skinCircleRes, addSpriteNum);

            //console.log("updateSnakeBody: addSpriteNum = " + addSpriteNum);
        } else if (addSpriteNum < 0) {
            var circle = null;
            for (var i = newLength - 1; i < len; ++i) {
                circle = this._drawCircleArray[i];
                if (circle.isVisible()) {
                    this._drawCircleArray[i].setVisible(false);
                    this._drawArray[i].setVisible(false);
                } else {
                    //console.log("updateSnakeBody: total length= " + len + ", end length= " + i);
                    break;
                }
            }
        }

        //update body skin information
        var width = this._radius * 0.58;
        var scaleY = width / PIC_SCALE_SIZE * 2;
        var preNodePos;
        var currNodePos;
        var preBodyPos;
        var currBodyPos;
        //计算视野大小
        //var centerPosition;
        //if (playerManager.getMainPlayer()) {
        //    centerPosition = playerManager.getViewPointPos();
        //    this._lastCenterPos = centerPosition;
        //} else {
        //    centerPosition = this._lastCenterPos;
        //}
        //var offset = 60;
        //var width = cc.winSize.width / GAME_MAP_SCALE;
        //var height = cc.winSize.height / GAME_MAP_SCALE;
        //var x = centerPosition.x - width / 2 - offset;
        //var y = centerPosition.y - height / 2 - offset;
        //var viewPort = cc.rect(x, y, width + offset * 2, height + offset * 2);
        for (var i = 0; i + 1 < newLength; ++i) {
            preBodyPos = bodyPointArray[i];
            currBodyPos = bodyPointArray[i + 1];
            //if (cc.rectContainsPoint(viewPort, preBodyPos) && cc.rectContainsPoint(viewPort, currBodyPos)) {
            preNodePos = cc.p(preBodyPos.x - this._headPos.x, preBodyPos.y - this._headPos.y);
            currNodePos = cc.p(currBodyPos.x - this._headPos.x, currBodyPos.y - this._headPos.y);

            this.drawSnakeBody(i, preNodePos, currNodePos, scaleY);
            //} else {
            //    console.log("out of screen: " + i);
            //}
        }
        //show or hide some parts of body
        this.showSnakeBody(bodyPointArray, scaleY);

        if (this._isAccState) { //is in accelerating state
            //show light effect
            this.onSnakeAcc(width);

            if (!this._protectState && this._isAnimPlaying) {
                this.endProtectEffect();
            }
        }
        else {
            //set normal state
            this.onAccelerateEnd();

            //make body more smooth
            if (this._useAnti) {
                this.AntiAliasTexture(bodyPointArray, width);
            }
            //show protect effect
            if (this._protectState && !this._isAnimPlayed) {
                this.onProtectEffect();
                this._isAnimPlayed = true;

            } else if (!this._protectState && this._isAnimPlaying) {
                this.endProtectEffect();
            }
            //zoom animation
            if (this._isAnimPlaying) {
                var headPos = bodyPointArray[0];
                var tailPos = bodyPointArray[newLength - 1];
                var x = (tailPos.x - headPos.x);
                var y = (tailPos.y - headPos.y);
                var scale = Math.sqrt(x * x + y * y) / 126;
                scale = scale > 1 ? scale : 1;
                this._animatNode.setScale(scale);
            }
        }

        //show light position
        if (this._skinID > 8) {
            this.createKeyPos(currNodePos, preNodePos);
        }
        //var half = Math.round(this._radius / 2 * 0.65);
        //var lineUpPos = this.createKeyPos(currNodePos, preNodePos, half);
        //var lineUpPos = this.createKeyPos(currNodePos, preNodePos);
        //this._tailSprite.setPosition(lineUpPos);
        //this._tailSprite.setScale(this._scale * 0.88);
        //console.log("updateSnakeBody: total use time is: " + (Date.now() - this._startTime) + "ms");
    },

    showSnakeBody: function (bodyPointArray, scaleY) {
        //this._startTime = Date.now();
        var newLength = bodyPointArray.length; //node number

        //add tail circle node
        var tailIndex = newLength - 1; //node number - 1;
        var tailFrom = newLength - 2;
        var posFrom = cc.p(bodyPointArray[tailFrom].x - this._headPos.x, bodyPointArray[tailFrom].y - this._headPos.y);
        var posTo = cc.p(bodyPointArray[tailIndex].x - this._headPos.x, bodyPointArray[tailIndex].y - this._headPos.y);
        var angleCircle = this.getAngleByPos(posFrom, posTo);
        var circleSprite = this._drawCircleArray[tailIndex];
        if (circleSprite) {
            circleSprite.setRotation(angleCircle);
            circleSprite.setPosition(posTo);
            circleSprite.setScale(scaleY);
            circleSprite.setVisible(true);
        }
        else {
            console.log("updateSnakeBody: circleSprite == null");
        }

        //this is the one do not need show
        var skinSprite = this._drawArray[tailIndex];
        if (skinSprite) {
            skinSprite.setVisible(false); // need be fixed later
        }
        //console.log("updateSnakeBody: showSnakeBody use time is: " + (Date.now() - this._startTime) + "ms");
    },

    updateSnakeHead: function () {
        //update snake position
        this.setPosition(this._headPos);
        var viewPos = playerManager.getViewPointPos();

        //change angle
        var theta = Math.atan2(this._direction.y, this._direction.x);
        this._angle = (-90 - Math.round(theta * 180 * REVERSE_PAI)); //-90 for x ->
        this._scale = Math.round(this._radius * 100 / PIC_SCALE_SIZE) * 0.01; //PIC_SCALE_SIZE is real width of png

        this._header.setScale(this._scale * 1.58); //radius is used to count scale
        this._header.setRotation(this._angle);
        this._header.setPosition(this._headPos.x - viewPos.x, this._headPos.y - viewPos.y);

        //update angry
        this._headerAngry.setScale(this._scale * 1.58);
        this._headerAngry.setRotation(this._angle);
        this._headerAngry.setPosition(this._headPos.x - viewPos.x, this._headPos.y - viewPos.y);

        var scale = this._scale < 0.8 ? this._scale * 3.4 : 2.8;
        this._nameCtrl.setScale(scale);
        scale = this._scale < 0.6 ? this._scale * 3 : 1.8;
        if (this._eyesR) {
            this._eyesR.setScale(scale);
        }
        if (this._eyesL) {
            this._eyesL.setScale(scale);
        }
    },

    getAngleByPos: function (from, to) {
        var dX = Math.round(from.x - to.x);
        var dY = Math.round(from.y - to.y);
        var angle = ( -Math.round(Math.atan2(dY, dX) * 180 * REVERSE_PAI)); //-90 for x ->
        return angle;
    },

    drawSnakeBody: function (index, from, to, scaleY) {
        var dX = (from.x - to.x);
        var dY = (from.y - to.y);
        var dZ = Math.sqrt(dX * dX + dY * dY);
        var scaleX = dZ / PIC_SCALE_SIZE;
        var angle = -(Math.atan2(dY, dX) * 180 * REVERSE_PAI); //-90 for x ->

        var skinSprite = this._drawArray[index];
        if (skinSprite) {
            skinSprite.setRotation(angle);
            skinSprite.setPosition(to);
            skinSprite.setScale(scaleX, scaleY);
            skinSprite.setVisible(true);
        }
        else {
            //console.log("drawSnakeBody: skinSprite == null");
        }

        var circleSprite = this._drawCircleArray[index];
        if (circleSprite) {
            circleSprite.setRotation(angle);
            circleSprite.setPosition(from);
            circleSprite.setScale(scaleY);
            circleSprite.setVisible(true);
        }
        else {
            //console.log("drawSnakeBody: circleSprite == null");
        }
    },

    //for clearer skin effect
    AntiAliasTexture: function (bodyPointArray, width) {
        var scale = Math.round(this._radius / ORIGINAL_WIDTH);
        var color = cc.color(this._bodyColor.r, this._bodyColor.g, this._bodyColor.b, this._bodyColor.a);
        var preNodePos = cc.p(bodyPointArray[0].x - this._headPos.x, bodyPointArray[0].y - this._headPos.y);
        var currNodePos = cc.p(bodyPointArray[1].x - this._headPos.x, bodyPointArray[1].y - this._headPos.y);

        width += (this._skinID == 10) ? 0.2 : 0;
        color.a -= 42;
        this._shadeLine.drawSegment(preNodePos, currNodePos, width + 0.3 * scale, color);
        color.a -= 32;
        this._shadeLine.drawSegment(preNodePos, currNodePos, width + 0.6 * scale, color);
        color.a -= 22;
        this._shadeLine.drawSegment(preNodePos, currNodePos, width + 0.9 * scale, color);
    },

    getPlayerID: function () {
        return this._id;
    },

    getHeadPosition: function () {
        return cc.p(this._headPos.x, this._headPos.y);
    },

    onAccelerateStart: function () {
        if (this._energy > ORIGINAL_ENERGY) {
            this._isAccState = true;

            var status = 1; //1: 开始加速，2:停止加速
            NetProxy.ChangeSnakeSpeed(status);

            playerManager.setNotifyPanel(false);
            MusicManager.playEffect(MusicEffectFiles.Audio_speed);
            //console.log("this snake energy: " + this._energy);
        } else {
            this._isAccState = false;

            playerManager.runNotifyAnim();
        }
    },

    onAccelerateEnd: function () {
        this._isAccState = false;
        this._shadeLine.clear();
        this._effectLine.clear();

        //accelerate effect
        this.setEyesIsAngry(false);
        //this.resetBodyColorByAccState(false);
    },

    onSnakeAcc: function (width) {
        //draw background light effect
        var len = this._cacheBodyPoints.length;
        var first = null;
        var second = null;
        var ra = this._radius * 0.75;
        this._accOpacity = this._accOpacity > 200 ? 0 : this._accOpacity;
        this._accOpacity += 20;

        this._shadeLine.clear();
        this._effectLine.clear();

        for (var i = 0; i + 1 < len; ++i) {
            first = this._cacheBodyPoints[i];
            second = this._cacheBodyPoints[i + 1];
            first = cc.p(first.x - this._headPos.x, first.y - this._headPos.y);
            second = cc.p(second.x - this._headPos.x, second.y - this._headPos.y);
            this._shadeLine.drawSegment(second, first, ra, cc.color(255, 255, 255, this._accOpacity));

            //draw body light effect
            this._effectLine.drawSegment(second, first, width, this._lightColor);
        }

        //accelerate effect
        this.setEyesIsAngry(true);
        //this.resetBodyColorByAccState(true);
    },

    setEyesIsAngry: function (angry) {
        if (this._isAngryState === angry) {
            return;
        }
        this._isAngryState = angry;
        //console.log("setEyesIsAngry: _isAngryState == " + this._isAngryState);

        if (this._skinID > 8) {
            if (angry) {
                this._header.setVisible(false);
                this._headerAngry.setVisible(true);
                //hide body
                this._bodySkinBatchNode.setVisible(false);
            } else {
                this._header.setVisible(true);
                this._headerAngry.setVisible(false);
                //show snake body
                this._bodySkinBatchNode.setVisible(true);
            }
        } else {
            var x = 100;
            var y = 50;
            if (angry) {
                this._eyesR.removeFromParent(false);
                this._eyesL.removeFromParent(false);
                this._headerAngry.addChild(this._eyesR);
                this._headerAngry.addChild(this._eyesL);
                this._header.setVisible(false);
                this._headerAngry.setVisible(true);

                this._eyesR.setPosition(x * 0.4, y);
                this._eyesL.setPosition(x * 0.62, y);

                //hide body
                this._bodySkinBatchNode.setVisible(false);
            } else {
                this._eyesR.removeFromParent(false);
                this._eyesL.removeFromParent(false);
                this._header.addChild(this._eyesR);
                this._header.addChild(this._eyesL);
                this._header.setVisible(true);
                this._headerAngry.setVisible(false);

                this._eyesR.setPosition(x * 0.28, y);
                this._eyesL.setPosition(x * 0.68, y);

                //show snake body
                this._bodySkinBatchNode.setVisible(true);
            }
        }
    },

    //resetBodyColorByAccState: function (isAccState) {
    //    var len = this._cacheBodyPoints.length;
    //    var skinSprite = null;
    //    var circleSprite = null;
    //    if (!isAccState) {
    //        for (var i = 0; i + 1 < len; ++i) {
    //            skinSprite = this._drawArray[i];
    //            if (skinSprite) {
    //                skinSprite.setColor(this._bodyColor);
    //            }
    //            circleSprite = this._drawCircleArray[i];
    //            if (circleSprite) {
    //                circleSprite.setColor(this._bodyColor);
    //            }
    //        }
    //        circleSprite = this._drawCircleArray[len - 1];
    //        if (circleSprite) {
    //            circleSprite.setColor(this._bodyColor);
    //        }
    //    } else {
    //        for (var i = 0; i + 1 < len; ++i) {
    //            skinSprite = this._drawArray[i];
    //            if (skinSprite) {
    //                skinSprite.setColor(cc.color(255, 255, 255));
    //            }
    //            circleSprite = this._drawCircleArray[i];
    //            if (circleSprite) {
    //                circleSprite.setColor(cc.color(255, 255, 255));
    //            }
    //        }
    //        circleSprite = this._drawCircleArray[len - 1];
    //        if (circleSprite) {
    //            circleSprite.setColor(cc.color(255, 255, 255));
    //        }
    //    }
    //},

    onProtectEffect: function () {
        if (this._isAnimPlayed) {
            return;
        }
        var root = ccs.load(res.ProtectAnim_json);
        this._animatNode = root.node;
        if (null == this._animatNode) {
            console.log("null == this._animatNode");
            return;
        }
        this._animatNode.setAnchorPoint(0.5, 0.5);
        this._animatNode.setPosition(0, 0);
        this.addChild(this._animatNode);
        this._action = root.action;
        this._action.retain();

        this._animatNode.stopAllActions();
        var action = this._action.clone();
        this._animatNode.runAction(action);
        action.gotoFrameAndPlay(0, 30, 0, true);

        this._isAnimPlaying = true;
    },

    endProtectEffect: function () {
        if (this._isAnimPlaying && this._animatNode) {
            this._animatNode.stopAllActions();
            var action = this._action.clone();
            action.setLastFrameCallFunc(this.onLastFrameCallBack.bind(this));

            this._animatNode.runAction(action);
            action.gotoFrameAndPlay(30, 55, 30, false);

            this._isAnimPlaying = false;
        }
    },

    onLastFrameCallBack: function () {
        if (this._animatNode) {
            this._action.release();
            this._animatNode.stopAllActions();
            this._animatNode.removeFromParent(true);
            this._action = null;
            this._animatNode = null;

            this._isAnimPlaying = false;
            //console.log("this._animationNode: delete");
        }
    },

    hideSnake: function () {
        this._header.setVisible(false);
        this._headerAngry.setVisible(false);

        this.setVisible(false);
    },

    showSnake: function () {
        if (this._isAccState) {
            this._headerAngry.setVisible(true);
        } else {
            this._header.setVisible(true);
        }
        this.setVisible(true);
    },

    died: function (callback, delay) {
        //animation
        this._isDied = true;
        this._isAccState = false;

        MusicManager.playEffect(MusicEffectFiles.Audio_death);

        this._nameCtrl.setVisible(false);
        if (this._eyesR) {
            this._eyesR.setVisible(false);
        }
        if (this._eyesL) {
            this._eyesL.setVisible(false);
        }

        this.onLastFrameCallBack(); //stop animation

        //do some animation
        //cc.director.getScheduler().schedule(this.animateFadeOut, this, 0.05, 12, 0, null);
        this.animateFadeOut();

        this.runAction(cc.sequence(cc.delayTime(delay), cc.callFunc(callback), cc.callFunc(this.destroy, this)));
    },

    isDied: function () {
        return this._isDied;
    },

    animateFadeOut: function () {
        //need update head face
        //var viewPos = playerManager.getViewPointPos();
        //this._header.setPosition(this._headPos.x - viewPos.x, this._headPos.y - viewPos.y);
        //this._headerAngry.setPosition(this._headPos.x - viewPos.x, this._headPos.y - viewPos.y);

        //draw body opacity
        //var opacity = this._bodyColor;
        //opacity.a -= 40;
        //if (opacity.a < 60) {
        this._effectLine.clear();
        this._shadeLine.clear();
        this._header.setVisible(false);
        this._headerAngry.setVisible(false);
        this._bodySkinBatchNode.setVisible(false);
        //}
        //else {
        //    this._shadeLine.clear();
        //    fade out
        //if (this._header.isVisible()) {
        //    this._header.setOpacity(opacity.a);
        //}
        //if (this._headerAngry.isVisible()) {
        //    this._headerAngry.setOpacity(opacity.a);
        //}
        //this._bodySkinBatchNode.setOpacity(opacity.a);
        //}
        //console.log("opacity.a= " + opacity.a);
        //
        //if (opacity.a > 110) {
        //    return;
        //}
        //this._opacity = this._opacity < 0 ? 0 : this._opacity;

        //draw die light effect
        //var first = null;
        //var second = null;
        //var width = this._radius * 0.54;
        //var newLength = this._cacheBodyPoints.length;
        //this._shadeLine.clear();
        //for (var i = 0; i + 1 < newLength; ++i) {
        //    first = this._cacheBodyPoints[i];
        //    second = this._cacheBodyPoints[i + 1];
        //    first = cc.p(first.x - this._headPos.x, first.y - this._headPos.y);
        //    second = cc.p(second.x - this._headPos.x, second.y - this._headPos.y);
        //    this._shadeLine.drawSegment(second, first, width, cc.color(255, 255, 255, this._opacity));
        //}
        ////console.log("this._opacity= " + this._opacity);
        //if (this._opacity >= 200 && this._addDie > 0) {
        //    this._addDie = -60;
        //}
        //this._opacity += this._addDie;
    },

    createKeyPos: function (currNodePos, preNodePos) {
        var y = currNodePos.y - preNodePos.y;
        var x = currNodePos.x - preNodePos.x;

        //get the position for every key point
        //var theta = Math.atan2(-y, -x) + HALF_PAI;
        //var sin = radius * Math.sin(theta);
        //var cos = radius * Math.cos(theta);
        //var x1 = currNodePos.x + cos; //up position
        //var y1 = currNodePos.y + sin;
        //var x2 = currNodePos.x - cos; //down position
        //var y2 = currNodePos.y - sin;

        //set light angle
        var theta = Math.atan2(-y, -x);
        var angle = (-90 - Math.round(theta * 180 * REVERSE_PAI)); //-90 for x ->
        this._tailSprite.setRotation(angle);
        this._tailSprite.setPosition(currNodePos);
        this._tailSprite.setScale(this._scale * 1.18);

        //return cc.p(x1, y1);
    },

    //createKeyPoint: function (pointsLeft, pointsRight, currNodePos, preNodePos, radius) {
    //    var y = currNodePos.y - preNodePos.y;
    //    var x = currNodePos.x - preNodePos.x;
    //
    //    //get the position for every key point
    //    var theta = Math.atan2(-y, -x) + HALF_PAI;
    //    var sin = radius * Math.sin(theta);
    //    var cos = radius * Math.cos(theta);
    //    var x1 = currNodePos.x + cos;
    //    var y1 = currNodePos.y + sin;
    //    var x2 = currNodePos.x - cos;
    //    var y2 = currNodePos.y - sin;
    //
    //    pointsLeft.push(cc.p(x1, y1));
    //    pointsRight.push(cc.p(x2, y2));
    //},

    updatePosition: function (dt) {
        var theta = Math.atan2(this._direction.y, this._direction.x);
        var speed = SPEED_DEFAULT;
        if (this._isAccState) {
            speed = SPEED_DEFAULT * 3;
        }
        this._speedX = speed * Math.cos(theta);
        this._speedY = speed * Math.sin(theta);
        var newHeadPos = this._headPos;
        var dx = this._speedX * dt;
        var dy = this._speedY * dt;
        newHeadPos.x += dx;
        newHeadPos.y += dy;

        //update draw body
        this.updateSnakeBody(this._cacheBodyPoints);
        //draw
        var width = this._radius * 0.58;
        var scaleY = width / PIC_SCALE_SIZE * 2;
        var preNodePos = cc.p(newHeadPos.x - this._headPos.x, newHeadPos.y - this._headPos.y);
        var currNodePos = cc.p(this._cacheBodyPoints[1].x - newHeadPos.x, this._cacheBodyPoints[1].y - newHeadPos.y);
        this.drawSnakeBody(0, preNodePos, currNodePos, scaleY);
        // anti
        var scale = this._radius / ORIGINAL_WIDTH;
        var color = cc.color(this._bodyColor.r, this._bodyColor.g, this._bodyColor.b, this._bodyColor.a);
        color.a -= 42;
        this._shadeLine.drawSegment(preNodePos, currNodePos, width + 0.2 * scale, color);
        color.a -= 32;
        this._shadeLine.drawSegment(preNodePos, currNodePos, width + 0.4 * scale, color);
        color.a -= 22;
        this._shadeLine.drawSegment(preNodePos, currNodePos, width + 0.6 * scale, color);

        //update head
        this._headPos = newHeadPos;
        this.updateSnakeHead();
    },

    //changeDirection: function (pos) {
    //move to the new direction
    //var srcPos = this.getPosition();
    //var desPos = this.getParent().convertToNodeSpace(pos); //convert to local space
    //var dx = desPos.x - srcPos.x;
    //var dy = desPos.y - srcPos.y;
    //var dz = Math.sqrt(dx * dx + dy * dy);
    //var cosA = (dx * 100 / dz) * 0.01;
    //var sinA = (dy * 100 / dz) * 0.01;
    //update speed
    //this._speedX = SPEED_DEFAULT * cosA;
    //this._speedY = SPEED_DEFAULT * sinA;
    //console.log("  this._speedX= " + this._speedX + " this._speedY= " + this._speedY);
    //},
});