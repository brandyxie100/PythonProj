/**
 * Created by malloyzhu on 2015/7/23.
 */

var Direction = {leftToRight: 1, rightToLeft: 2, topToBottom: 3, bottomToTop: 4};

var UIHelper = {
    _extendListArray: [],

    /**
     * Calculate the scale ratio for SHOW_ALL mode
     *
     * @param designSize {cc.size}
     * @param containerSize {cc.size}
     * @returns {float}
     */
    calculateShowAllScale: function (designSize, containerSize) {
        var containerW = containerSize.width, containerH = containerSize.height,
            designW = designSize.width, designH = designSize.height,
            scaleX = containerW / designW, scaleY = containerH / designH, scale = 0,
            contentW, contentH;

        (scaleX < scaleY) ? (scale = scaleX, contentW = containerW, contentH = designH * scale)
            : (scale = scaleY, contentW = designW * scale, contentH = containerH);

        return scale;
    },

    /**
     * 将 widgetCopy 的属性拷贝到 widget 中
     * @param widget：要拷贝的 widget
     * @param widgetCopy：被拷贝的 widget
     */
    copyProperties: function (widget, widgetCopy) {
        if (cc.sys.isNative) {
            widget.copyProperties(widgetCopy);
        } else {
            widget._copyProperties(widgetCopy);
        }
    },

    /**
     * 水平居中放置
     * @param views：要水平居中放置的视图列表
     * @param midX：中点值
     * @param horizontalInterval：水平间隔
     */
    horizontalCenterPlace: function (views, midX, horizontalInterval) {
        if (null == views) {
            return;
        }
        if (!Util.isArray(views)) {
            return;
        }
        if (0 == views.length) {
            return;
        }

        horizontalInterval = horizontalInterval || 0;
        var y = views[0].getPositionY();
        var startX = midX;
        var width = views[0].getContentSize().width;
        var count = views.length;

        var lastX = (width + horizontalInterval) * count;
        var firstX = (width + horizontalInterval) * 1;
        var offsetX = -((lastX - firstX) / 2);
        for (var i = 0; i < count; i++) {
            var x = startX + (width + horizontalInterval) * i + offsetX;
            views[i].setPosition(cc.p(x, y));
        }
    },

    /**
     * * 排序多个 view 的位置
     * @param views ：view 列表
     * @param viewHorizontalSpacing ：两个 view 之间的水平间距
     * @param midX ：中心坐标，用于 views 偏移
     * @param sortDirection : 排序方向
     */
    sortViewsPosition: function (views, viewHorizontalSpacing, midX, sortDirection) {
        if (!Util.isArray(views)) {
            return;
        }

        sortDirection = sortDirection || Direction.leftToRight;

        var firstIndex = (sortDirection == Direction.leftToRight ? 0 : views.length - 1);
        if (1 == views.length) {
            return;
        }

        var parent = views[0].getParent();
        if (null == parent) {
            console.log("parent is null");
            return;
        }

        for (var i = 1; i < views.length; i++) {
            if (views[i].getParent() !== parent) {
                console.log("parent not same");
                return;
            }
        }

        viewHorizontalSpacing = viewHorizontalSpacing || 0;

        var nextPositionX = 0;
        nextPositionX = _updateNextPositionX(views[firstIndex], nextPositionX, sortDirection);

        var viewsCount = views.length;
        if (Direction.leftToRight == sortDirection) {
            for (var i = 1; i < viewsCount; i++) {
                _setViewPosition(views[i], nextPositionX, sortDirection);
                nextPositionX = _updateNextPositionX(views[i], nextPositionX, sortDirection);
            }
        } else if (Direction.rightToLeft == sortDirection) {
            for (var i = viewsCount - 2; i >= 0; i--) {
                _setViewPosition(views[i], nextPositionX, sortDirection);
                nextPositionX = _updateNextPositionX(views[i], nextPositionX, sortDirection);
            }
        }

        if (null != midX) {
            var totalWidth = 0;
            for (var i in views) {
                var width = views[i].getContentSize().width;
                var scaleX = views[i].getScaleX();
                totalWidth += (width * scaleX + viewHorizontalSpacing);
            }
            totalWidth -= viewHorizontalSpacing;

            var firstView = views[0];
            var firstViewSize = firstView.getContentSize();
            var firstViewAnchor = firstView.getAnchorPoint();
            var firstViewScaleX = firstView.getScaleX();
            var firstViewParent = firstView.getParent();
            var firstViewWorldPosition = cc.p(firstViewParent.getPositionX() + firstView.getPositionX(), firstViewParent.getPositionY() + firstView.getPositionY());
            var firstViewLeftPositionX = firstViewWorldPosition.x - (firstViewSize.width * firstViewAnchor.x * firstViewScaleX);
            var offsetX = midX - (firstViewLeftPositionX + totalWidth / 2);
            for (var i in views) {
                views[i].setPositionX(views[i].getPositionX() + offsetX);
            }
        }

        //更新下一个 x 坐标
        function _updateNextPositionX(view, nextPositionX, sortDirection) {
            var viewPosition = view.getPosition();
            var viewContentSize = view.getContentSize();
            var viewAnchorPoint = view.getAnchorPoint();
            var scaleX = view.getScaleX();
            if (Direction.leftToRight == sortDirection) {
                nextPositionX = viewPosition.x + viewContentSize.width * (1 - viewAnchorPoint.x) * scaleX + viewHorizontalSpacing;
            } else if (Direction.rightToLeft == sortDirection) {
                nextPositionX = viewPosition.x - (viewContentSize.width * viewAnchorPoint.x) * scaleX - viewHorizontalSpacing;
            }
            return nextPositionX;
        }

        //设置 view 位置
        function _setViewPosition(view, nextPositionX, sortDirection) {
            var viewContentSize = view.getContentSize();
            var viewAnchorPoint = view.getAnchorPoint();
            var viewScaleX = view.getScaleX();
            var positionX = 0;
            if (Direction.leftToRight == sortDirection) {
                positionX = nextPositionX + viewContentSize.width * viewAnchorPoint.x * viewScaleX;
            } else if (Direction.rightToLeft == sortDirection) {
                positionX = nextPositionX - viewContentSize.width * (1 - viewAnchorPoint.x) * viewScaleX;
            }
            view.setPositionX(positionX);
        }
    },

    loadUI: function (filePath) {
        var rootJson = ccs.load(filePath);
        var rootNode = rootJson.node;
        this.setRootNode(rootNode);
        return rootNode;
    },

    setRootNode: function (rootNode) {
        this._rootNode = rootNode;
    },

    seekWidget: function (name, bIgnoreSize, rootNode) {
        rootNode = rootNode || this._rootNode;
        var widget = ccui.helper.seekWidgetByName(rootNode, name);
        if (null == widget) {
            console.log("widget is null");
        }
        widget.ignoreContentAdaptWithSize(bIgnoreSize);
        return widget;
    },

    updateUITextContentSize: function (object) {
        if (this.isUITextObject(object)) {
            var chars = object.getString();
            var charsLength = Util.getStringLength(chars);
            var fontSize = object.getFontSize();
            var width = charsLength * fontSize * 0.5;
            var contentSize = object.getContentSize();
            object.setContentSize(cc.size(width, contentSize.height));
        }
    },

    /**
     * 设置tableView的滚动条
     * @param tableView  : tableView对象
     * @param cellSize  : cell的尺寸
     * @param cellNum   : cell的数量
     * @param slider1   :   滑块
     * @param bar   : 滚动条
     * @param bar_length    : 滚动条长度
     * @param direct    : 滚动方向(1表示垂直滚动)
     */
    setSliderPosOfTableView: function (tableView, cellSize, cellNum, slider1, bar, bar_length, direct) {
        var viewSize = tableView.getViewSize();


        if (1 == direct) {
            if (viewSize.height >= cellSize.height * cellNum) {
                slider1.setVisible(false);
                bar.setVisible(false);
                return;
            } else {
                slider1.setVisible(true);
                bar.setVisible(true);
            }

            var deltaHeight = cellSize.height * cellNum - viewSize.height;
            var ratio = Math.min(deltaHeight, Math.max(0, -tableView.getContentOffset().y)) / deltaHeight;

            slider1.height = bar_length * (viewSize.height / (cellSize.height * cellNum));
            slider1.y = ratio * (bar_length - slider1.height);
        }
    },

    /**
     * 给ccui.ListView列表绑定滚动条
     * @param listView : 列表
     * @param slider1 : 滑动块1
     * @param slider2 : 滑动块2
     * @param bar_length : 滚动条长度
     * @param direct : 滚动方向
     */
    bindSliderToListView: function (listView, slider1, slider2, bar_length, direct) {
        var globalScheduler = GlobalScheduler.getInstance();
        globalScheduler.addListViewSlideUpdate(listView, slider1, slider2, bar_length, direct,
            function (handler) {
                var _listView = handler._listView;
                var _slider1 = handler._slider1;
                var _slider2 = handler._slider2;
                var _bar_length = handler._bar_length;
                var _direct = handler._direct;

                var innerContainerSize = _listView.getInnerContainerSize();
                var viewSize = _listView.getContentSize();
                if (innerContainerSize.height <= viewSize.height) {
                    _slider1.setVisible(false);
                    _slider2.setVisible(false);
                    return;
                } else {
                    _slider1.setVisible(true);
                    _slider2.setVisible(true);
                }

                var deltaHeight = innerContainerSize.height - viewSize.height;
                var ratio = Math.min(deltaHeight, Math.max(0, _listView.getBottomBoundary() - _listView.getInnerContainer().y)) / deltaHeight;
                if (handler._last_ratio == ratio) {
                    //位置没有变化，直接返回
                    return;
                }

                handler._last_ratio = ratio;

                var halfSliderHeight = _slider1.height / 2;
                var sliderPosY = (_bar_length - _slider1.height) * ratio + halfSliderHeight;
                _slider1.y = sliderPosY;
                _slider2.y = sliderPosY;

            }
        );
    },

    /**
     * 给ccui.ListView解绑滚动条
     * @param listView
     */
    unBindSliderToListView: function (listView) {
        var globalScheduler = GlobalScheduler.getInstance();
        globalScheduler.removeListViewSlideUpdate(listView);
    },

    /**
     * 图标依附一个红点提示
     * @param icon : 图标
     * @param pos : 位置
     */
    attachRedPot: function (icon, pos) {
        var redPot = icon.getChildByTag(1);
        if (redPot == null) {
            redPot = new cc.Sprite("res/scene/common_ui/red_pot.png");
            redPot.setTag(1);
            if (pos != null) {
                redPot.setPosition(pos);
            } else {
                redPot.setPosition(icon.width * 0.8, icon.height * 0.8);
            }
            icon.addChild(redPot);
        }
        redPot.setVisible(true);
    },

    /**
     * 分离图标的红点显示
     * @param icon
     */
    detachRedPot: function (icon) {
        var redPot = icon.getChildByTag(1);
        if (redPot != null) {
            redPot.setVisible(false);
        }
    },

    /**
     * 调整ui布局（针对多分辨率适配调整）
     * @param rootNode
     */
    adjustUILayout: function (rootNode) {
        console.log("adjustUILayout");
        if (null == rootNode) {
            console.log("null == rootNode");
            return;
        }
        var winSize = cc.winSize;
        //var designSize = GameCommonDef.DESIGN_RESOLUTION_SIZE;
        //if (designSize.width == winSize.width && designSize.height == winSize.height) {
        //    return;
        //}
        //modify max width and height
        winSize.height = winSize.height > 750 ? 750 : winSize.height;
        console.log("winSize.width= " + winSize.width);
        console.log("winSize.height= " + winSize.height);

        if (GameCommonDef.RESOLUTION_POLICY == cc.ResolutionPolicy.FIXED_HEIGHT) {
            console.log("UIHelper:adjustUILayout:FIXED_HEIGHT");
            //var rootSize = rootNode.getContentSize();
            //var deltaWidth = winSize.width - rootSize.width;

            var bgImage = ccui.helper.seekWidgetByName(rootNode, "bgImage");
            if (bgImage != null) {
                bgImage.x = winSize.width / 2;
                //var bgSize = bgImage.getContentSize();
                var scaleX = winSize.width / 1334;
                var scaleY = winSize.height / 750;
                cc.log("scaleX: " + scaleX + ", scaleY: " + scaleY);

                //背景
                bgImage.setScale(scaleX > scaleY ? scaleX : scaleY);
            }

            var topPanel = ccui.helper.seekWidgetByName(rootNode, "topPanel");
            if (topPanel != null) {
                topPanel.x = winSize.width / 2;
            }

            var bottomPanel = ccui.helper.seekWidgetByName(rootNode, "bottomPanel");
            if (bottomPanel != null) {
                bottomPanel.x = winSize.width / 2;
            }

            var rightPanel = ccui.helper.seekWidgetByName(rootNode, "rightPanel");
            if (rightPanel != null) {
                rightPanel.x = winSize.width;
            }

            var middlePanel = ccui.helper.seekWidgetByName(rootNode, "middlePanel");
            if (middlePanel != null) {
                middlePanel.x = winSize.width / 2;
            }
        }
    },

    /**
     * 调整背景图片（针对多分辨率适配调整）
     * @param bgImage
     */
    adjustBgImage: function (bgImage) {
        var winSize = cc.winSize;
        var designSize = GameCommonDef.DESIGN_RESOLUTION_SIZE;
        //if (designSize.width == winSize.width && designSize.height == winSize.height) {
        //    return;
        //}
        //modify max width and height
        winSize.height = winSize.height > 750 ? 750 : winSize.height;

        if (GameCommonDef.RESOLUTION_POLICY == cc.ResolutionPolicy.FIXED_WIDTH) {
            cc.log("UIHelper:adjustBgImage");
            if (bgImage != null) {
                bgImage.y = winSize.height / 2;
                //var bgSize = bgImage.getContentSize();
                var scaleX = winSize.width / 1334;
                var scaleY = winSize.height / 750;
                cc.log("scaleX: " + scaleX + ", scaleY: " + scaleY);

                //背景
                bgImage.setScale(scaleX > scaleY ? scaleX : scaleY);
            }
        } else if (GameCommonDef.RESOLUTION_POLICY == cc.ResolutionPolicy.FIXED_HEIGHT) {
            if (bgImage != null) {
                bgImage.x = winSize.width / 2;
                //    var bgSize = bgImage.getContentSize();
                var scaleX = winSize.width / designSize.width;
                var scaleY = winSize.height / designSize.height;
                cc.log("scaleX: " + scaleX + ", scaleY: " + scaleY);

                //背景
                bgImage.setScale(scaleX > scaleY ? scaleX : scaleY);
            }
        }


    },

    setGrayImageView: function (imageView, filename) {
        //得到纹理
        var texture /*= cc.textureCache.getTextureForKey(filename)*/;
        if (!texture) {
            texture = cc.textureCache.addImage(filename);
        }

        //判断运行的平台是不是浏览器
        var isHtml5 = (typeof document != 'undefined');
        if (isHtml5) {
            var canvas = document.createElement('canvas');
            var image = texture.getHtmlElementObj();

            //将图片的高宽赋值给画布
            canvas.width = image.width;
            canvas.height = image.height;

            //获得二维渲染上下文
            if (canvas.getContext) {//为了安全起见，先判断浏览器是否支持canvas
                var context = canvas.getContext("2d");
                context.drawImage(image, 0, 0);//将得到的image图像绘制在canvas对象中
                var canvasData = context.getImageData(0, 0, canvas.width, canvas.height);//返回ImageData对象

                // 填充灰色【读取像素值和实现灰度计算】
                for (var x = 0; x < canvasData.width; x++) {
                    for (var y = 0; y < canvasData.height; y++) {
                        // Index of the pixel in the array
                        var idx = (x + y * canvasData.width) * 4;
                        var r = canvasData.data[idx + 0];
                        var g = canvasData.data[idx + 1];
                        var b = canvasData.data[idx + 2];
                        // 灰度的计算
                        var gray = .299 * r + .587 * g + .114 * b;
                        // assign gray scale value
                        canvasData.data[idx + 0] = gray; // Red channel
                        canvasData.data[idx + 1] = gray; // Green channel
                        canvasData.data[idx + 2] = gray; // Blue channel
                        //canvasData.data[idx + 3] = 255; // Alpha channel
                        // 新增黑色边框
                        if (x < 8 || y < 8 || x > (canvasData.width - 8) || y > (canvasData.height - 8)) {
                            canvasData.data[idx + 0] = 0;
                            canvasData.data[idx + 1] = 0;
                            canvasData.data[idx + 2] = 0;
                        }
                    }
                }
                context.putImageData(canvasData, 0, 0); // 处理完成的数据重新载入到canvas二维对象中

                var tempTexture = new cc.Texture2D();
                tempTexture.initWithElement(canvas);
                tempTexture.handleLoadedTexture();

                return imageView._imageRenderer.setTexture(tempTexture);
            }
        }

        //使用shader方式实现图片变灰（适用于app和浏览器不支持canvas的情况）
        if (!cc.GLProgram.createWithByteArrays) {
            cc.GLProgram.createWithByteArrays = function (vert, frag) {
                var shader = new cc.GLProgram();
                shader.initWithVertexShaderByteArray(vert, frag);
                shader.link();
                shader.updateUniforms();
                setTimeout(function () {
                    shader.link();
                    shader.updateUniforms();
                }, 0);
                return shader;
            }
        }

        var SHADER_POSITION_GRAY_FRAG =
            "varying vec4 v_fragmentColor;\n" +
            "varying vec2 v_texCoord;\n" +
            (isHtml5 ? "uniform sampler2D CC_Texture0;\n" : "") +
            "void main()\n" +
            "{\n" +
            "    vec4 v_orColor = v_fragmentColor * texture2D(CC_Texture0, v_texCoord);\n" +
            "    float gray = dot(v_orColor.rgb, vec3(0.299, 0.587, 0.114));\n" +
            "    gl_FragColor = vec4(gray, gray, gray, v_orColor.a);\n" +
            "}\n";

        var SHADER_POSITION_GRAY_VERT =
            "attribute vec4 a_position;\n" +
            "attribute vec2 a_texCoord;\n" +
            "attribute vec4 a_color;\n" +
            "\n" +
            "varying vec4 v_fragmentColor;\n" +
            "varying vec2 v_texCoord;\n" +
            "\n" +
            "void main()\n" +
            "{\n" +
            "    gl_Position = " + (isHtml5 ? "(CC_PMatrix * CC_MVMatrix)" : "CC_PMatrix") + " * a_position;\n" +
            "    v_fragmentColor = a_color;\n" +
            "    v_texCoord = a_texCoord;\n" +
            "}";

        var sprite = imageView._imageRenderer;
        sprite.setTexture(texture);

        var shader = cc.GLProgram.createWithByteArrays(SHADER_POSITION_GRAY_VERT, SHADER_POSITION_GRAY_FRAG);
        shader.addAttribute(cc.ATTRIBUTE_NAME_POSITION, cc.VERTEX_ATTRIB_POSITION);
        shader.addAttribute(cc.ATTRIBUTE_NAME_COLOR, cc.VERTEX_ATTRIB_COLOR);
        shader.addAttribute(cc.ATTRIBUTE_NAME_TEX_COORD, cc.VERTEX_ATTRIB_TEX_COORDS);
        sprite.setShaderProgram(shader);
    },

    /**
     * 将文本内容按行宽分段并设置到文本控件中
     * @param uiText：文本控件
     * @param str：文本内容
     * @param lineWidth：行宽
     */
    subsectionTextForUIText: function (uiText, str, lineWidth) {
        if (!this.isUITextObject(uiText)) {
            console.log("uiText parameter error");
            return;
        }

        if (typeof(lineWidth) !== 'number' || lineWidth <= 0) {
            console.log("lineWidth parameter error");
            return;
        }

        if (lineWidth < uiText.getFontSize()) {
            console.log("lineWidth less than fontSize");
            return;
        }

        if (typeof(str) !== 'string') {
            console.log("str parameter error");
            return;
        }

        uiText.ignoreContentAdaptWithSize(false);
        uiText.setTextAreaSize(cc.size(lineWidth, 0));
        uiText.setString(str);
        uiText.setTextAreaSize(uiText.getVirtualRendererSize());
    },

    isNodeObject: function (object) {
        return (object instanceof cc.Node);
    },

    isUISliderObject: function (object) {
        return (object instanceof ccui.Slider);
    },

    isWidgetObject: function (object) {
        return (object instanceof ccui.Widget);
    },

    isUITextObject: function (object) {
        return (object instanceof ccui.Text);
    },

    isUITextFieldObject: function (object) {
        return (object instanceof ccui.TextField);
    },

    isUIButtonObject: function (object) {
        return (object instanceof ccui.Button);
    },

    isUIImageViewObject: function (object) {
        return (object instanceof ccui.ImageView);
    },

    isUIPanelObject: function (object) {
        return (object instanceof ccui.Layout);
    },

    isUIListViewObject: function (object) {
        return (object instanceof ccui.ListView);
    },

    isUIPageViewObject: function (object) {
        return (object instanceof ccui.PageView);
    },

    isUIScrollViewObject: function (object) {
        return (object instanceof ccui.ScrollView);
    },

    isUIScale9SpriteObject: function (object) {
        return (object instanceof ccui.Scale9Sprite);
    },

    isSpriteObject: function (object) {
        return (object instanceof cc.Sprite);
    },

    /**
     * 绑定 UI 控件
     * @param object：被绑定的对象
     * @param uiFilePath：ui 文件路径
     *
     * eg：ui 文件中的所有控件都绑定到 object 中，命名规则为 下划线 + 控件名字（控件名以下划线开头的才会被绑定到 object 上）
     * 如 ui 中有个名字为 _backBtn 的按钮，则通过 object._backBtn 可得到对应名字的对象
     * 注册事件：只需要在 object 中定义函数名，事件函数名命名规则为 下划线 + 控件名字 + Touched
     * 如有个名字为 _backBtn 的按钮要注册事件，如果在 object 中定义了 _onBackBtnTouched，
     * 则会将事件函数绑定到 _backBtn 上，如没有则不会绑定，绑定事件的控件有
     * Button, ListView, PageView, ScrollView 4种类型的控件，代码详见 bindUIWidgetTouchListener
     */
    bindUIWidget: function (object, uiFilePath) {
        var uiRoot = this.loadUI(uiFilePath);
        this.bindUIWidgetToObject(object, uiRoot);
        return uiRoot;
    },

    /**
     * 绑定 UI 控件
     * @param object：被绑定的对象
     * @param uiRoot：ui 根
     */
    bindUIWidgetToObject: function (object, uiRoot) {
        if (!Util.isObject(object)) {
            console.log("object is not object type");
            return;
        }

        if (!this.isNodeObject(uiRoot)) {
            console.log("uiRoot is not node type");
            return;
        }

        var uiWidgetChildren = uiRoot.getChildren();
        for (var i = 0; i < uiWidgetChildren.length; i++) {
            var uiWidget = uiWidgetChildren[i];
            this._ignoreContentSize(uiWidget);
            this._handleUIWidget(object, uiWidget);
            this._handleSortViewGroup(object, uiWidget);
            this.bindUIWidgetToObject(object, uiWidget);
        }
    },

    _handleUIWidget: function (object, uiWidget) {
        var uiWidgetName = uiWidget.getName();
        //只绑定命名以下划线开头的控件
        if (Util.startsWithString(uiWidgetName, '_')) {
            object[uiWidgetName] = uiWidget;
            this.bindUIWidgetTouchListener(object, uiWidget);
        }
    },

    _handleSortViewGroup: function (object, uiWidget) {
        var uiWidgetName = uiWidget.getName();
        if (Util.endsWithString(uiWidgetName, '_')) {
            uiWidget.setBackGroundColorType(ccui.Layout.BG_COLOR_NONE);
            uiWidget.setTouchEnabled(false);

            var uiWidgets = uiWidget.getChildren();
            var sortViews = [];
            for (var i in uiWidgets) {
                sortViews.push(uiWidgets[i]);
            }

            sortViews.sort(function (a, b) {
                return (a.getPositionX() - b.getPositionX());
            });

            var sortViewGroup = new SortViewGroup();
            for (var j = 0; j < sortViews.length; j++) {
                var sortView = sortViews[j];
                sortViewGroup.addView(sortView);
            }
            var memberName = '_' + uiWidgetName.substring(0, uiWidgetName.length - 1);
            object[memberName] = sortViewGroup;

            if (object._sortViewGroupList == null) {
                object._sortViewGroupList = [];
            }
            object._sortViewGroupList.push(sortViewGroup);

            if (object.sortViewGroups == null) {
                object.sortViewGroups = function () {
                    for (var i in object._sortViewGroupList) {
                        object._sortViewGroupList[i].sort();
                    }
                }
            }
        }
    },

    _ignoreContentSize: function (uiWidget) {
        if (this.isUITextObject(uiWidget) || this.isUITextFieldObject(uiWidget)) {
            uiWidget.ignoreContentAdaptWithSize(true);
            var originalStr = uiWidget.getString();
            uiWidget.setString("");
            uiWidget.setString(originalStr);
        }
    },

    bindUIWidgetTouchListener: function (object, uiWidget) {
        if (!Util.isObject(object)) {
            console.log("object is not object type");
            return;
        }

        if (!this.isWidgetObject(uiWidget)) {
            console.log("uiWidget is not widget type");
            return;
        }

        var uiWidgetName = uiWidget.getName();
        if (!Util.startsWithString(uiWidgetName, '_')) {
            return;
        }

        //删除下划线
        uiWidgetName = uiWidgetName.substring(1);
        //将首字母转换为大写
        uiWidgetName = Util.upperFirstLetter(uiWidgetName);

        var touchListenerName = "_on" + uiWidgetName + "Touched";
        if (typeof object[touchListenerName] !== 'function') {
            return;
        }

        if (this.isUIButtonObject(uiWidget)) {
            uiWidget.addTouchEventListener(object[touchListenerName], object);
            return;
        }

        if (this.isUIListViewObject(uiWidget)) {
            uiWidget.addEventListener(object[touchListenerName], object);
            return;
        }

        if (this.isUIPageViewObject(uiWidget)) {
            uiWidget.addEventListener(object[touchListenerName], object);
            return;
        }

        if (this.isUIScrollViewObject(uiWidget)) {
            uiWidget.addEventListener(object[touchListenerName], object);
            return;
        }

        if (this.isUISliderObject(uiWidget)) {
            uiWidget.addEventListener(object[touchListenerName], object);
            return;
        }

        if (this.isUITextFieldObject(uiWidget)) {
            uiWidget.addEventListener(object[touchListenerName], object);
            return;
        }

        if (this.isUIPanelObject(uiWidget)) {
            uiWidget.addTouchEventListener(object[touchListenerName], object);
            return;
        }
    },

    /**
     * 灰化视图
     * @param view：需要灰化的视图，目前只提供 Sprite 和 UIImageView 灰化
     */
    grayView: function (view) {
        if (this.isSpriteObject(view)) {
            Filter.grayScale(view);
        } else if (this.isUIImageViewObject(view)) {
            var renderer = view.getImageRenderer();
            if (this.isSpriteObject(renderer)) {
                Filter.grayScale(renderer)
            } else {
                // renderer is Scale9Sprite object
                Filter.grayScale(renderer.getSprite());
            }
        }
    },

    /**
     * 取消灰化
     * @param view：需要取消灰化的视图，目前只提供 Sprite 和 UIImageView 取消灰化
     */
    unGrayView: function (view) {
        var program = cc.shaderCache.programForKey(cc.SHADER_POSITION_TEXTURECOLOR);
        if (this.isSpriteObject(view)) {
            view.setShaderProgram(program);
        } else if (this.isUIImageViewObject(view)) {
            var renderer = view.getImageRenderer();
            if (this.isSpriteObject(renderer)) {
                renderer.setShaderProgram(program);
            } else {
                // renderer is Scale9Sprite object
                renderer.getSprite().setShaderProgram(program);
            }
        }
    },

    /**
     * 显示弹出文字
     * @param container
     * @param tipsText
     */
    showPopUpTips: function (container, tipsText, fontSize, textColor, pos) {
        var label = new cc.LabelTTF(tipsText, "Arial", fontSize);
        if (textColor) {
            label.setColor(textColor);
        }
        label.setAnchorPoint(cc.p(0.5, 0.5));
        if (pos) {
            label.setPosition(pos);
        } else {
            var containerSize = container.getContentSize();
            label.setPosition(cc.p(containerSize.width / 2, containerSize.height / 2));
        }
        container.addChild(label, 100);
        var action = new cc.Sequence(cc.moveBy(0.5, cc.p(0, 50)), cc.removeSelf());
        label.runAction(action);
    },

    /**
     * 将视图排序成 n 列
     * @param startPosition：起始位置
     * @param viewList：视图列表
     * @param horizontalInterval：水平间隔
     * @param verticalInterval：垂直间隔
     * @param col：列数
     */
    sortViewNCol: function (startPosition, viewList, horizontalInterval, verticalInterval, col, direction) {
        viewList = Util.spliceListToNCol(viewList, col);

        if (viewList.length == 0) {
            return;
        }

        if (viewList[0].length == 0) {
            return;
        }

        var yOffset = startPosition.y;
        var viewSize = viewList[0][0].getContentSize();

        for (var row = 0; row < viewList.length; row++) {
            var rowView = viewList[row];
            for (var col = 0; col < rowView.length; col++) {
                var view = rowView[col];
                var xOffset = startPosition.x + (horizontalInterval + viewSize.width) * col;
                view.setPosition(xOffset, yOffset);
            }

            direction = direction || Direction.topToBottom;
            if (direction == Direction.topToBottom) {
                yOffset -= viewSize.height;
                yOffset -= verticalInterval;
            } else if (direction == Direction.bottomToTop) {
                yOffset += viewSize.height;
                yOffset += verticalInterval;
            } else {
                console.log("direction error");
            }
        }
    },

    release: function (object) {
        if (object && object.release) {
            object.release();
        }
    },

    retain: function (object) {
        if (object && object.retain) {
            object.retain();
        }
    },

    clipLongTextLabel: function (label, text, fontSize, maxWidth, clipedNum) {
        var preTime = new Date().getTime();
        var result = "";
        if (!label) {
            label = new cc.LabelTTF(text, "Arial", fontSize);
        }
        label.setString(text);
        if (label.getContentSize().width > maxWidth) {
            if (clipedNum != null) {
                result = text.substring(0, clipedNum - 1) + "...";
            } else {
                var strLength = text.length;
                for (var i = strLength - 2; strLength >= 0; i--) {
                    result = text.substring(0, i) + "...";
                    label.setString(result);
                    if (label.getContentSize().width <= maxWidth) {
                        break;
                    }
                }
            }

        } else {
            result = text;
        }
        var consumeTime = new Date().getTime() - preTime;
        //cc.log("cliplongText:" + consumeTime);
        return result;
    },

    getCustomFontName: function () {
        return res.GGTR00H_TTF;
    }
};
