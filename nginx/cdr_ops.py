

def parse_extended(toks):
    #<id>,<dmcc>,<mnc>,<bytes_used>,<cellid>
    if len(toks) != 5:
        return { 'errmsg' : "INVALID TOKEN COUNT {} FOR EXTENDED, EXPECTED 5".format(len(toks)) }

    try:
        mnc_int = int(toks[2])
        bytecnt = int(toks[3])
        cellint = int(toks[4])
    except:
        return { 'errmsg' : "FAILED TO INT PARSE VALUES: {}".format(toks[2:5]) }

    return {
        'dmcc' : toks[1],
        'mnc'  : mnc_int,
        'bytes_used' : bytecnt,
        'cell_id' : cellint,

        'ip' : None
    }

def parse_hex_ip(hexip):
    quads = []
    for i in range(4):
        hval = hexip[ i : i+2 ]
        hint = int(hval, 16)
        quads.append(str(hint))

    ipval = '.'.join(quads)

    return ipval

def parse_hex(toks):
    if len(toks) != 2:
        return { 'errmsg' : "INVALID TOKEN COUNT {} FOR HEX, EXPECTED 2".format(len(toks)) }

    hexdata = toks[1]
    if len(hexdata) != 24:
        return { 'errmsg' : "INVALID HEX LEN {} FOR HEX STRING, EXPECTED 24".format(len(hexdata)) }

    mnc     = hexdata[0:4]
    bytecnt = hexdata[4:8]
    cell_id = hexdata[9:16]
    ip      = hexdata[16:]

    try:
        mnc_int = int(mnc, 16)
        byteint = int(bytecnt, 16)
        cellint = int(cell_id, 16)
    except:
        return { 'errmsg' : "FAILED TO INT PARSE VALUES: {} {} {}".format(mnc, bytecnt, cell_id) }

    parsed_ip = parse_hex_ip(ip)

    return {
        'bytes_used' : byteint,
        'mnc'        : mnc_int,
        'cell_id'    : cellint,
        'ip'         : parsed_ip,

        'dmcc'       : None
    }

def parse_basic(toks):
    if len(toks) != 2:
        return { 'errmsg' : "INVALID TOKEN COUNT {} FOR BASIC, EXPECTED 2".format(len(toks)) }

    try:
        bytecnt = int(toks[1])
    except:
        return { 'errmsg' : "FAILED TO INT PARSE BYTE CNT: {}".format(toks[1]) }

    return {
        'bytes_used' : bytecnt,

        'dmcc'       : None,
        'mnc'        : None,
        'cell_id'    : None,
        'ip'         : None
     }


cdr_parsers = {
    4 : parse_extended,
    6 : parse_hex,
}

def parse_line(line):
    #print("parsing line: {}".format(line))
    if "," not in line:
        return { 'errmsg' : 'NO COMMAS IN LINE, FAIL' }

    toks = line.split(',')
    cdr_id = toks[0]

    try:
        cdr_id = int(cdr_id)
    except:
        return { 'errmsg' : 'FAILED TO INT PARSE ID' }

    cdr_type = cdr_id % 10

    func = cdr_parsers.get(cdr_type, parse_basic)

    parsed_line = func(toks)
    parsed_line['cdr_id'] = cdr_id
    #print("got parsed line: {}".format(parsed_line))

    return parsed_line
