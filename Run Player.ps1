#You can add cd "path/to/directory" here
Start-Process python -ArgumentList "server.py" 

Start-Sleep -Seconds 2

Start-Process python -ArgumentList "client.py" 