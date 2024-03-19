from datetime import datetime
import boto3

# Set up AWS S3 client (you should configure your credentials before using this)
s3 = boto3.client('s3')

# Specify the S3 bucket and key (path) where the image should be uploaded
bucket_name = 'static.hiphopdx.com'

# Get current year and month
current_year_month = datetime.now().strftime('%Y/%m')

# Our path to insert the screenshot
key = f'assets/prod/img/tweets/{current_year_month}/test-cli-upload-1.png'

# Create our year/month subdirectory if it doesn't exist
s3.put_object(Bucket=bucket_name, Key=f'assets/prod/img/tweets/{current_year_month}/')

# Upload the file to S3
s3.upload_file('/home/ec2-user/twitter-embeds/@HipHopDX_1769905153896067089_tweetcapture.png', bucket_name, key)

# Get the existing ACL
acl = s3.get_object_acl(Bucket=bucket_name, Key=key)

# Set the modified ACL back to the object
s3.put_object_acl(
    ACL='public-read',
    Bucket=bucket_name,
    Key=key
)

s3_url = f'https://{bucket_name}/{key}'

print(s3_url)
