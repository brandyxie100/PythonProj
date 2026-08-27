
'use strict'

class Controller{

	constructor(PacketHandler) {
		this.PacketHandler = PacketHandler
	}

    sendToClient(cmd, data) {
        this.PacketHandler && this.PacketHandler.sendToClient(cmd, data);
    }
    
};

module.exports = Controller;