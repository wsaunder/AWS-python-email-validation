import sys
import logging
import pymysql
import json
import urllib.parse
import boto3
import csv
import hashlib
import os

# setting up s3
s3 = boto3.client('s3')
client = boto3.client('sqs')

# rds settings
rds_host  = os.environ.get('RDS_HOST')
user_name = os.environ.get('RDS_USER')
password = os.environ.get('RDS_PASS')
db_name = os.environ.get('RDS_DB')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.

try:
    conn = pymysql.connect(host=rds_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")


def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    s3_resource = boto3.resource('s3')
    s3_object = s3_resource.Object(bucket, key)
    data = s3_object.get()['Body'].read().decode('utf-8').splitlines()
    eTag = s3_object.get()['ETag']
    eTag = eTag.strip('\"')
    lines = csv.reader(data)
    headers = next(lines)
    item_count = 0


    with conn.cursor() as cur:
        cur.execute("create table if not exists CSVs (id int NOT NULL AUTO_INCREMENT, CSVid varchar(255) NOT NULL, PRIMARY KEY (id))")
        CSV_insert_stmt = (
                "INSERT INTO CSVs (CSVid)"
                "VALUES (%s)"
            )
        cur.execute(CSV_insert_stmt, eTag)
        print("CSVid Uploaded")
        conn.commit()
        cur.execute("create table if not exists Emails ( EmailID  int NOT NULL AUTO_INCREMENT, Email varchar(255) NOT NULL, CSVid varchar(255) NOT NULL, PRIMARY KEY (EmailID))")
        data1 = []
        data2 = []
        insert_stmt1 = (
                "INSERT INTO Emails (Email, CSVid)"
                "VALUES (%s, %s)"
                )
        insert_stmt2 = (
                "INSERT INTO Permanent (hashed_email, email)"
                "VALUES (%s, %s)"
            )
        for line in lines:
            if not line : 
                continue
            data1.append((line, eTag))
            hashed = hashlib.sha256(json.dumps(line[0]).encode('utf-8')).hexdigest()
            data2.append((hashed, line[0]))
            item_count += 1
        cur.executemany(insert_stmt1, data1)
        cur.executemany(insert_stmt2, data2)
        print("email inserted")

        
        
        conn.commit()
   
        items_sent = 0
        pagesize = 10
        offset = 0
        while items_sent <= item_count:
            messageString = str(offset) + ", " + str(pagesize) + ", " + str(eTag)
            items_sent += pagesize
            offset += pagesize
            print(messageString)os.environ.get('SQS_QUEUE')
            try:
                message1 = client.send_message(
                    QueueUrl=ENV,
                    MessageBody= messageString
                )
            except Exception as e:
                print(e)
                raise e
            

        


