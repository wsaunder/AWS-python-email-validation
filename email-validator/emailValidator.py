import json
import urllib.parse
import boto3
import csv
from email_validator import validate_email, EmailNotValidError
import pymailcheck
import pymysql
import sys
import logging
import hashlib
import os

print('Loading function')
client = boto3.client('sqs')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# rds settings
rds_host  = os.environ.get('RDS_HOST')
user_name = os.environ.get('RDS_USER')
password = os.environ.get('RDS_PASS')
db_name = os.environ.get('RDS_DB')

try:
    conn = pymysql.connect(host=rds_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()
logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

def lambda_handler(event, context):
    body = event['Records'][0]['body']
    offset = int(body.split(', ')[0])
    limit = int(body.split(', ')[1])
    etag = body.split(', ')[2]
    print("Set: " + str(offset))
    with conn.cursor() as cur:
        cur.execute("SELECT Email FROM Emails t1 INNER JOIN CSVs t2 ON t1.CSVid = t2.CSVid WHERE t1.CSVid = %s ORDER BY t1.EmailID LIMIT %s OFFSET %s;", (etag, limit, offset))
        things = cur.fetchall()
        for line in things:
            a = hashlib.sha256(json.dumps(line[0]).encode('utf-8')).hexdigest()
            b = spelling(line[0])
            c = syntax(line[0])
            update_stmt = "UPDATE Permanent SET spelling = %s, syntax = %s WHERE hashed_email = %s;"
            cur.execute(update_stmt, (b, c, a))
        conn.commit()
              
def syntax(email):
    try:
        v = validate_email(email, check_deliverability=False, allow_smtputf8=True )
        email = v["email"] 
        return("Good")
    except EmailNotValidError as e:
        return("Bad")
def spelling(email):
    if pymailcheck.suggest(email) != False:
        return("Bad")
    else:
        return("Good")


