'use strict'
var Util = require('util')
var Controller = require('./Controller')
var SnakeModel = require('../models/SnakeModel')
var FoodModel = require('../models/FoodModel')

class SnakeController extends Controller {
	
	constructor(PacketHandler) {
		super(PacketHandler);
        console.log("SnakeController: constructor");
	}

	move(params) {

		var touchPos = params.touchPos;

		var snake = this.PacketHandler.getSnake();
		if (!snake) {
			return;
		}

		// Get dir
		var touchX = parseFloat(touchPos.xPos);
		var touchY = parseFloat(touchPos.yPos);
		if (isNaN(touchX) || isNaN(touchY) || (touchX === 0 && touchY === 0)) {
			return;
		}
		snake.setTargetPos(touchX, touchY);
	}

	changeSpeed(params) {

		var snake = this.PacketHandler.getSnake();
		if (!snake) {
			return;
		}

		if (params.changeStatus == 1) {
			snake.accelerate = 1;
		} else {
			snake.accelerate = 0;
		}
		
	}

	resizeScreen(clientScreen) {
		var snake = this.PacketHandler.getSnake();
		if (!snake) {
			return;
		}

		if (clientScreen.screenWidth && clientScreen.screenHeight) {
			snake.setScreenParams(clientScreen.screenWidth, clientScreen.screenHeight);
		}
	}

}

module.exports = SnakeController

