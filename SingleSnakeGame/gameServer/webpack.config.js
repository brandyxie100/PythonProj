//module.exports = {
//  entry: './server/server.js',
//  output: {
//    filename: 'bundle.js'
//  }
//};

var webpack = require('webpack');
var uglifyJsPlugin = webpack.optimize.UglifyJsPlugin;

module.exports = {
    entry: {
        'serverLogic': './server/server.js'
    },
    output: {
        filename: 'bundle.js',
        library: 'serverLogic',
        libraryTarget: 'umd',
        umdNamedDefine: true
    },
    module: {
        loaders: [
            {test: /\.js[x]?$/, exclude: /node_modules/, loader: 'babel-loader?presets[]=es2015'}
        ]
    },
    node: {
        global: true,
        process: false,
        Buffer: false
    },
    externals: {},
    plugins: [
        new uglifyJsPlugin({
            compress: {
                warnings: false
            }
        })]
};
