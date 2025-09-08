curl -X POST \
  -F "cmd=submit_file" \
  -F "file=@$1" \
  http://localhost/holo
