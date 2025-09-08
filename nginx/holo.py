import json
import sys
from os import environ
from copy import deepcopy
from time import sleep, time
from functools import lru_cache
from traceback import format_exc, format_exception
from datetime import datetime
from cdr_ops import parse_line


logfile = open("/tmp/app.log","a")
def logprint(msg):
    logfile.write(msg)
    logfile.write("\n")
    logfile.flush()

if __name__ == "__main__":        
    class Mys():
        def __init__(self, a):
            self.mys_con = self
            pass
        def store(self, func, vals):
            print("NOT CALLING STORE() WITH {} AND {}".format(func, vals))
        def close(self):
            pass
        def commit(self):
            pass

    def exec_vals(cur, func, vals):
        print("NOT CALLING EXECUTE_VALUES ON {} RECORDS".format(len(vals)))

    mys = Mys(environ)
    mys_cur = None
else:
    from mysd import Mys
    import psycopg2.extras as extras
    exec_vals = extras.execute_values

    mys = Mys(environ)
    mys_cur = mys.mys_con.cursor()

mys_get_cdr_data_by_file_id = "SELECT * FROM cdr_data WHERE file_id = %(file_id)s"
mys_get_cdr_data_all = "SELECT file_id, cdr_id, mnc, bytes_used, cell_id, ip, dmcc FROM cdr_data"
mys_get_errors_all = "SELECT file_id, raw_text, err_msg FROM errors"
mys_store_error    = "INSERT INTO errors ( file_id, raw_text, err_msg ) VALUES ( %(file_id)s, %(raw_text)s, %(err_msg)s ) "
mys_store_cdr_file = "INSERT INTO cdr_file ( file_id, file_name, tstamp) VALUES ( %(file_id)s, %(file_name)s, NOW() ) "
mys_store_cdr_data = "INSERT INTO cdr_data ( file_id, cdr_id, mnc, bytes_used, cell_id, ip, dmcc ) VALUES ( %(file_id)s, %(cdrid)s, %(mnc)s, %(bytes)s, %(cellid)s, %(ip)s, %(dmcc)s ) "


mys_store_cdr_data_bulk = "INSERT INTO cdr_data ( file_id, cdr_id, mnc, bytes_used, cell_id, ip, dmcc ) VALUES %s"

#        "uid BIGSERIAL PRIMARY KEY, " \
#        "file_id BIGINT NOT NULL, " \
#        "cdr_id BIGINT NOT NULL, " \
#        "mnc INT , " \
#        "bytes_used INT NOT NULL, " \
#        "cell_id INT , " \
#        "ip VARCHAR(20) , " \
#        "dmcc VARCHAR(32) " \

def submit_file(form_data):
    file_obj = form_data['file']
    #print("GOT FILE DATA: {}: {}".format(file_obj, type(file_obj)))

    ds = datetime.now()
    str_datetime = int(ds.strftime("%m%d%H%M%S"))
    vals = {
        'file_id' : str_datetime,
        'file_name' : file_obj['file_name']
    }

    mys.store(mys_store_cdr_file, vals)

    cnt = 0
    value_cache = []
    time_st = time()
    errors = 0
    lines = file_obj['file_data'].decode('utf-8').split('\n')
    #for line in file_data.file.readlines():
    for line in lines:
        if len(line.strip()) <= 0:
            #empty line
            pass

        cnt += 1
        cdr_data = parse_line(line.strip())
        if 'errmsg' in cdr_data:
            print("ERROR PARSING CDR DATA LINE {} : {}".format(line, cdr_data['errmsg']))
            vals = {
                'file_id'  : str_datetime,
                'raw_text' : line.strip(),
                'err_msg'  : cdr_data['errmsg']
            }
            mys.store(mys_store_error, vals)
            errors += 1
        else:
            cdr_data['file_id'] = str_datetime
            ordered_val_tuple = order_vals(cdr_data)
            value_cache.append(ordered_val_tuple)
            #mys.store(mys_store_cdr_data, cdr_data)

            if len(value_cache) > 100:
                commit_cache(value_cache)
                value_cache = []

    if len(value_cache) > 0:
        print("cleanup commit: {}".format(len(value_cache)))
        #print("cleanup commit: {}".format(value_cache))
        commit_cache(value_cache)
        value_cache = []
    time_dur = time() - time_st
    print("{} LINES COMMITTED IN {}s, {} lines/sec".format(cnt, time_dur, cnt/time_dur))
    report = {
        'file_name' : file_obj['file_name'],
        'file_id'   : str_datetime,
        'cnt_line'  : cnt,
        'cnt_err'   : errors
    }

    mys.mys_con.commit()
    return json.dumps(report)

