import pymysql
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import os
from collections import defaultdict
from datetime import datetime
import configparser

# ------------------------- 配置区域 (请根据实际情况修改) -------------------------

# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

DB_CONFIG = {
    'host': config.get('database', 'host'),
    'port': config.getint('database', 'port'),
    'user': config.get('database', 'user'),
    'password': config.get('database', 'password'),
    'database': config.get('database', 'database'),
    'charset': config.get('database', 'charset')
}

OUTPUT_DIR = config.get('output', 'directory')

# 样式定义
BLUE_FILL = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")
DARK_BLUE_FILL = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=10)
INFO_FONT = Font(size=10)
BOLD_INFO_FONT = Font(bold=True, size=10)
HYPERLINK_FONT = Font(color="0563C1", underline="single")
THIN_BORDER = Border(left=Side(style='thin'), right=Side(style='thin'),
                     top=Side(style='thin'), bottom=Side(style='thin'))


# -----------------------------------------------------------------------------

def get_db_connection():
    """建立数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def export_schema_by_prefix():
    """主函数：根据表名前缀分组导出到多个Excel文件"""

    print("开始连接数据库并导出结构...")
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR)

            cursor.execute("""
                           SELECT TABLE_NAME, TABLE_COMMENT
                           FROM INFORMATION_SCHEMA.TABLES
                           WHERE TABLE_SCHEMA = DATABASE()
                           ORDER BY TABLE_NAME;
                           """)
            tables = cursor.fetchall()

            prefix_groups = defaultdict(list)
            for table in tables:
                table_name, table_comment = table
                prefix = table_name.split('_')[0] if '_' in table_name else '其他'
                prefix_groups[prefix].append((table_name, table_comment))

            for prefix, tables_in_group in prefix_groups.items():
                output_filename = os.path.join(OUTPUT_DIR, f"{prefix}_表结构.xlsx")
                create_excel_for_prefix(prefix, tables_in_group, cursor, output_filename, conn)

            print(f"导出成功！文件保存在目录: {OUTPUT_DIR}")

    finally:
        conn.close()


def create_excel_for_prefix(prefix, tables, cursor, output_filename, conn):
    """为特定前缀创建Excel文件"""
    wb = Workbook()
    if 'Sheet' in wb.sheetnames:
        wb.remove(wb['Sheet'])

    # 创建Table List工作表
    ws_table_list = wb.create_sheet("Table List", 0)
    setup_table_list_sheet(ws_table_list, tables)

    for table_name, table_comment in tables:
        sheet_name = table_comment or table_name
        sheet_name = sheet_name[:31]  # Excel工作表名称最大31个字符
        ws_table = wb.create_sheet(sheet_name)
        setup_table_sheet_exact(ws_table, table_name, table_comment, cursor, conn)

    wb.save(output_filename)


def setup_table_list_sheet(ws, tables):
    """设置Table List工作表"""
    ws.title = "Table List"

    # 空出第一行和第一列
    start_row = 2
    start_col = 2

    # 设置表头（深蓝色）
    headers = ['No', 'Physical Table Name', 'Logical Table Name', 'Created Date', 'Modified Date', 'Modified Version']

    # 写入表头
    for col_num, header in enumerate(headers, start_col):
        cell = ws.cell(row=start_row, column=col_num)
        cell.value = header
        cell.fill = DARK_BLUE_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    # 填充数据
    current_date = datetime.now().strftime("%Y/%m/%d")
    for i, (table_name, table_comment) in enumerate(tables, 1):
        row_data = [i, table_name, table_comment or '', current_date, '', '1.0']

        # 写入数据行
        for col_num, value in enumerate(row_data, start_col):
            cell = ws.cell(row=start_row + i, column=col_num)
            cell.value = value
            cell.border = THIN_BORDER

            # 设置对齐方式
            if col_num == start_col:  # No列
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_num == start_col + 1 or col_num == start_col + 2:  # Physical Name和Logical Name列
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:  # 其他列
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # 为表名添加超链接
            if col_num == start_col + 1:  # Physical Table Name列
                sheet_name = table_comment or table_name
                sheet_name = sheet_name[:31]  # Excel工作表名称最大31个字符
                cell.hyperlink = f"#'{sheet_name}'!A1"
                cell.font = HYPERLINK_FONT

    # 设置列宽
    column_widths = [8, 40, 30, 15, 15, 15]
    for i, width in enumerate(column_widths, start_col):
        ws.column_dimensions[get_column_letter(i)].width = width


def setup_table_sheet_exact(ws, table_name, table_comment, cursor, conn):
    """按照图片样式设置工作表"""
    ws.sheet_view.showGridLines = False

    # 1. 返回目录放在A1位置
    ws.cell(row=1, column=1, value="← 返回目录").font = HYPERLINK_FONT
    ws.cell(row=1, column=1).hyperlink = f"#'Table List'!A1"

    # 2. 顶部信息区域 - 新布局
    start_row = 3  # 从第3行开始
    start_col = 2  # 从B列开始

    # 设置列宽
    ws.column_dimensions[get_column_letter(start_col)].width = 15  # 标签列
    ws.column_dimensions[get_column_letter(start_col + 1)].width = 30  # 内容列1
    ws.column_dimensions[get_column_letter(start_col + 2)].width = 25  # 内容列2

    # 表信息区域（6行x3列布局）
    info_rows = [
        ['数据库', DB_CONFIG['database'], ''],
        ['表名', table_name, ''],  # 新增的表名行
        ['备注', table_comment or '', ''],
        ['创建人', '', ''],
        ['创建日期', datetime.now().strftime("%Y/%m/%d"), ''],
        ['修改人', '', ''],
        ['修改日期', '', ''],
        ['版本', '1.0', '']
    ]

    # 填充所有单元格
    for row_idx, row_data in enumerate(info_rows, start=start_row):
        for col_idx, value in enumerate(row_data, start=start_col):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = THIN_BORDER
            cell.alignment = Alignment(vertical="center")

            # 设置标签列样式（蓝色背景，粗体）
            if col_idx == start_col:
                cell.fill = BLUE_FILL
                cell.font = BOLD_INFO_FONT
            else:
                cell.font = INFO_FONT

    # 合并第二列和第三列的内容单元格
    for row_idx in range(start_row, start_row + len(info_rows)):
        ws.merge_cells(start_row=row_idx, start_column=start_col + 1,
                       end_row=row_idx, end_column=start_col + 2)

    # 空一行
    info_end_row = start_row + len(info_rows) + 1

    # 3. 字段列表表头 - 添加Default列
    headers = ['No.', 'Physical Name', 'Logical Name', 'Data Type', 'Size', 'Key', 'NULL', 'Default', 'Description',
               'Remarks']

    for col_num, header in enumerate(headers, start_col):
        cell = ws.cell(row=info_end_row + 1, column=col_num)
        cell.value = header
        cell.fill = DARK_BLUE_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    # 4. 获取字段数据并填充
    cursor.execute(f"""
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION;
    """)
    columns = cursor.fetchall()

    for i, col in enumerate(columns, 1):
        col_name, col_type, is_nullable, col_key, col_default, extra, col_comment = col

        # 解析数据类型和长度
        data_type = col_type
        size = ''
        if '(' in col_type and ')' in col_type:
            data_type = col_type.split('(')[0]
            size = col_type.split('(')[1].split(')')[0]

        is_key = 'PK' if 'PRI' in col_key else ('FK' if 'MUL' in col_key else '')
        is_null = 'N' if is_nullable == 'NO' else 'Y'
        default_value = str(col_default) if col_default is not None else ''

        row_data = [
            i,  # No.
            col_name,  # Physical Name
            col_comment or '',  # Logical Name
            data_type,  # Data Type
            size,  # Size
            is_key,  # Key
            is_null,  # NULL
            default_value,  # Default
            '',  # Description (留空)
            ''  # Remarks (留空)
        ]

        for col_num, value in enumerate(row_data, start_col):
            cell = ws.cell(row=info_end_row + 1 + i, column=col_num)
            cell.value = value
            cell.border = THIN_BORDER

            # 设置对齐方式
            if col_num == start_col:  # No.列
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_num == start_col + 1 or col_num == start_col + 2:  # Physical Name和Logical Name列
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:  # 其他列
                cell.alignment = Alignment(horizontal="center", vertical="center")

    # 5. 设置字段列表列宽
    column_widths = [8, 30, 40, 12, 8, 8, 8, 10, 15, 20]
    for i, width in enumerate(column_widths, start_col):
        ws.column_dimensions[get_column_letter(i)].width = width

    # 6. 在字段列表下方放置DDL区域
    ddl_start_row = info_end_row + len(columns) + 4

    # DDL标题
    ws.cell(row=ddl_start_row, column=start_col, value="DDL").font = BOLD_INFO_FONT
    ws.merge_cells(start_row=ddl_start_row, start_column=start_col,
                   end_row=ddl_start_row, end_column=start_col + len(headers) - 1)

    # 获取表DDL
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    ddl_result = cursor.fetchone()
    ddl = ddl_result[1] if ddl_result else f"无法获取 {table_name} 的DDL"

    # 分割DDL为多行并写入
    ddl_lines = ddl.split('\n')
    for i, line in enumerate(ddl_lines, start=1):
        ws.cell(row=ddl_start_row + i, column=start_col, value=line)
        ws.merge_cells(start_row=ddl_start_row + i, start_column=start_col,
                       end_row=ddl_start_row + i, end_column=start_col + len(headers) - 1)


if __name__ == '__main__':
    export_schema_by_prefix()