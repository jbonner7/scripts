# FortiCNAPP Webhook for FortiSIEM
This repository contains code for implementing a custom Lambda webhook to enrich alerts from Lacework FortiCNAPP using the python SDK and alerts API. 

## SPECIAL NOTE
There are two versions of the Lambda function - one for destination applications with valid SSL certificates, and a separate folder with an updated function that removes SSL verification for self-signed certificates. If possible, consider replacing the self-signed certificate with a valid SSL certificate from a recognized Certificate Authority (CA). This is the most secure and recommended approach. Bypassing SSL verification is not recommended for production code because it opens you up to man-in-the-middle attacks. Use this only for testing purposes.

## Deployment Guide
1. Log into AWS Portal and navigate to S3
2. Create a new S3 bucket
3. Upload “deployment-package-*.zip” file (depending on your setup) that contains the Lambda function code. 
4. Edit “LaceworkWebhookFilter.yaml” file and add S3 URL of the bucket that was just created, on line 35. Upload “LaceworkWebhookFilter.yaml” to S3 bucket.
5. Navigate to CloudFormation
6. Click “Create Stack (with new resources)
7. ![image](https://github.com/user-attachments/assets/9f093925-3384-4046-88bb-908d7d883585)

8. Click “Next” at the bottom
9. Provide the S3 URL where the Lambda function deployment zip file is located
10. Specify the yaml file that references the deployment.zip in the S3 URI
11. ![image](https://github.com/user-attachments/assets/7f881b00-3674-4ea4-a5bf-600647cf9c2d)

12. Click “Next”
13. Enter “Stack Name,” click next
14. Skip additional options on this page, click “Next”
15. Do not specify an IAM Role, click “Next”
16. Acknowledge and click “Create Stack”

## Set Project Environment Variables
1. Navigate to the newly created Lambda function
2. Click on “Configuration > Environment Variables”
3. Add the following environment variables specific to the customer
4. ![image](https://github.com/user-attachments/assets/a5b5f294-3626-4c4f-96e7-0fe3101f39bf)
5. The webhook URL here should be the destination webhook URL for FortiSIEM, but can be applied to other tools. 

## Create Alert Channel in Lacework
1. Log into your Lacework tenant
2. Navigate to Settings > Alert Channels
3. Click “Add new”
4. Select “Webhook” at the bottom
5. Provide a name and the function URL as Webhook URL
6. ![image](https://github.com/user-attachments/assets/881b26ed-044a-4b87-9303-2df2e9799eec)



