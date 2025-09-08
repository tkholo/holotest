from sys import argv
import requests




try:
    cmd = argv[2]
except:
    print("python {} url command <parm>".format(argv[0]))

try:
    if cmd == 'submit_file':
        _, url, cmd, filename = argv
    else:
        _, url, cmd = argv
except:
    print("python {} url command <parm>".format(argv[0]))

if cmd == 'submit_file':
    data = {
        'cmd': (None, cmd),
        'file': (filename, open(filename, 'rb'), 'text/plain')
    }
else:
    data = {
        'cmd': (None, cmd),
    }

response = requests.post(url, files=data)

print("success? {}".format(response.ok))
print("response: {}".format(response.text))
