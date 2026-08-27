## configObject-generator，配置对象生成工具 ##

**主要内容**

- 读取并解析excel文件
- 以表名 + Object 为文件名生成 js 文件，提供 get set 类型接口
- excel文件默认表名为 Sheet1, Sheet2, Sheet3,需要根据实际内容修改表名，如Ship
- 表第一行为字段名，第二行为类型，第三行为程序用的字段名，第四行为描述

双击 generator.bat 会在当前目录下生成 js 代码文件

PS:现工具还未完全完善，暂时只做生成代码功能示例