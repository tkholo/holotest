from sys import argv
import random

_, testfilename, rcnt = argv
rcnt = int(rcnt)

words = []
with open("/usr/share/dict/words", "r") as wordfile:
    for line in wordfile.readlines():
        words.append(line.strip())

random.seed()
urand = open("/dev/urandom","rb")

def generate_hex_line():
    cdr_id = random.randint(0, 1048576)
    cdr_type = cdr_id % 10
    cdr_id += (6 - cdr_type)
    #print("hex type was {}".format(cdr_type))
    cdr_type = cdr_id % 10
    #print("\thex type now {}".format(cdr_type))
    #hex_data = random.randbytes(12).hex()
    hex_data = urand.read(12).hex()
    return "{},{}".format(cdr_id, hex_data)

def generate_basic_line():
    cdr_id     = random.randint(0, 1048576)
    cdr_type = cdr_id % 10

    if cdr_type == 6:
        cdr_id += 1
    elif cdr_type == 4:
        cdr_id -= 1
    bytes_used = random.randint(0, 1048576)
    return "{},{}".format(cdr_id, bytes_used)

def generate_extended_line():
    cdr_id     = random.randint(0, 1048576)
    cdr_type = cdr_id % 10
    #print("extended type was {}".format(cdr_type))
    cdr_id += (4 - cdr_type)
    cdr_type = cdr_id % 10
    #print("\textended type now {}".format(cdr_type))

    #randwords = []
    #for i in range (3):
    #    randword = random.randint(1,len(words))
    #    randword = words[randword]
    #    randwords.append(randword)
    randwords = random.sample(words, 3)
    dmcc       = ' '.join(randwords)
    mnc        = random.randint(0, 1048576)
    bytes_used = random.randint(0, 1048576)
    cell_id    = random.randint(0, 1048576)
    return "{},{},{},{},{}".format(cdr_id, dmcc, mnc, bytes_used, cell_id)

lines = [ generate_hex_line, generate_basic_line, generate_extended_line ]


with open(testfilename, 'w') as testfile:
    for i in range(rcnt):
        linetype = random.randint(0,2)
        func = lines[linetype]
        line = func()
        testfile.write("{}\n".format(line))

