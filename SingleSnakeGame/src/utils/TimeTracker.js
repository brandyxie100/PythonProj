/**
 * Created by alexgan on 2016/5/23.
 */

var TimeTracker = {

    timer: {},

    start: function (key) {
        if (this.timer[key] == null) {
            this.timer[key] = [];
        }

        this.timer[key].start = new Date().getTime();
    },

    stop: function (key) {
        this.timer[key].stop = new Date().getTime();

        var elapsed = this.duration(key);
        delete this.timer[key];
        console.log("[" + key + "] elapsed:", elapsed);
    },

    duration: function (key) {
        return (this.timer[key].stop - this.timer[key].start);
    }
};