#!/usr/bin/python3
from pymysql import Connect, cursors

def conn_db():
    conn = Connect(
        host="localhost",
        port=3306,
        user="bot_2500",
        password='123456',
        db="bot_2500",
        cursorclass=cursors.DictCursor
    )
    return conn