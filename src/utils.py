import os
import sys
import sqlite3
from src.exception import CustomException
from src.logger import logging

def sqli_connect(db_name):
    try:
        conn = sqlite3.connect(db_name+'.db')
        logging.info("Connected to database successfully")
        return conn
    except Exception as e:
        raise CustomException(e,sys)  