def get_all_data(form_data):
    rets = []
    #no parms needed?
    datarows = mys.query_all(mys_get_cdr_data_all, {})
    for drow in datarows:
        drowdict = {
            'file_id' : drow[0],
            'cdr_id'  : drow[1],
            'mnc'     : drow[2],
            'bytes_used' : drow[3],
            'cell_id' : drow[4],
            'ip'      : drow[5],
            'dmcc'    : drow[6]
        }
        rets.append(drowdict)
    return json.dumps(rets)

def get_data_by_file_id(form_data):
    file_id = form_data['file_id']
    pass

def get_errors(file_data):
    rets = []
    error_rows = mys.query_all(mys_get_errors_all, {})
    for row in error_rows:
        rets.append({
            'file_id' : row[0],
            'raw_text' : row[1],
            'err_msg' : row[2]
        })
    return json.dumps(rets)

def sz_query(form_data):
    si = form_data
    ##OK, PARMS REQUIRED FOR id_pkg and cmp_pkg
    parms = {}
    if 'parms' in si:
        parms = si.pop('parms')
        #if 'id_pkg' in parms:
        #    parms.pop('id_pkg')
        #id_pkg  = parms.get('id_pkg',default_id_pkg)
    #print("GOT PARMS: {}".format(parms))
    rets = sz_proc(si, parms.get('enabled_name_search_options',{}))

    #print("prejs")
    jsonret = json.dumps(erets)
    #jsonret = json.dumps(llr_results)
    #print("preuni")
    utfret  = jsonret.encode('utf8')
    #print("preret")

    return utfret

from cgi import FieldStorage
def parse_wsgi(environ):
    try:
        clen = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        print("INFO: no content length, can't parse wsgi data")
        return None

    ret = {}

    #try:
    #request_body = environ['wsgi.input'].read(clen)

      # Parse multipart/form-data
    request_body = FieldStorage(
        fp=environ['wsgi.input'],
        environ=environ,
        keep_blank_values=True
    )
    #print("REQ BODY: {}: {}".format(type(request_body), request_body))

    ret['cmd'] = request_body.getvalue('cmd')
    #print("PWSGI ret: {}".format(ret))

    
    if 'file' in request_body:
        #print("GOT A FILE: {}".format(request_body['file']))
        #filedata = request_body['file'].pop()
        filedata = request_body['file']
        #print("FILE DATA: {}".format(filedata))
        print("FILE NAME: {}".format(filedata.filename))
        filedict = {
            'file_name' : filedata.filename,
            'file_data' : filedata.file.read()
        }
        #print("FILE DICT: {}".format(filedict))
        ret['file'] = filedict

    #bdata = json.loads(ret)
    #logprint("got form_data: {}".format(bdata))
    return ret
    #except Exception as ex:
    #    print("__ERROR__: bad data format: {}",ex)
    #    return None
    

commands = {
    'submit_file' : submit_file,
    'get_all_data' : get_all_data,
    'get_data_by_file_id' : get_data_by_file_id,
    'get_errors' : get_errors
}

