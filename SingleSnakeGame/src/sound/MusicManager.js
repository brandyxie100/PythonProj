/**
 * Created by malloyzhu on 2015/7/7.
 */

var MusicManager = {
    _fileExtension: '.mp3',
    _bSoundEnable: true,
    _bMusicEnable: true,

    setSoundEnable: function (bValue) {
        if (this._bSoundEnable === bValue) {
            return;
        }
        this._bSoundEnable = bValue;
        if (this._bSoundEnable === false) {
            cc.audioEngine.stopAllEffects();
        }
    },

    setMusicEnable: function (bValue) {
        if (this._bMusicEnable === bValue) {
            return;
        }
        this._bMusicEnable = bValue;
        if (this._bMusicEnable === false) {
            cc.audioEngine.stopMusic();
        }
    },

    playMusic: function (url, loop) {
        if (!this._bMusicEnable) {
            return;
        }

        var src = url + this._fileExtension;
        if (!cc.audioEngine.isMusicPlaying()) {
            cc.audioEngine.playMusic(src, loop);
        }
    },

    stopMusic: function () {
        if (cc.audioEngine.isMusicPlaying()) {
            cc.audioEngine.stopMusic();
        }
    },

    isMusicPlaying: function () {
        return cc.audioEngine.isMusicPlaying();
    },

    playEffect: function (url, callback, loop) {
        if (!this._bSoundEnable) {
            return;
        }
        var src = url + this._fileExtension;
        var audio = cc.audioEngine.playEffect(src, loop, function (audio) {
            typeof(callback) === 'function' && callback(audio);
        }.bind(this));
        if (null != audio) {
            typeof(callback) === 'function' && callback(audio);
        }
    },

    pauseEffect: function (audio) {
        cc.audioEngine.pauseEffect(audio);
    },

    stopEffect: function (audio) {
        cc.audioEngine.stopEffect(audio);
    },

    pauseAllEffects: function () {
        cc.audioEngine.pauseAllEffects();
    },

    resumeAllEffects: function () {
        cc.audioEngine.pauseAllEffects();
    },

    stopAllEffects: function () {
        cc.audioEngine.stopAllEffects();
    }
};