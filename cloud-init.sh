#!/bin/bash
sudo su - opc
uname -n 100000
curl https://objectstorage.us-ashburn-1.oraclecloud.com/n/OBJECT_STORAGE_NAMESPACE/b/public-bucket/o/client.py >> /home/opc/client.py
nohup python /home/opc/client.py >& /home/opc/output.txt &
