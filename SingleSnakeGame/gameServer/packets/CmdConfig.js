
var CMD = {

	1: {
		packetBody: 'pingRequest',
		route: 'LoginController.ping'
	},
	2: {
		packetBody: 'loginRequest',
		route: 'LoginController.login'
	},
	3: {
		packetBody: 'moveSnake',
		route: 'SnakeController.move'
	},
	4: {
		packetBody: 'changeSnakeSpeed',
		route: 'SnakeController.changeSpeed'
	},
	5: {
		packetBody: 'reviveSnake',
		route: 'LoginController.revive'
	},
	6: {
		packetBody: 'resizeClientScreen',
		route: 'SnakeController.resizeScreen'
	},
	101: {
		packetBody: 'pingResponse'
	},
	102: {
		packetBody: 'loginResponse'
	},
	103: {
		packetBody: 'reviveResponse'
	},
	104: {
		packetBody: 'errorResponse'
	},
	201: {
		packetBody: 'updateRankList'
	},
	202: {
		packetBody: 'updateGlobalInfo'
	},
	203: {
		packetBody: 'updateEatFood'
	},
	204: {
		packetBody: 'updateSnakeDeath'
	},
	205: {
		packetBody: 'updateSnakeSuicide'
	},
	206: {
		packetBody: 'timeOver'
	},
	207: {
		packetBody: 'updateRadarInfo'
	},
	208: {
		packetBody: 'updateSnakeIncrementInfo'
	},
	209: {
		packetBody: 'updateSelfRank'
	},
	210: {
		packetBody: 'updateCallBoardInfo'
	}
};

module.exports = CMD