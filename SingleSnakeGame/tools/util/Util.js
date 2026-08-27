/**
 * Created by malloyzhu on 2015/12/21.
 */

var fs = require('fs');

/**
 * 获取日期
 * @returns {string}
 */
exports.getFullDate = function () {
    var dateObject = new Date();
    var year = dateObject.getFullYear();
    var month = dateObject.getMonth() + 1;
    var date = dateObject.getDate();
    var fullDate = year + "/" + month + "/" + date;
    return fullDate;
};

/**
 * 是否是磁盘路径
 * @param path
 * @returns {*}
 */
exports.isDiskPath = function (path) {
    if (typeof path !== 'string') {
        return false;
    }

    return path.match(/^[a-zA-Z]:\\[a-zA-Z_0-9\\]*/);
};

/**
 * 文件名是否全为字母
 * @param fileName
 * @returns {*}
 */
exports.isFullLetterFileName = function (fileName) {
    if (typeof fileName !== 'string') {
        return false;
    }

    return fileName.match("^[A-Za-z]+$");
};

/**
 * 替换代码模板中的字符串
 * @param ruleList：规则列表[{regular: xxx, replaceString: xxx}]
 * @param codeTemplateString：代码模板字符串
 */
exports.replaceCodeTemplateString = function (ruleList, codeTemplateString) {
    if (typeof codeTemplateString !== 'string') {
        return;
    }

    var ret = codeTemplateString;
    for (var i in ruleList) {
        var rule = ruleList[i];
        var regular = rule.regular;
        var replaceString = rule.replaceString;
        var reg = new RegExp(regular, "g");
        ret = ret.replace(reg, replaceString);
    }
    return ret;
};

/**
 * 将首字母置为大写
 * @param word
 * @returns {*}
 */
exports.upperFirstLetter = function (word) {
    if (typeof word !== 'string') {
        return word;
    }
    return word.substring(0, 1).toUpperCase() + word.substring(1);
};

exports.isBlankString = function (str) {
    return (!str || /^\s*$/.test(str));
};

exports.endsWithString = function (str, suffix) {
    if (!this.isBlankString(str)) {
        return str.match(suffix + "$") == suffix;
    } else {
        return false;
    }
};

exports.startsWithString = function (str, prefix) {
    if (!this.isBlankString(str)) {
        return str.indexOf(prefix) === 0;
    } else {
        return false;
    }
};