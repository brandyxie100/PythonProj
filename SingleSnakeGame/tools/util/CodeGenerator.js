/**
 * Created by malloyzhu on 2015/12/21.
 */

var fs = require('fs');
var util = require("./Util.js");
var fileName = process.argv[2];
var codeTemplateBasePath = process.argv[3];
var codeTemplateFileName = process.argv[4];
var ruleList = process.argv[5];

/**
 * 生成代码文件
 * @param codeTemplateFilePath：模板代码文件路径
 * @param codeFilePath：生成代码文件路径
 */
exports.generatorCodeFile = function (codeTemplateFilePath, codeFilePath, ruleList) {
    if (typeof codeTemplateFilePath !== 'string') {
        return;
    }

    if (typeof codeFilePath !== 'string') {
        return;
    }

    try {
        var codeTemplate = fs.readFileSync(codeTemplateFilePath,"utf-8");
        var code = util.replaceCodeTemplateString(ruleList, codeTemplate);
        try {
            fs.writeFileSync(codeFilePath, code);
        }
        catch (e) {
            console.log(e);
        }
    }
    catch(e) {
        console.log(e);
    }
};

/**
 *
 * @param basePath
 * @param codeTemplateFileName
 * @param fileName
 * @param ruleList
 */
exports.generator = function (basePath, codeTemplateFilePath, fileName, ruleList) {
    var ret = util.isFullLetterFileName(fileName);
    if (!ret) {
        console.log("文件名错误");
        return;
    }

    ret = util.isDiskPath(basePath);
    if (!ret) {
        console.log("磁盘路径错误");
        return;
    }

    basePath += '\\';
    var codePath = basePath + fileName + ".js";
    this.generatorCodeFile(codeTemplateFilePath, codePath, ruleList);
};

if (module == require.main) {
    try {
        ruleList = JSON.parse(ruleList);
        this.generator(codeTemplateBasePath, codeTemplateFileName, fileName, ruleList);
    }
    catch (e) {
        console.log(e);
    }
};
