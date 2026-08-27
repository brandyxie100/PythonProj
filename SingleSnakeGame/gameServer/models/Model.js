'use strict'

var DataManager = require('./DataManager')
var EventEmitter = require('../utils/eventEmitter')
var idConfig = {
	Snake: {
		key: 'snakeId',
		type: 0,
		val: 10
	},
	Food: {
		key: 'foodId',
		type: 1,
		val: 11
	}
}

class Model {

  constructor() {

  }

  /**
	* @method 操作数据底层接口
	* @param {String} options.type 操作类型
	* @param {String} options.name 模型名称
	* @param {Object} options.data 参数数据
	* @param {Function} options.callback 回调函数
  */
  query(options) {
		var type = options.type,
			name = options.name,
			key = idConfig[name]['key'],
			data = options.data,
			callback = options.callback,
			gameData = DataManager.gameData,
			originalData = gameData['original'][name],
			mapData = gameData['map'][name],
			result;

		switch (type) {

			case 'get':

				if (data instanceof Array) {
					result = [];
					data.forEach(function (id) {
						if (mapData[id]) {
							result.push(mapData[id])
						}
					}) 
				} else {
					result = mapData[data]
				}
				callback && callback(null, result)

			break;

			case 'insert':

				var _insert = function (item) {
					var id = idConfig[name]['val'];
					item[key] = id;
					mapData[id] = item;
					originalData.push(item);

					var incrementId = parseInt(id / 10) + 1;
					idConfig[name]['val'] = incrementId * 10 + idConfig[name]['type'];
					return item
				};

				if (data instanceof Array) {
					result = [];
					data.forEach(function (item) {
						result.push(_insert(item))
					});
				} else {
					result = _insert(data)
				}
				callback && callback(null, result)

			break;

			case 'update':
				var _update = function (item) {
					var tgtData = mapData[item.id],
						itemData = item.data;
					if (tgtData && itemData) {
						for (var key in itemData) {
							tgtData[key] = itemData[key]
						}
						return tgtData
					}
				};

				if (data instanceof Array) {
					result = [];
					data.forEach(function (item) {
						var _result = _update(item);
						if (_result) {
							result.push(_result)
						}
					})
				} else {
					result = _update(data)
				}
				callback && callback(null, result)

			break;

			case 'delete':

				var _delete = function (id) {
					if (mapData[id]) {
						delete mapData[id]
					}
					originalData.some(function (item, i) {
						if (item[key] == id) {
							originalData.splice(i, 1);
							return true;
						}
					});

					EventEmitter.emit(name + 'Delete', id)
				};
				if (data instanceof Array) {
					data.forEach(function (id) {
						_delete(id)
					})
				} else {
					_delete(data)
				}
				callback && callback()

			break;

			case 'foreach':

				originalData.forEach(function (item) {
					callback && callback(item)
				})

			break;
		}
		
	}

	getData(name) {
		var originalData = DataManager.gameData['original'][name];
		return originalData
	}
}

module.exports = Model