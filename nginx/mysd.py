#!/usr/bin/python
# -*- coding: utf-8 -*-

import psycopg2
import copy
import time

MAX_CACHE_AGE = 3600


class Mys():
    def __init__(self, config):
        #print("got configs _{}_".format(config))

        self.dbhost = config.get('psql_hostname', None)
        self.dbname = config.get('psql_db',       None)
        self.dbuser = config.get('psql_username', None)
        self.dbpass = config.get('psql_password', None)
        self.dbport = config.get('psql_port',     5432)

        self.reconnect()

    def reconnect(self):
        print("attempting to connect to psql db _{}_".format(self.dbhost))
        self.mys_con = psycopg2.connect("dbname='{}' user='{}' host={} password = '{}' port='{}' connect_timeout=10 options='-c statement_timeout=30s' ".format(self.dbname,self.dbuser, self.dbhost, self.dbpass, self.dbport))
        print("connected to psql db _{}_".format(self.dbhost))
        #self.mys_con.set_session(autocommit=True)

    def close(self):
        self.mys_con.close()

    def query_cur(self, cur, func, vals):
        #print("MYS: cur calling _{}_".format(func), vals)
        cur.execute(func,vals)
        self.mys_con.commit()

    def query_cur_wrap(self, func, vals):
        retries = vals.get('retries', 2)
        for i in range(retries):
            cur = None
            try:
                cur = self.mys_con.cursor()
                self.query_cur(cur, func, vals)
                return cur
            except psycopg2.OperationalError as ex:
                print("MYS OPERATIONAL ERROR: {}".format(ex))
            except psycopg2.InterfaceError as ex:
                print("MYS INTERFACE ERROR: {}".format(ex))
            except psycopg2.Error as ex:
                print("MYS UNKNOWN ERROR _{}_".format(ex))
            except psycopg2.extensions.QueryCanceledError as ex:
                print("STATEMENT TIMEOUT ERROR {}".format(ex))
            except Exception as ex:
                print("UNHANDLED ERROR: {}".format(ex))
            del cur
            print("ATTEMPT {}/{}".format(i,retries))
            self.reconnect()
        print("MYS QCW FAILED, RETRIES EXHAUSTED")
        return None

    def store(self, func, vals):
        cur = self.query_cur_wrap(func, vals)
        if cur is None:
            print("MYS: FAILED TO CALL STORE _{}_".format(func), vals)
            ret = False
        else:
            ret = True
            #if cur.rowcount > 0:
            #    print("MYS: STORE IMPACTED {} ROWS".format(cur.rowcount))
            del cur
        return ret

    def query_all(self, func, vals):
        cur = self.query_cur_wrap(func, vals)
        if cur is None:
            print("MYS: FAILED TO CALL QA _{}_ WITH _{}_".format(func, vals))
            ret = None
        else:
            ret = copy.deepcopy(cur.fetchall())
            del cur
        return ret

    def query_singleton(self, func, vals):
        cur = self.query_cur_wrap(func, vals)
        if cur is None:
            print("MYS: FAILED TO CALL QS _{}_ WITH _{}_".format(func, vals))
            ret = None
        else:
            ret = cur.fetchone()
            if isinstance(ret, tuple) and len(ret) == 1:
                #print("replacing _{}_ with _{}_ for single-value queries".format(ret, ret[0]))
                ret = ret[0]
            try:
                cur.fetchall()
            except:
                pass
            del cur
        return ret

