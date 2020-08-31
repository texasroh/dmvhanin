import sys
import psycopg2
import pandas as pd
from .config import Config
from .logging import logging

class Database():
	# postgresql class
    
    def __init__(self, config = Config):
        self.host = config.DB_HOST
        self.user = config.DB_USER
        self.pwd = config.DB_PWD
        self.port = config.DB_PORT
        self.dbname = config.DB_NAME
        self.conn = None
        
        
    def connect(self):
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(host=self.host,
                                             user=self.user,
                                             password=self.pwd,
                                             port=self.port,
                                             dbname=self.dbname)
                print('Connection opened successfully.')
            except psycopg2.DatabaseError as e:
                print(e)
                sys.exit()
        else:
            try:
                with self.conn.cursor() as cur:
                    cur.execute("select 1")
            except:
                self.close()
                self.connect()
                
                
    def close(self):
        if self.conn is not None:
            print("close connection")
            self.conn.close()
        self.conn = None
                
                
    def select_row(self, query, parameters: list=[], **kwargs):
        self.connect()

        records = pd.read_sql(query, self.conn, params = parameters, **kwargs)

        #self.close()
        if records.empty:
            return None
        return records.to_dict('records')[0]

            
            
    def select_rows(self, query, parameters: list=[], **kwargs):
        self.connect()

        records = pd.read_sql(query, self.conn, params = parameters, **kwargs)
        #self.close()
        return records

    
    
    def update_rows(self, query, parameters: list=[]):
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(query, parameters)
            self.conn.commit()

        #self.close()
        return f"{cur.rowcount} rows affected."