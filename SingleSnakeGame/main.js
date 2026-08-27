/**
 * A brief explanation for "project.json":
 * Here is the content of project.json file, this is the global configuration for your game, you can modify it to customize some behavior.
 * The detail of each field is under it.
 {
    "project_type": "javascript",
    // "project_type" indicate the program language of your project, you can ignore this field

    "debugMode"     : 1,
    // "debugMode" possible values :
    //      0 - No message will be printed.
    //      1 - cc.error, cc.assert, cc.warn, cc.log will print in console.
    //      2 - cc.error, cc.assert, cc.warn will print in console.
    //      3 - cc.error, cc.assert will print in console.
    //      4 - cc.error, cc.assert, cc.warn, cc.log will print on canvas, available only on web.
    //      5 - cc.error, cc.assert, cc.warn will print on canvas, available only on web.
    //      6 - cc.error, cc.assert will print on canvas, available only on web.

    "showFPS"       : true,
    // Left bottom corner fps information will show when "showFPS" equals true, otherwise it will be hide.

    "frameRate"     : 60,
    // "frameRate" set the wanted frame rate for your game, but the real fps depends on your game implementation and the running environment.

    "noCache"       : false,
    // "noCache" set whether your resources will be loaded with a timestamp suffix in the url.
    // In this way, your resources will be force updated even if the browser holds a cache of it.
    // It's very useful for mobile browser debuging.

    "id"            : "gameCanvas",
    // "gameCanvas" sets the id of your canvas element on the web page, it's useful only on web.

    "renderMode"    : 0,
    // "renderMode" sets the renderer type, only useful on web :
    //      0 - Automatically chosen by engine
    //      1 - Forced to use canvas renderer
    //      2 - Forced to use WebGL renderer, but this will be ignored on mobile browsers

    "engineDir"     : "frameworks/cocos2d-html5/",
    // In debug mode, if you use the whole engine to develop your game, you should specify its relative path with "engineDir",
    // but if you are using a single engine file, you can ignore it.

    "modules"       : ["cocos2d"],
    // "modules" defines which modules you will need in your game, it's useful only on web,
    // using this can greatly reduce your game's resource size, and the cocos console tool can package your game with only the modules you set.
    // For details about modules definitions, you can refer to "../../frameworks/cocos2d-html5/modulesConfig.json".

    "jsList"        : [
    ]
    // "jsList" sets the list of js files in your game.
 }
 *
 */

var t;
var resize = function () {
    var timeout = t ? 200 : 1000;
    clearTimeout(t);

    t = setTimeout(function () {
        //var tipIDName;
        //if (cc.sys.OS_ANDROID == cc.sys.os) {
        //    tipIDName = 'portraintAndroidTip';
        //} else {
        //    tipIDName = 'portraitTip';
        //}
        //var div = document.getElementById(tipIDName);
        //if (document.documentElement.clientHeight > document.documentElement.clientWidth || cc.winSize.height > cc.winSize.width) {
        //    if (LOGIN_REQUEST_DATA.GAME_START) {
        //        if (!div) {
        //            div = document.createElement('div');
        //            div.id = tipIDName;
        //            document.body.appendChild(div);
        //        }
        //    } else {
        //        console.log("game not start yet.");
        //    }
        //} else {
        //    if (div) {
        //        document.body.removeChild(div);
        //    }

        //modify window size
        NetProxy.ResizeWindow();

        //send resize event here
        var evt = new CEvent(CEventType.RESIZE_WINDOW);
        CEventManager.dispatchEvent(evt);

    }, timeout);
};

cc.game.onStart = function () {
    if (!cc.sys.isNative && document.getElementById("cocosLoading")) //If referenced loading.js, please remove it
    {
        document.body.removeChild(document.getElementById("cocosLoading"));
    }

    //set property
    cc.view.resizeWithBrowserSize(true);
    // setOrientation is a native (JSB) API; not present in cocos2d-html5 web builds.
    if (typeof cc.view.setOrientation === "function") {
        cc.view.setOrientation(cc.ORIENTATION_LANDSCAPE_LEFT);
    }
    cc.view.setDesignResolutionSize(1334, 750, cc.ResolutionPolicy.FIXED_HEIGHT);
    cc.view.adjustViewPort(true);
    //var bOpenRetina = (cc.sys.os == cc.sys.OS_IOS || cc.sys.os == cc.sys.OS_OSX) ? true : false;
    var bOpenRetina = true;
    //if (cc._renderType !== cc.game.RENDER_TYPE_WEBGL) {
    //    bOpenRetina = false;
    //}
    cc.view.enableRetina(bOpenRetina);

    //on window resize
    cc.view.setResizeCallback(resize);
    resize();

    //on loading finished
    //window.addEventListener('onload', function () {
    //    console.log("main.js onLoadFinished");
    //});
    //document.body.onload = function () {
    //    console.log("document.body.onload onLoadFinished");
    //};
    //window.onload = function () {
    //    console.log("window.onload onLoadFinished");
    //};
    //window.addEventListener('onpageshow', function () {
    //    MusicManager.playMusic(MusicEffectFiles.Audio_bgm, true);
    //});
    //window.addEventListener('onpagehide', function () {
    //    MusicManager.stopMusic(true);
    //});

    //进入后台
    cc.eventManager.addCustomListener(cc.game.EVENT_HIDE, function () {
        console.log("main.js cc.game.EVENT_HIDE");

        MusicManager.stopMusic(true);
        cc.game.pause();

        NetProxy.pauseServer();

        // closeOutSound is provided by the host H5 SDK when embedded; skip locally.
        if (typeof window.closeOutSound === "function") {
            window.closeOutSound();
        }
    });

    //恢复显示
    cc.eventManager.addCustomListener(cc.game.EVENT_SHOW, function () {
        console.log("main.js cc.game.EVENT_SHOW");

        MusicManager.playMusic(MusicEffectFiles.Audio_bgm, true);
        cc.game.resume();

        NetProxy.resumeServer();
    });

    //load resources
    cc.LoaderScene.preload(resGroup.Main, function () {
        console.log("load resGroup.Main finished");

        ConfigLoader.load();
        SpriteLoader.load();
        storageManager.load();
        dataManager.init();

        //need fix this later, no login scene
        cc.director.runScene(new LoginScene());
    }, this);
};

cc.game.run();