# AWS-python-email-validation

This is a pair of lambdas that when uploaded will allow a csv of email addresses uploaded to s3 to be processed into a rds database and then checked for spelling or syntax errors.

There are a number of things needed to set this up. 

Create AWS account.
Create S3 Bucket.
Create SQS queues for passing data between the 2 functions.
Set up VPC for the database.
Create RDS in VPC.
Create IAM roles for everything.
Zip each individual function in this git.
Create both Lambda functions in AWS.
Upload zipped functions.
Configure triggers and other permissions.

