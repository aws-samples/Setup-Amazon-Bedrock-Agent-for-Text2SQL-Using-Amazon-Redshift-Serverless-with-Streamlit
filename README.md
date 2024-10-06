# Setup Amazon Bedrock Agent for Text2SQL Using Amazon Redshift Serverless with Streamlit

## Introduction
This project sets up an Amazon Bedrock agent with an action group that translates natural language to SQL queries. It uses Amazon Redshift Serverless for data storage and querying, with a Streamlit frontend for user interaction.

## Prerequisites
- An active AWS Account
- Familiarity with AWS services like Amazon Bedrock, Amazon S3, AWS Lambda, Amazon Redshift Serverless, and Amazon EC2
- Access granted to the **Anthropic: Claude 3 Sonnet** model from the Amazon Bedrock console

## High-Level Setup Steps

1. Create an SSH key pair
2. Create a Redshift Serverless workgroup
3. Load sample data into Redshift Serverless
4. Prepare the Lambda function code (if modifications are needed)
5. Update the Streamlit app credentials
6. Create an S3 bucket and upload project files
7. Create CloudFormation stack
8. Access the Streamlit application

## Detailed Setup Instructions

### Step 1: Create SSH Key Pair
1. Navigate to the EC2 console in your preferred region
2. Go to "Network & Security" > "Key Pairs"
3. Click "Create Key Pair"
4. Name your key pair and download the .pem file

### Step 2: Create Redshift Serverless Workgroup
1. Open the Amazon Redshift console
2. Navigate to "Serverless dashboard" > "Workgroups"
3. Click "Create workgroup"
4. Follow the wizard to set up your workgroup, noting the name for later use

### Step 3: Load Sample Data
1. Connect to your Redshift Serverless instance
2. Use the Redshift query editor or a SQL client to load sample data
   (Specific instructions for loading data will depend on your dataset)

### Step 4: Prepare Lambda Function (if needed)
If you need to modify the Lambda function:
1. Navigate to `bedrock-agent-text2sql-redshift/function/`
2. Make your changes to `lambda_function.py` and/or `redshift_serverless_functions.py`
3. Zip both files together: 
   ```
   zip -j lambda_function.zip lambda_function.py redshift_serverless_functions.py
   ```

### Step 5: Update Streamlit App Credentials
1. Open `bedrock-agent-text2sql-redshift/streamlit_app/credentials.json`
2. Add or modify user credentials as needed for frontend access

### Step 6: Create S3 Bucket and Upload Files
1. Create a new S3 bucket in your preferred region
2. Upload the entire `bedrock-agent-text2sql-redshift/` folder to the root of this bucket using the following AWS CLI command:
   ```
   cd bedrock-agent-text2sql-redshift/
   aws s3 sync . s3://your-bucket-name/bedrock-agent-text2sql-redshift/
   ```
   Replace `your-bucket-name` with the name of the S3 bucket you created.

### Step 7: Create CloudFormation Stack
1. Open the CloudFormation console
2. Click "Create stack" > "With new resources (standard)"
3. Upload the template file: `bedrock-agent-text2sql-redshift/cloudformation-template/ec2-streamlit-template.yaml`
4. Fill in the required parameters:
   - InstanceType: Choose an appropriate EC2 instance type
   - KeyPair: Select the SSH key pair created in Step 1
   - AgentName: Name for your Bedrock Agent
   - RedshiftWorkgroupName: Name of the Redshift Serverless workgroup created in Step 2
   - S3BucketName: Name of the S3 bucket created in Step 6
   - AllowedIP: Your public IP address for SSH access to the EC2 instance
5. Review and create the stack

### Step 8: Access the Streamlit Application
1. Once the CloudFormation stack is complete, find the EC2 instance public IP in the Outputs
2. Open a web browser and navigate to `http://<EC2-Public-IP>:8501`

### Step 9: Restart the Streamlit Application (if needed)
If you need to restart the Streamlit application:
1. Connect to your EC2 instance via SSH:
   ```
   ssh -i /path/to/your-key.pem ec2-user@<EC2-Public-IP>
   ```
2. Find the running Streamlit process:
   ```
   ps aux | grep streamlit
   ```
3. Note the process ID (PID) of the Streamlit application
4. Kill the process:
   ```
   kill <PID>
   ```
5. Navigate to the application directory:
   ```
   cd /home/ubuntu/app/streamlit_app
   ```
6. Restart the Streamlit application:
   ```
   nohup streamlit run app.py &
   ```
7. Exit the SSH session:
   ```
   exit
   ```
8. The Streamlit application should now be restarted and accessible at `http://<EC2-Public-IP>:8501`


### Checking Environment Variables

