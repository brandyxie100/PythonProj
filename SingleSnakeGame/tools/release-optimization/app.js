
var fs = require('fs');
var path = require('path');
var imagemin = require('imagemin');
var imageminMozjpeg = require('imagemin-mozjpeg');
var imageminPngquant = require('imagemin-pngquant');
var directoryPath = path.join(__dirname, '..', '..', 'publish/html5');

console.log('\r\n开始优化资源=========================');

function getResRecursive (_path, filter, container) {
    if (fs.existsSync(_path)) {
        var files = fs.readdirSync(_path);
        files.forEach(function (file, index) {
            var curPath = path.join(_path, file);
            if(fs.statSync(curPath).isDirectory()) {
              getResRecursive(curPath, filter, container);
            } else { 
              if (filter.test(curPath)) {
                var exists = container[file];
                if (exists) {
                    var randomName = parseInt(new Date().getTime() * Math.random());
                    container[randomName + '_' + file] = {
                        path: curPath,
                        originName: file
                    }
                } else {
                    container[file] = {
                        path: curPath
                    }
                }

              }
            }
        });
    }
}

function copyFile (source, target, cb) {

    var cbCalled = false;
    var rd = fs.createReadStream(source);
    rd.on("error", done);

    var wr = fs.createWriteStream(target);
    wr.on("error", done);
    wr.on("close", function() {
        done();
    });
    rd.pipe(wr);

    function done(err) {
        if (!cbCalled) {
            cbCalled = true;
            if (err) {
                console.log('拷贝出错');
            }
            cb && cb(err);
        }
    }
}

function deleteFolderRecursive (_path) {
    if (fs.existsSync(_path)) {
        var files = fs.readdirSync(_path);
        files.forEach(function (file, index) {
            var curPath = path.join(_path, file);
            if (fs.statSync(curPath).isDirectory()) {
              deleteFolderRecursive(curPath);
            } else { 
              fs.unlinkSync(curPath);
            }
        });
        try {
          fs.rmdirSync(_path);
        } catch (e) {
          console.log(e)
        }
    }
};


var fileOptimization = function (options) {
    this.filter = options.filter;
    this.tempPath = options.tempPath;
    this.optimizedPath = options.optimizedPath;
    this.desc = options.desc || '';
    this.onOptimizate = options.onOptimizate || function () {};
    this.data = {};
    this.start();
};

fileOptimization.prototype = {

    start: function () {

        var filter = this.filter;
        var tempPath = this.tempPath;
        var optimizedPath = this.optimizedPath;

        getResRecursive(directoryPath, filter, this.data);
        deleteFolderRecursive(tempPath);
        deleteFolderRecursive(optimizedPath);

        fs.mkdirSync(tempPath);
        fs.mkdirSync(optimizedPath);
        this.copyToTemp()

    },

    copyToTemp: function () {

        console.log('正在拷贝' + this.desc);

        var _self = this;
        var len = Object.keys(this.data).length;

        var cb = function () {
            len--;
            if (len <= 0) {
                _self.onOptimizate.call(_self);
            }
        }

        for (var key in this.data) {

            var item = this.data[key];
            var name = key;
            var tempPath = this.tempPath;
            var tgtPath = path.join(tempPath, name);

            copyFile(item.path, tgtPath, function (err) {
                if (err) {
                    console.log(err)
                } else {
                    cb()
                }
            })
        }

    },

    copyOptimized: function () {

        var _self = this;
        var desc = this.desc;

        console.log('优化' + desc + '完毕, 拷贝回目录');

        var optimizedPath = this.optimizedPath;
        var optimizedFiles = fs.readdirSync(optimizedPath);

        var len = optimizedFiles.length;
        var cb = function () {
            len--;
            if (len <= 0) {
               console.log(desc + '优化完成!')
            }
        };

        optimizedFiles.forEach(function (file) {
            var item = _self.data[file];

            if (item) {
                copyFile(path.join(optimizedPath, file), item['path'], function (err) {
                    if (err) {
                        console.log(err)
                    } else {
                        cb()
                    }
                })
            } else {
                console.log('异常文件: ' + file)
            }
        })

    }
};