def application(environ, start_response):
    #logprint("app")
    #logprint("environ: {}".format(environ))
    #logger.info("environ: {}".format(environ))
    print("Access-Control-Allow-Origin: *")  # Allow all origins (or specify e.g., "http://localhost:3000")
    print("Access-Control-Allow-Methods: POST, OPTIONS")  # Allow POST and OPTIONS
    print("Access-Control-Allow-Headers: Content-Type")  # Allow Content-Type header
    print("Content-Type: application/json")
    print()

    inp = environ.get('wsgi.input',{})
    #logprint("inp: {}".format(inp))
    #logger.info("inp: {}".format(inp))

    form_data = parse_wsgi(environ)
    print("APP FORM DATA: {}".format(form_data))
    if form_data is None:
        err_line = "NO FORM DATA"
        print(err_line)
        resp = bytes("NO QUERY",'utf8')
        start_response('500 Internal Error', [('Content-Type', 'text/html')])
        return [resp]

    if 'cmd' not in form_data:
        err_line = "NO CMD IN {}".format(json.dumps(form_data))
        print(err_line)
        resp = bytes(err_line,'utf8')
        start_response('500 Internal Error', [('Content-Type', 'text/html')])
        return [resp]

    cmd = form_data['cmd']

    if cmd not in commands:
        err_line = "CMD {} NOT IN VALID COMMANDS {}".format(cmd, commands.keys())
        print(err_line)
        resp = bytes(err_line,'utf8')
        start_response('500 Internal Error', [('Content-Type', 'text/html')])
        return [resp]

    try:
        func = commands[cmd]
        resp = func(form_data)
    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        exc = format_exception(exc_type, exc_value,exc_traceback)
        errline = "EXCEPTION WHEN PROCESSING COMMAND {}: {}: {}".format(cmd, ex, exc)
        print(errline)
        resp = bytes(err_line,'utf8')
        start_response('500 Internal Error', [('Content-Type', 'text/html')])
        return [resp]

    resp = bytes(resp, 'utf-8')
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [resp]

logprint("on")

#mys_store_cdr_data = "INSERT INTO cdr_data ( file_id, cdr_id, mnc, bytes_used, cell_id, ip, dmcc ) VALUES ( %(fid)s, %(cdrid)s, %(mnc)s, %(bytes)s, %(cellid)s, %(ip)s, %(dmcc)s ) "
cdr_val_order = [ 'file_id', 'cdr_id', 'mnc', 'bytes_used', 'cell_id', 'ip', 'dmcc' ]
#s(['dmcc', 'mnc', 'bytes_used', 'cell_id', 'ip', 'cdr_id', 'file_id'])

def order_vals(vals):
    ret = ()
    for vo in cdr_val_order:
        ret = ret + (vals[vo],)

    return ret

def commit_cache(value_cache):
    print("exec_vals is {}".format(exec_vals))
    exec_vals(mys_cur, mys_store_cdr_data_bulk, value_cache)
    mys.mys_con.commit()

if __name__ == "__main__":        
    _, testfile = sys.argv

    value_cache = []

    ds = datetime.now()
    str_datetime = ds.strftime("%m%d%H%M%S")

    time_st = time()
    cnt = 0
    with open(testfile, 'r') as cdrfile:
        vals = {
            'file_id'   : str_datetime,
            'file_name' : testfile
        }
        mys.store(mys_store_cdr_file, vals)
        for line in cdrfile.readlines():
            if len(line.strip()) <= 0:
                #empty line
                pass

            cnt += 1
            cdr_data = parse_line(line.strip())
            if 'errmsg' in cdr_data:
                print("ERROR PARSING CDR DATA LINE {} : {}".format(line, cdr_data['errmsg']))
                vals = {
                    'file_id'  : str_datetime,
                    'raw_text' : line.strip(),
                    'err_msg'  : cdr_data['errmsg']
                }
                try:
                    mys.store(mys_store_error, vals)
                except Exception as ex:
                    print("ERROR STORING ERROR MSG: {}".format(ex))
                    vals['raw_text'] = "POSSIBLE ERROR HANDLING RAW TEXT"
                    mys.store(mys_store_error, vals)
            else:
                cdr_data['file_id'] = str_datetime
                ordered_val_tuple = order_vals(cdr_data)
                value_cache.append(ordered_val_tuple)
                #mys.store(mys_store_cdr_data, cdr_data)

                if len(value_cache) > 100:
                    commit_cache(value_cache)
                    value_cache = []

        if len(value_cache) > 0:
            commit_cache(value_cache)
            value_cache = []
        time_dur = time() - time_st
        print("{} LINES NOT COMMITTED IN {}s, {} lines/sec".format(cnt, time_dur, cnt/time_dur))

