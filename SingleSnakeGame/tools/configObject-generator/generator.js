/**
 * Created by malloyzhu on 2015/12/21.
 */
var fs = require('fs');
var path = require("path");
var xlsx = require('node-xlsx');
var util = require("../util/Util.js");

var MinRow = 2;
//var basePath = process.cwd() + path.sep;
var basePath = __dirname;
var xlsxRootPath = basePath + '/lib/excel/';
var configRootPath = basePath + '/config/';
var configObjectRootPath = basePath + '/configObject/';
var structureCodeTemplatePath = basePath + '/lib/StructureTemplate.js';
var getSetCodeTemplatePath = basePath + '/lib/GetSetTemplate.js';

var excleName = null;
var xlsFileList = [];
var structureCodeTemplate = null;
var getSetCodeTemplate = null;

function initCodeTemplate() {
    try {
        structureCodeTemplate = fs.readFileSync(structureCodeTemplatePath, "utf-8");
        getSetCodeTemplate = fs.readFileSync(getSetCodeTemplatePath, "utf-8");
    }
    catch (e) {
        console.log(e);
    }
};

function generatorConfigObjectCodeFile(excelFilePath) {
    var result = excelFilePath.split(path.sep);
    result = result[result.length - 1].split(".");
    excleName = result[0];
    var sheetDatas = xlsx.parse(excelFilePath);
    for (var i in sheetDatas) {
        var sheetData = sheetDatas[i];
        handleSheet(sheetData);
    }
};

function handleSheet(sheetData) {
    if (sheetData.data.length >= (MinRow - 1)) {
        var code = generatorConfigObjectCode(sheetData);
        writeConfigObjectCodeFile(sheetData.name, code);
        var configData = getSheetConfigData(sheetData);
        writeConfigFile(excleName + '_' + sheetData.name, 'var ' + excleName + '_' + sheetData.name + ' = ' + JSON.stringify(configData, null, 4) + ";");
    }
};

function getSheetConfigData(sheetData) {
    var data = [];
    for (var row = 3; row < sheetData.data.length; row++) {
        var rowData = {};
        var cols = sheetData.data[row];
        for (var col = 0; col < cols.length; col++) {
            var fieldName = sheetData.data[0][col];
            var fieldValue = sheetData.data[row][col];
            rowData[fieldName] = fieldValue;
        }
        data.push(rowData);
    }
    return data;
};

function writeConfigFile(sheetName, sheetData) {
    try {
        var codeFilePath = configRootPath + util.upperFirstLetter(sheetName) + ".js";
        fs.writeFileSync(codeFilePath, sheetData);
        console.log("生成 " + util.upperFirstLetter(sheetName) + ".js" + " 成功");
    }
    catch (e) {
        console.log(e);
    }
};

function writeConfigObjectCodeFile(sheetName, code) {
    try {
        var codeFilePath = configObjectRootPath + util.upperFirstLetter(sheetName) + "ConfigObject.js";
        fs.writeFileSync(codeFilePath, code);
        console.log("生成 " + util.upperFirstLetter(sheetName) + "ConfigObject.js" + " 成功");
    }
    catch (e) {
        console.log(e);
    }
};

/**
 * 生成配置对象代码
 * @param sheetData：工作表数据
 */
function generatorConfigObjectCode(sheetData) {
    var ruleList = [{regular: "&.*?&", replaceString: util.getFullDate()}, {
        regular: "#.*?#",
        replaceString: util.upperFirstLetter(sheetData.name) + "ConfigObject"
    }];

    var code = util.replaceCodeTemplateString(ruleList, structureCodeTemplate);
    code = code.replace(/\n+$/g, "");//去掉最后的换行符

    var fieldData = sheetData.data[0];//字段数据
    var fieldTypeData = sheetData.data[1];//字段类型数据
    var noteData = sheetData.data[2];//注释数据

    //遍历列
    for (var j = 0; j < fieldData.length; j++) {
        code += "\n\n";
        var field = fieldData[j];//将首字母置为大写
        var letterField = util.upperFirstLetter(fieldData[j]);//将首字母置为大写
        var fieldType = fieldTypeData[j];
        var note = noteData[j];
        var ruleList = [{regular: "#.*?#", replaceString: note}, {
            regular: "&.*?&",
            replaceString: letterField
        }, {regular: "%.*?%", replaceString: field}, {regular: "@.*?@", replaceString: fieldType}];
        var getSetCode = util.replaceCodeTemplateString(ruleList, getSetCodeTemplate);
        getSetCode = getSetCode.replace(/\n+$/g, "");
        getSetCode += ",";
        code += getSetCode;
    }

    code = code.replace(/,+$/g, "");
    code += "\n";
    code += "});";

    return code;
};

function initXlsFileList() {
    travel(xlsxRootPath, function (pathName) {
        xlsFileList.push(pathName);
    });
};

function travel(dir, callback) {
    var files = fs.readdirSync(dir);
    for (var i in files) {
        var file = files[i];
        var pathName = path.join(dir, file);
        if (fs.statSync(pathName).isDirectory()) {
            travel(pathName, callback);
        } else {
            var ext = path.extname(pathName);
            if (ext === ".xlsx" || ext === ".xls") {
                callback(pathName);
            }
        }
    }
};

function deleteOldFile() {
    deleteFile(configObjectRootPath);
    deleteFile(configRootPath);
};

function deleteFile (dir) {
    var folder_exists = fs.existsSync(dir);
    if (folder_exists == true) {
        var dirList = fs.readdirSync(dir);
        dirList.forEach(function (fileName) {
            fs.unlinkSync(dir + fileName);
        });
    }
};

if (module == require.main) {
    initCodeTemplate();
    initXlsFileList();
    deleteOldFile();
    for (var i in xlsFileList) {
        generatorConfigObjectCodeFile(xlsFileList[i]);
    }
};
