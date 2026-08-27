/**
 * Created by billbao on 2015/6/11.
 *
 * 模态窗口
 */

var ModalDialog = cc.Layer.extend({
    touchListener: null,     //触摸监听器
    ctor: function(){
        this._super();

        this.touchListener = cc.EventListener.create({
            event: cc.EventListener.TOUCH_ONE_BY_ONE,
            swallowTouches: true,
            onTouchBegan: function(touch, event){
                return true;
            }
        });
    },

    onEnter: function(){
        this._super();

        cc.eventManager.addListener(this.touchListener, this);

    },

    onExit: function(){

        cc.eventManager.removeListener(this.touchListener);
        this._super();
    }
});

var MDlgManager = {
    _mdList: []
};

MDlgManager.AddDialog = function(name, dlgLayer){
    if(!MDlgManager._mdList){
        MDlgManager._mdList = [];
    }

    MDlgManager._mdList.push({name: name, dlg: dlgLayer});
};

MDlgManager.RemoveDialog = function(name){
    if(MDlgManager._mdList){
        var list = MDlgManager._mdList;
        var len = list.length;
        for(var i = 0; i < len; i++){
            var item = list[i];
            if(item && item.name == name){
                item.dlg.removeFromParent(true);
                item.dlg = null;
                list.splice(i, 1);
                break;
            }
        }
    }
};

MDlgManager.ClearAllDialog = function(){
    if(MDlgManager._mdList){
        var list = MDlgManager._mdList;
        var len = list.length;
        for(var i = 0; i < len; i++){
            var item = list[i];
            if(item){
                item.dlg.removeFromParent(true);
                item.dlg = null;
            }
        }
        list.splice(0, list.length);
    }
};

MDlgManager.IsHaveDialog = function(name){
    var isHave = false;
    if(MDlgManager._mdList){
        var list = MDlgManager._mdList;
        var len = list.length;
        for(var i = 0; i < len; i++){
            var item = list[i];
            if(item && item.name == name){
                isHave = true;
                break;
            }
        }
    }
    return isHave;
};

MDlgManager.GetDialog = function(name){
    if(MDlgManager._mdList){
        var list = MDlgManager._mdList;
        var len = list.length;
        for(var i = 0; i < len; i++){
            var item = list[i];
            if(item && item.name == name){
                return item.dlg;
            }
        }
    }
    return null;
};