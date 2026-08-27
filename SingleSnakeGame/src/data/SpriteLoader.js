/**
 * Created by malloyzhu on 2016/2/2.
 */

var SpriteLoader = {
    load: function () {
        for (var i in resGroup.Plist) {
            cc.spriteFrameCache.addSpriteFrames(resGroup.Plist[i]);
        }
    }
};

