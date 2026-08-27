/**
 * Created by billbao on 2016/6/12.
 */

function Queue() {//声明这个队列类的属性和方法

    var items = [];

    this.enqueue = function(element){//入列
        items.push(element);
    };

    this.dequeue = function(){//出列，shift() 方法用于把数组的第一个元素从其中删除并返回第一个元素的值。
        return items.shift();
    };

    this.front = function(){
        return items[0];
    };

    this.isEmpty = function(){
        return items.length == 0;
    };

    this.clear = function(){
        items = [];
    };

    this.size = function(){
        return items.length;
    };

    this.print = function(){
        //console.log(items.toString());
    };
};