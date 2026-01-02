import datetime as dt
import os
import sys
import time
from pathlib import Path

import pandas as pd
from gremlin_python.driver import client, serializer
import logging
logging.basicConfig(level=logging.DEBUG)

def record2dict(schema, record):
    d = dict()
    for idx, field in enumerate(schema['fields']):
        parsed = field.split(' ')[-1].split('.')[-1]
        d[parsed] = record[idx]

    return d

def buildSelect(schema):
    schema['select'] = 'select '
    for field in schema['fields']:
        schema['select'] += field + ','
    schema['select'] = schema['select'][:-1]
    schema['select'] += ' from '
    for table in schema['table']:
        schema['select'] += table + ','
    schema['select'] = schema['select'][:-1]
    schema['select'] += ' '

class SqlDatabase():
    
    def __init__(self, config):
        self.configuration = config
        self.dbCursor = None
        self.dbConnection = None
        self.dbType = None
        self.server = None
        self.database = None
        self.uid = None
        self.password = None
        
        self.dbType = self.configuration['Interface'].upper()
        if self.dbType not in ['MYSQL', 'SQLSERVER', 'SQLITE']:
            raise Exception('CloudDatabase: Type not recognized.')

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def connect(self):
        self.dbCursor = None
        if self.dbType == 'MYSQL':
            try:
                import mysql.connector as MySQLdb
                self.dbConnection = MySQLdb.connect(host = self.configuration['Host'], 
                                                    user = self.configuration['User'], 
                                                    password = self.configuration['Password'], 
                                                    database = self.configuration['Database'],
                                                    use_pure=True
                                                    )
            except Exception as excp:
                raise Exception('CloudDatabase.connect', 'MySql Error: {0}'.format(excp))
            
        elif self.dbType == 'SQLITE':
            try:
                import sqlite3
                self.dbConnection = sqlite3.connect(self.configuration['Source'])
            except Exception as excp:
                raise Exception('CloudDatabase.connect', 'SQLITE Error: {0}'.format(excp))

        elif self.dbType == 'SQLSERVER':
            connectString = ('Driver={ODBC Driver 18 for SQL Server};'
                              'Server=' + self.configuration['Server'] + ';'
                              'Database=' + self.configuration['Database'] + ';'
                              'Uid=' + self.configuration['User'] + ';'
                              'Pwd=' + self.configuration['Password'] + ';'
                              'TrustServerCertificate=yes;'
                              )
            try:
                import pyodbc
                self.dbConnection = pyodbc.connect(connectString)
                return self
            except Exception as excp:
                raise Exception('CloudDatabase.connect', 'pyodbc Error: {0}'.format(excp))
    
    def close(self):
        self.closeCursor()
        self.dbConnection.close()

    def closeCursor(self):
        if self.dbCursor != None:
            try:
                self.dbCursor.close()
            except:
                pass
            
            self.dbCursor = None

    def sendSqlNoReturn(self, sql, params = None):
        cursor = self.dbConnection.cursor()
        if params == None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, params)
        
        rowsAffected = cursor.rowcount
        cursor.close()
        self.dbConnection.commit()
        return rowsAffected
    
    def insertRows(self, sqlInsert, sqlValues, cursor):
        ret = [None] * len(sqlValues)
        sql = sqlInsert
        for sqlValue in sqlValues:
            sql += sqlValue + ','
        sql = sql[0:-1]     
        
        # First try all the rows together
        allRowsOK = True
        try:
            cursor.execute(sql)
        except:
            allRowsOK = False
            
        if allRowsOK == False:    
            # There was a problem so try one row at a time
            for idx, sqlValue in enumerate(sqlValues):
                sql = sqlInsert + sqlValue
                try:
                    cursor.execute(sql)
                except Exception as excp:
                    ret[idx] = excp
        return ret

    def multiRowInsert(self, sqlInsert, sqlValuesList, batchSize, sourceName, logObject):
        totalRows = len(sqlValuesList)
        cursor = self.dbConnection.cursor()

        rowsInserted = 0
        for startIdx in range(0, totalRows, batchSize):
            endIdx = startIdx + batchSize
            if endIdx > totalRows:
                endIdx = totalRows
                
            sqlValuesSubList = sqlValuesList[startIdx:endIdx]
            retValues = self.insertRows(sqlInsert, sqlValuesSubList, cursor)
            for idx, retValue in enumerate(retValues):
                if retValue == None:
                    rowsInserted += 1
                else:
                    s = retValue.args[1]
                    if s.find('duplicate key') > -1:
                        logObject.addStatus(sourceName, 'Failed adding record with duplicate key  {0}'.format(sqlValuesSubList[idx]))
                    else:
                        logObject.addStatus(sourceName, 'Failed adding record {0}'.format(sqlValuesSubList[idx]))
                        logObject.addStatus(sourceName, '   Error: {0}'.format(s))
                    logObject.addStatus(sourceName, '', fileLog = False)

            logObject.addStatus(sourceName, 'Added {0} of {1} Records'.format(rowsInserted, totalRows), useTop = True, fileLog = False)
        
        cursor.close()
        self.dbConnection.commit()
        return rowsInserted

    
    def sendSql(self, sql, params = None):
        try:
            cursor = self.dbConnection.cursor()
            if params == None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            records = cursor.fetchall()  
            cursor.close()
            self.dbConnection.commit()
        except:
            print("CloudDatabase: Unexpected error:", sys.exc_info()[0])
            raise  
        
        return records


    def sendSql2(self, schema, params=None):
        try:
            # Extract SQL query from the schema dictionary
            sql = schema["select"]  
            # Ensure that sql is a string
            if not isinstance(sql, str):
                raise TypeError(f"Error: SQL query must be a string. Found {type(sql)}")
            cursor = self.dbConnection.cursor()
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            records = cursor.fetchall()
            cursor.close()
            self.dbConnection.commit()
        except Exception as e:
            print("CloudDatabase: Unexpected error:", e)
            raise
        return records

    def sendStoredProcedure(self, proc, args):
        try:
            cursor = self.dbConnection.cursor()
            cursor.callproc(proc, args)
            records = []
            results = cursor.stored_results()
            for result in results:
                record = result.fetchall()
                records.extend(record) 

            cursor.close()
            self.dbConnection.commit()
        except:
            print("CloudDatabase: Unexpected error:", sys.exc_info()[0])
            raise  
        
        return records

    def sendSqlCursor(self, sql):
        self.closeCursor()
        try:
            self.dbCursor = self.dbConnection.cursor()
            self.dbCursor.execute(sql)
        except:
            print("CloudDatabase: Unexpected error:", sys.exc_info()[0])
            raise  

    def fetch(self, n):
        if self.dbCursor == None:
            return []
        try:
            return self.dbCursor.fetchmany(n)  
        except:
            print("CloudDatabase: Unexpected error:", sys.exc_info()[0])
            raise  

    def select(self, schema, where):
        sql = schema['select'] + where
        record_list = self.sendSql(sql)
        records = []
        for record in record_list:
            record = record2dict(schema, record)
            records.append(record)
        return records
    
   
    def select_patients_by_location_step(self, schema, where="", order_by=None, offset=None, fetch=None):
        # Define the subquery to get the most recent EntryDatetime for each patient where Location is CTOR
        subquery = """
            (SELECT MRN, MAX(EntryDatetime) AS MaxEntryDatetime
            FROM location_steps
            WHERE Location = 'CTOR'
            GROUP BY MRN) AS ls
        """

        # Define the join with the subquery
        join_clause = f"""
            LEFT JOIN {subquery} ON patients.MRN = ls.MRN
            LEFT JOIN admissions ON patients.MRN = admissions.MRN
        """

        # Build the SQL query
        select_clause = ", ".join([f"{field}" for field in schema['fields']])
        # Always include admissions.ReviewDate in the select for ordering
        if 'admissions.ReviewDate' not in select_clause:
            select_clause += ", admissions.ReviewDate"
        sql = f"SELECT {select_clause}, ls.MaxEntryDatetime FROM patients {join_clause} {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        else:
            # Default order by admissions.ReviewDate DESC
            sql += " ORDER BY admissions.ReviewDate DESC"
        if offset is not None and fetch is not None:
            sql += f" OFFSET {offset} ROWS FETCH NEXT {fetch} ROWS ONLY"

        try:
            record_list = self.sendSql(sql)
        except Exception as e:
            logging.error(f'Error executing SQL: {e}')
            raise
        records = []

        for record in record_list:
            record = record2dict(schema, record)
            records.append(record)

        return records

    def select_patients_by_location_step_original(self, schema, where="", order_by=None, offset=None, fetch=None):
        # Define the subquery to get the most recent EntryDatetime for each patient where Location is CTOR
        subquery = """
            (SELECT MRN, MAX(EntryDatetime) AS MaxEntryDatetime
            FROM location_steps
            WHERE Location = 'CTOR'
            GROUP BY MRN) AS ls
        """
        
        # Define the join with the subquery
        join_clause = f"""
            LEFT JOIN {subquery} ON patients.MRN = ls.MRN
        """
        
        # Build the SQL query
        select_clause = ", ".join([f"patients.{field}" for field in schema['fields']])
        sql = f"SELECT DISTINCT {select_clause}, ls.MaxEntryDatetime FROM patients {join_clause} {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        else:
            # Default order by the most recent EntryDatetime, with patients without CTOR entries last
            sql += " ORDER BY CASE WHEN ls.MaxEntryDatetime IS NULL THEN 1 ELSE 0 END, ls.MaxEntryDatetime DESC"
        if offset is not None and fetch is not None:
            sql += f" OFFSET {offset} ROWS FETCH NEXT {fetch} ROWS ONLY"
        
        try:
            record_list = self.sendSql(sql)
        except Exception as e:
            logging.error(f'Error executing SQL: {e}')
            raise
        records = []


        for record in record_list:
            record = record2dict(schema, record)
            records.append(record)
        return records

    def select_patients(self,    schema, where, order_by=None, offset=None, fetch=None):        
        sql = schema['select'] + " " + where
        if order_by:
            sql += f" ORDER BY {order_by}"
        if offset is not None and fetch is not None:
            sql += f" OFFSET {offset} ROWS FETCH NEXT {fetch} ROWS ONLY"
        try:
            record_list = self.sendSql(sql)
        except Exception as e:
            logging.error(f'Error executing SQL: {e}')
            raise

        records = []
        for record in record_list:
            record = record2dict(schema, record)
            records.append(record)
        return records
    
    def search_patient_mrn(self, schema, mrn):
        """
        Queries the database for patients with the specified MRN.

        Args:
            schema (dict): The schema dictionary containing SQL templates.
            mrn (str): The Medical Record Number to search for.

        Returns:
            list: A list of patient records matching the MRN.
        """
        # Construct the WHERE clause to search for the specified MRN
        where = f"WHERE mrn = '{mrn}'"
        return self.select_patients(schema, where)
    
 