var imageOptimization = new fileOptimization({
    filter: /(\.png|\.jpg|\.jpeg)$/,
    tempPath: path.join(__dirname, '__tempImage'),
    optimizedPath: path.join(__dirname, '__optimizedImage'),
    desc: '图片',
    onOptimizate: function () {

        var _self = this;
        var tempPath = this.tempPath;
        var optimizedPath = this.optimizedPath;

        var _compareImage = function () {
            tempImageFiles = fs.readdirSync(tempPath);
            optimizedImageFiles = fs.readdirSync(optimizedPath);

            var unOptiFiles = [];
            tempImageFiles.forEach(function (file) {
                if (optimizedImageFiles.indexOf(file) < 0) {
                    unOptiFiles.push(file)
                }
            });

            var len = unOptiFiles.length;
            var cb = function () {
                len--;
                if (len <= 0) {
                   _self.copyOptimized()
                }
            };

            unOptiFiles.forEach(function (file) {
                copyFile(path.join(tempPath, file), path.join(optimizedPath, file), function (err) {
                    if (err) {
                        console.log(err)
                    } else {
                        cb()
                    }
                })
            });
        };

        imagemin([tempPath + '/*.{jpg,png}'], optimizedPath, {
            plugins: [
                imageminMozjpeg(),
                imageminPngquant({quality: '50-80'})
            ]
        }).then(function (files) {
            _self.copyOptimized()
        }, function (err) {
            //出现无法按要求优化的文件
            setTimeout(function () {
                _compareImage()
            }, 2000)
        });

    }
});

var jsonOptimization = new fileOptimization({
    filter: /\.json$/,
    tempPath: path.join(__dirname, '__tempJson'),
    optimizedPath: path.join(__dirname, '__optimizedJson'),
    desc: 'json',
    onOptimizate: function () {

        var _self = this;
        var tempPath = this.tempPath;
        var optimizedPath = this.optimizedPath;
        var tempJsonFiles = fs.readdirSync(tempPath);

        var len = tempJsonFiles.length;
        var cb = function () {
            len--;
            if (len <= 0) {
                _self.copyOptimized()
            }
        };

        tempJsonFiles.forEach(function(file) {

            var content = '';
            var fileReadStream = fs.createReadStream(path.join(tempPath, file), {flags: 'r', encoding : 'utf8'});
            fileReadStream.on('data', function (data) {
                content += data;
            });
            fileReadStream.once('end', function () {
                try {
                    var compressedString = JSON.stringify(JSON.parse(content));
                    var fileWriteStream = fs.createWriteStream(path.join(optimizedPath, file));
                    fileWriteStream.write(compressedString);
                    fileWriteStream.end(function () {
                        cb()
                    });
                    
                } catch (e) {
                    console.log(e)
                    console.log('json压缩失败')
                }
            });

        })

    }
});

var plistOptimization = new fileOptimization({
    filter: /(\.plist|\.xml)$/,
    tempPath: path.join(__dirname, '__tempPlist'),
    optimizedPath: path.join(__dirname, '__optimizedPlist'),
    desc: 'plist',
    onOptimizate: function () {

        var _self = this;
        var tempPath = this.tempPath;
        var optimizedPath = this.optimizedPath;
        var tempPlistFiles = fs.readdirSync(tempPath);

        var len = tempPlistFiles.length;
        var cb = function () {
            len--;
            if (len <= 0) {
                _self.copyOptimized()
            }
        };

        tempPlistFiles.forEach(function(file) {

            var content = '';
            var fileReadStream = fs.createReadStream(path.join(tempPath, file), {flags: 'r', encoding : 'utf8'});
            fileReadStream.on('data', function (data) {
                content += data;
            });
            fileReadStream.once('end', function () {
                try {
                    var compressedString = content.replace(/\<![ \r\n\t]*(--([^\-]|[\r\n]|-[^\-])*--[ \r\n\t]*)\>/g,"").replace(/>\s{0,}</g,"><");
                    var fileWriteStream = fs.createWriteStream(path.join(optimizedPath, file));
                    fileWriteStream.write(compressedString);
                    fileWriteStream.end(function () {
                        cb()
                    });
                    
                } catch (e) {
                    console.log(e)
                    console.log('plist压缩失败')
                }
            });

        })

    }
});