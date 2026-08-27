/**
 * StringResParser is a singleton object for parsing string resource files
 *
 * Created by alexgan on 2015/5/8.
 *
 * Resouces file structure:
 * <?xml version="1.0" encoding="utf-8"?>
 * <resources>
 * <string name="key">value</string>
 * …
 * </resources>
 *
 * Usage:
 * var stringResParser = StringResParser.getInstance();
 * stringResParser.parse(xmlStr);
 * stringResParser.getString("key");
 *
 */

var StringResParser = cc.Class.extend({
    _dict: null,

    ctor: function () {
        // 如果已经缓存了实例，则直接返回缓存的实例
        if (typeof StringResParser._instance === 'object') {
            return StringResParser._instance;
        }
        // 缓存实例
        StringResParser._instance = this;
        return this;
    },

    /**
     * parse a xml string as dict object.
     *
     * @param {String} xmlTxt xml contents
     * @return {*} dict object
     */
    parseXml: function (xmlTxt) {
        this._dict = this._dict || {};

        var parser = new marknote.Parser();
        var xmlDoc = parser.parse(xmlTxt);

        var root = xmlDoc.getRootElement();
        if (root.getName() !== 'resources')
            throw "Not a resources file!";

        // Get first real node
        var node = null;
        var childElements = root.getChildElements();
        for (var i = 0, len = childElements.length; i < len; i++) {
            node = childElements[i];
            this._parseNode(node);
        }
        xmlDoc = null;

        return this._dict;
    },

    _parseNode: function (node) {
        if (node.getName() === "string") {
            this._dict[node.getAttributeValue("name")] = node.getText();
        }
    },

    /**
     * parse a json string as dict object.
     *
     * @param {String} jsonTxt json contents
     * @return {*} dict object
     */
    parse: function (jsonTxt) {
        this._dict = this._dict || {};

        var jsonDoc = JSON.parse(jsonTxt);
        for (var i in jsonDoc.string) {
            var item = jsonDoc.string[i];
            this._dict[item.name] = item.text;
        }
        return this._dict;
    },

    /**
     * get a value that map the given key in dict object,
     * otherwise return the input key directly.
     *
     * @param {String} key
     * @return {String} value
     */
    getString: function (key) {
        return this._dict[key] || key;
    }
});

StringResParser.GetInstance = function () {
    if (typeof StringResParser._instance !== 'object') {
        StringResParser._instance = new StringResParser();
    }
    return StringResParser._instance;
};
