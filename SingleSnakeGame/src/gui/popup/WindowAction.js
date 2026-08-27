/**
 * Created by malloy on 2015/5/29.
 */

/**
 * 窗口 action
 * @type {{}}
 */
var WindowAction = {
    /**
     * 缩放并带回弹效果
     * @param window
     * @returns {*}
     */
    getScaleEaseElasticOutAction: function (window) {
        if (null == window) {
            return null;
        }
        var currentScale = 1.0;
        window.setScale(0.8);
        var scaleTo = new cc.ScaleTo(1.0, currentScale, currentScale);
        var easeElasticOut = new cc.EaseElasticOut(scaleTo);
        var actionCompleteCallBack = new cc.CallFunc(this._onActionComplete, this);
        var action = new cc.Sequence(easeElasticOut, actionCompleteCallBack);
        return action;
    },

    getDropAction: function (window) {
        if (null == window) {
            return null;
        }
        var originalPosition = window.getPosition();
        window.setPositionY(originalPosition.y + cc.winSize.height);
        var moveAction = new cc.MoveTo(0.75, originalPosition);
        var elasticOutAction = moveAction.easing(cc.easeElasticOut(0.7));
        var callback = new cc.CallFunc(this._onActionComplete, this);
        var action = new cc.Sequence(elasticOutAction, callback);
        return action;
    },

    /**
     * 设置 action 完成回调
     */
    setActionCompleteCallBack: function (func) {
        this._actionCompleteCallBack = func;
    },

    /**
     * action 完成时回调
     * @param object
     * @private
     */
    _onActionComplete: function (object) {
        this._actionCompleteCallBack(object);
    }
};

