var fs = require('fs');
var path = require('path');
var xlsx = require('node-xlsx');

var basePath     = path.join(__dirname, '/');
var mappingFile  = path.join(basePath, 'effect.xlsx');
var effectFile   = path.join(basePath, 'MusicEffectFiles.js');

var generator = function () {
	var mappingData = xlsx.parse(mappingFile);
	// 写音效文件
	var effectMap = {};
	var effectSheet = 0;
	for(var row = 1; row < mappingData[effectSheet].data.length; row++) {
		var filename = mappingData[effectSheet].data[row][1];
		var key = "Audio_" + filename;
		effectMap[key] = 'res/sound/' + filename;
	}

	try {
		fs.writeFile(effectFile, 'var MusicEffectFiles = ' + JSON.stringify(effectMap, null, 4) + ';');
		console.log("MusicEffectFiles.js 生成成功");
	}
	catch(e) {
		console.log('Write effect file failed');
	}
};

if (module == require.main) {
	generator();
};


