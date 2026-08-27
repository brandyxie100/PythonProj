'use strict'
var Entities = require("../entities/entities");

class SnakeModel
{
	constructor() {
		this.snakes = new Map();
	}

	/**
	 * @method 获取初始蛇数据
	 * @param {String} 名称
	 */
	getInitSnake(name) {
		var data = new Entities.Snake(name);
		return data;
	}

	/**
	 * @method 新增蛇信息
	 * @param {Object | Array} data 数据 @example {SnakeInfo} | [{SnakeInfo},{SnakeInfo},...]
	 * @param {Function} callback 回调函数
	 */
	insert(data)
	{
		this.snakes.set(data.snakeId, data);
	}


	/**
	 * @method 删除蛇信息
	 * @param {Int | Array} data 蛇id @example snakeId1 | [snakeId1,snakeId2,...]
	 * @param {Function} callback 回调函数
	 */
	delete(snakeId)
	{
		this.snakes.delete(snakeId);
	}
	
	getById(id)
	{
		return this.snakes.get(id);
	}

	getSize()
	{
		return this.snakes.size;
	}
}

module.exports = new SnakeModel();

