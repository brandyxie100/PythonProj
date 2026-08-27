/**
* Created by malloyzhu on &2015/12/21&
*/

var #CodeTemplate# = WindowBase.extend({
	ctor: function () {
		this._super();
	},

	onShowNotify: function () {

	},

	onShow: function () {

	},

	onHideNotify: function () {

	},

	onHide: function () {

	},

	onRemoveNotify: function () {

	},

	onRemove: function () {

	},

	onCover: function () {

	},

	onResume: function () {

	},

	onDestroy: function () {

	}
});

#CodeTemplate#.GetInstance = function () {
	if(null == #CodeTemplate#._instance){
		#CodeTemplate#._instance = new #CodeTemplate#();
	}
	return #CodeTemplate#._instance;
};

#CodeTemplate#.Show = function () {
	 var instance = #CodeTemplate#.GetInstance();
	WindowManager.GetInstance().showWindow(instance, null, true, WindowZOrder.LAYER_Z_ORDER_SECOND_SUB_UI, false, null, null);
};

#CodeTemplate#.Hide = function () {
	WindowManager.GetInstance().hideWindow(#CodeTemplate#._instance);
};

#CodeTemplate#.Remove = function () {
	WindowManager.GetInstance().removeWindow(#CodeTemplate#._instance);
	#CodeTemplate#._instance = null;
};