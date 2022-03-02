import sqlite3

import xlsxwriter as xlsxwriter

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()


def generate_excel_deposites():
    cursor.execute("SELECT * from deposit")
    res = cursor.fetchall()
    name = 'deposites.xlsx'
    workbook = xlsxwriter.Workbook(name)
    worksheet = workbook.add_worksheet()
    header_data = ['number', 'payment id', 'user id', 'amount', 'date']
    for col_num, data in enumerate(header_data):
        worksheet.write(0, col_num, data, )
    for i, row in enumerate(res):
        for j, value in enumerate(row):
            worksheet.write(i + 1, j, value)
    workbook.close()
    return name



def generate_excel_orders():
    cursor.execute("SELECT * from deposit")
    res = cursor.fetchall()
    name = 'orders.xlsx'
    workbook = xlsxwriter.Workbook('orders.xlsx')
    worksheet = workbook.add_worksheet()
    header_data = ['number', 'user id','username','item_id','name', 'amount', 'date']
    for col_num, data in enumerate(header_data):
        worksheet.write(0, col_num, data, )
    for i, row in enumerate(res):
        for j, value in enumerate(row):
            worksheet.write(i + 1, j, value)
    workbook.close()
    return name
