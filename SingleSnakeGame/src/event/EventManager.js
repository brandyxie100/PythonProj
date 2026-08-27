/**
 * Created by billbao on 2016/4/21.
 */


/**
 * 事件类
 */
var CEvent = function (type, data,cancelable) {
    this.cancelable = cancelable; //是否取消传递
    this.type = type; //类型
    this.data = data; // 数据

    /// <summary>
    /// 复制
    /// </summary>
    /// <returns type="Event">复制后的元素</returns>
    this.clone = function() {
        var that = new CEvent();
        that.cancelable = this.cancelable;
        that.type = this.type;
        that.data = this.data;
        return that;
    };

    this.toString = function() {
        return "Event( type: " + this.type + ", cancelable: " + this.cancelable + this.eventPhase + ")";
    };
};

/**
 * 事件监听类
 * @param listener 监听回调函数
 * @param priority 优先级
 */
var CEventListener = function (listener,priority) {
    if (typeof(arguments[0]) != "function") {
        throw "必须指明listener";
    }
    this.listener = listener;
    this.priority = priority?priority:0;
};

var CEventManager = {
    eventListeners : [],

    /// <summary>
    /// 添加事件处理函数
    /// </summary>
    /// <param name="type">类型</param>
    /// <param name="listener">处理函数</param>
    /// <param name="priority">优先级，默认为0</param>
    addEventListener : function (type, listener, priority) {
        if (typeof (arguments[1]) != "function") {
            throw "必须指明type和listener";
        }

        if (!this.eventListeners[type]) {
            this.eventListeners[type] = [];
        }
        var index = this.eventListeners[type].length;
        //防止重复监听
        for (var i = 0; i < index; i++) {
            var temp = this.eventListeners[type][i];
            if (temp.listener == listener) {
                return;
            }
        }
        //console.log(type + "监听个数：" + (index+1));
        var eventListener = new CEventListener(listener, priority);
        this.eventListeners[type].push(eventListener);
        this.eventListeners[type].sort(function (a, b) { return a.priority - b.priority; });
        return listener;
    },
    /// <summary>
    /// 移除监听器
    /// </summary>
    /// <param name="type">类型</param>
    /// <param name="listener">监听器</param>
    removeEventListener : function (type, listener) {
        var len = arguments.length;
        if (len < 2) {
            throw "必须指定type 与 listener";
        }
        if (!this.eventListeners[type]) {
            return;
        }
        var index = this.eventListeners[type].length;
        //如果数组长度为0，删掉整个数组
        if (index == 0) {
            var lisIndex = this.eventListeners.length;
            for (var i = 0; i < lisIndex; i++) {
                if (type == this.eventListeners[i]) {
                    this.eventListeners.splice(i, 1);
                }
            }
        } else {
            for (var j = 0; j < index; j++) {
                var temp = this.eventListeners[type][j];
                if (temp.listener == listener) {
                    this.eventListeners[type].splice(j, 1);
                    break;
                }
            }
        }
    },
    /// <summary>
    /// 分派一个事件
    /// </summary>
    /// <param name="event">事件</param>
    dispatchEvent : function (event) {
        // 如果event不是一个Event类，则默认是字符串，作为事件标识创建一个新的Event(event)
        event = (typeof (event) == "string") ? new CEvent(event) : event;
        if (!this.eventListeners[event.type]) {
            return;
        }
        var index = this.eventListeners[event.type].length;
        for (var k = 0; k < index; k++) {
            var temp = this.eventListeners[event.type][k];
            if (temp.listener) {
                if (!event.cancelable) {
                    temp.listener(event);
                } else {
                    continue;
                }
            }
        }
    },
    /// <summary>
    /// 判断是否具有该事件的处理器
    /// </summary>
    /// <param name="type">事件类型</param>
    /// <returns type="boolean">判断是否具有该事件的处理器</returns>
    hasEventListener : function (type) {
        return this.eventListeners[type] && this.eventListeners[type].length > 0;
    }

};

/**
 * example
 *
 var RequestManager = {
    sendData: function (eventType, params, listener, priority) {
        CEventManager.addEventListener(eventType, listener, priority);
        console.log("发包，事件：" + eventType);
        var json = {
            eventType: eventType,
            parameters: params
        };
        SocketManager._instance.json.send(json);
    },
    readData: function (data) {
        var evt = new CEvent();
        evt.type = data.eventType;
        evt.data = data;
        CEventManager.dispatchEvent(evt);
    }
};
 */
