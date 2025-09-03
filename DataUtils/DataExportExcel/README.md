# 数据库结构导出到Excel工具

## 项目介绍

这是一个Python工具，用于将MySQL数据库的表结构导出到Excel文件中。工具会根据表名前缀自动分组，并为每个分组生成一个独立的Excel文件，每个Excel文件包含该分组中所有表的详细结构信息。

## 功能特点

- 自动连接MySQL数据库并获取表结构信息
- 根据表名前缀自动分组导出
- 生成美观的Excel文档，包含以下内容：
  - Table List工作表：列出所有表及其基本信息
  - 每个表的详细结构信息工作表
  - 字段详细信息（包括字段名、类型、长度、主键、是否可为空等）
  - 表DDL语句
- 支持超链接跳转，方便在Excel中导航
- 自动设置样式和列宽，提高可读性

## 配置说明

在使用工具前，需要创建一个 [config.ini](file://D:\github\TsuPythonUtils\DataUtils\DataExportExcel\config.ini) 配置文件，包含数据库连接信息和输出目录设置：

```ini
[database]
host = localhost
port = 3306
user = your_username
password = your_password
database = your_database_name
charset = utf8mb4

[output]
directory = 数据库结构文档
```


配置参数说明：
- `host`: MySQL数据库服务器地址
- `port`: MySQL数据库端口
- `user`: 数据库用户名
- `password`: 数据库密码
- `database`: 要导出结构的数据库名称
- `charset`: 数据库字符集
- `directory`: 导出Excel文件的保存目录

## 运行方式

1. 安装依赖包：
   ```bash
   pip install pymysql openpyxl
   ```


2. 创建配置文件：
   在项目根目录下创建 [config.ini](file://D:\github\TsuPythonUtils\DataUtils\DataExportExcel\config.ini) 文件，并根据实际情况修改配置参数

3. 运行导出脚本：
   ```bash
   python __init__.py
   ```


## 使用示例

```python
# 直接运行脚本
python __init__.py

# 或者在其他Python脚本中调用
from DataExportExcel import export_schema_by_prefix

export_schema_by_prefix()
```


运行完成后，导出的Excel文件将保存在配置文件中指定的输出目录中，每个表前缀组会生成一个独立的Excel文件。