#### On Lambda:
1. Open the AWS Lambda console
2. Select your function
3. Go to the "Configuration" tab
4. Click on "Environment variables"

Key environment variables to check:
- `REDSHIFT_WORKGROUP_NAME`: The name of your Redshift Serverless workgroup

#### On EC2:
1. SSH into your EC2 instance
2. Check the environment variables:
   ```
   cat /etc/profile.d/bedrock_env.sh
   ```
   This will show you the following environment variables:
   - `AGENT_ID`: The ID of your Bedrock agent
   - `AGENT_ALIAS_ID`: The alias ID of your Bedrock agent
   - `AWS_REGION`: The AWS region where your resources are deployed

   You can also check if these variables are set in your current session:
   ```
   env | grep AGENT
   env | grep AWS_REGION
   ```

If these variables are not set or have incorrect values, you may need to source the environment file or restart your EC2 instance:
```
source /etc/profile.d/bedrock_env.sh
```

These environment variables are crucial for the Streamlit application to interact with the Bedrock agent correctly. If you're experiencing issues with the application, verifying these variables is a good first step in troubleshooting.


## Troubleshooting

If you encounter issues with the application, follow these steps to diagnose and potentially resolve the problem:

### 1. Check EC2 Instance Status
1. Open the AWS EC2 console
2. Locate your instance and check its status
3. Ensure it's in a "running" state with all status checks passed

### 2. Verify Environment Variables
1. SSH into your EC2 instance
2. Check the environment variables:
   ```
   cat /etc/profile.d/bedrock_env.sh
   ```
3. Ensure `AGENT_ID`, `AGENT_ALIAS_ID`, and `AWS_REGION` are set correctly
4. If not, source the file:
   ```
   source /etc/profile.d/bedrock_env.sh
   ```

### 3. Check User Data Log
1. SSH into your EC2 instance
2. View the user data execution log:
   ```
   sudo cat /var/log/cloud-init-output.log
   ```
3. Look for any error messages or failures during the initial setup

### 4. Check Streamlit Application Logs
1. SSH into your EC2 instance
2. View the Streamlit log:
   ```
   cat /home/ubuntu/app/streamlit_app/streamlit.log
   ```
3. Look for any error messages or warnings

### 5. Verify Lambda Function
1. Open the AWS Lambda console
2. Select your function
3. Check the "Configuration" tab for correct environment variables
4. Review recent invocations in the "Monitor" tab for any errors

### 6. Check Bedrock Agent Configuration
1. Open the Amazon Bedrock console
2. Go to "Agents" and select your agent
3. Verify the agent's status is "Active"
4. Check the associated Lambda function is correct

### 7. Review CloudWatch Logs
1. Open the CloudWatch console
2. Navigate to "Log groups"
3. Check logs for:
   - EC2 instance: `/var/log/cloud-init-output.log`
   - Lambda function: `/aws/lambda/<YourFunctionName>`
   - Bedrock agent: `/aws/bedrock/agents/<YourAgentName>`

### 8. Test Database Connectivity
1. Open the Amazon Redshift console in the AWS Management Console
2. In the navigation pane, choose "Query editor v2"
3. If prompted, select your Redshift Serverless workgroup
4. Try running a simple query, such as:
   ```sql
   SELECT current_date;
   ```
5. If the query fails, check:
   - The status of your Redshift Serverless workgroup
   - VPC and security group configurations
   - IAM permissions for your user/role

This method is more appropriate for Redshift Serverless and doesn't require direct SSH access to the EC2 instance. It also aligns better with AWS best practices for serverless database access.

Let's also add a note about checking the Redshift Serverless workgroup status:

### 11. Check Redshift Serverless Workgroup Status
1. Open the Amazon Redshift console
2. In the navigation pane, choose "Serverless dashboard"
3. Select your workgroup
4. Check the status - it should be "Available"
5. If not available, check the recent events for any errors or configuration issues

### 9. Restart Streamlit Application
If all else fails, try restarting the Streamlit application:
1. SSH into your EC2 instance
2. Run the restart script:
   ```
   /home/ubuntu/app/restart_streamlit.sh
   ```

### 10. Check CloudFormation Stack
1. Open the CloudFormation console
2. Select your stack
3. Go to the "Events" tab
4. Look for any failed resource creations or updates

If you're still experiencing issues after following these steps, you may need to review the CloudFormation template for any misconfigurations or consult AWS support for further assistance.

## Cleanup
To avoid unnecessary charges, remember to delete the following resources when you're done:
1. CloudFormation stack
2. S3 bucket
3. Redshift Serverless workgroup
4. SSH key pair (if no longer needed)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the MIT-0 License. See the LICENSE file for details.