class GraphDatabase():
    
    def __init__(self, config):
        self.configuration = config
        self.user = self.configuration['user']
        self.ip = self.configuration['IP']
        self.pwd = self.configuration['pwd']
        self.client = None
        #log('User: {} IP: {} PWD: {}'.format(self.user, self.ip, self.pwd))

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def connect(self):
        if not self.client:
            self.client = client.Client(self.ip, 
                                        'g',
                                        username=self.user,
                                        password=self.pwd,
                                        message_serializer=serializer.GraphSONSerializersV2d0()
                                        )
    
    def close(self):
        #print('In cleanup: {}'.format(self.client))
        if self.client:
            #print('Closing connection')
            self.client.close()
            self.client._executor.shutdown()
            #print('Closed connection')
        self.client = None
            
            
    def cleanupGraph(self):
        try:
            ids = self.sendQuery('g.V().values("id")')
            print('Droping {} verticies'.format(len(ids)))
            for idx, id in enumerate(ids):
                #if idx > 0 and (idx % 5) == 0:
                #    time.sleep(.1)
                time.sleep(.1)
                gremlin = 'g.V().has("id", \"{0}\").drop()'.format(id)
                self.sendAction(gremlin)
        except Exception as excp:
            raise Exception('GremlinDatabase.cleanupGraph failed {0}'.format(excp))
        try:
            ids = self.sendQuery('g.E().values("id")')
            print('Droping {} edges'.format(len(ids)))
            for id in ids:
                gremlin = 'g.E().has("id", \"{0}\").drop()'.format(id)
                self.sendAction(gremlin)
        except Exception as excp:
            raise Exception('GremlinDatabase.cleanupGraph failed {0}'.format(excp))


    def sendQuery(self, gremlin):
        resultsIter = self.client.submitAsync(gremlin).result()
        results = []
        for result in resultsIter:
            results.extend(result)

        return results

    def reformatResults(self, resultsIn, columns):
        results = []
        for idx in range(0, len(resultsIn), columns):
            result = []
            for col in range(columns):
                result.append(resultsIn[idx+col])
                
            results.append(result)
        
        return results

    def sendAction(self, gremlin):
        results = self.client.submitAsync(gremlin)
        ret = results.result().one()
        
        if len(ret) > 0:
            raise Exception('GremlinDatabase.sendAction failed gremlin: {}, {})'.format(gremlin, str(ret)))

    def sendWrite(self, gremlin):
        results = self.client.submitAsync(gremlin)
        ret = results.result().one()
        
        if len(ret) == 0:
            raise Exception('GremlinDatabase.sendWrite failed gremlin: {}, {})'.format(gremlin, str(ret)))

    def send(self, gremlin):
        results = self.client.submitAsync(gremlin)
        ret = results.result().one()
