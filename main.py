import os
import tempfile
from tweetcapture.screenshot import TweetCapture
from flask import Flask, request
import boto3
import asyncio

from datetime import datetime

# start up flask
app = Flask(__name__)


@app.route('/get_twitter_screenshot', methods=['GET', 'POST'])
def get_twitter_screenshot():
    url = request.args.get('url', default=1, type=str)
    filename = request.args.get('filename', default=1, type=str)
    print(f'url: {url} \n filename: {filename}')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(run_twitter_screenshot(url, filename))
    finally:
        loop.close()

    return "Script executed successfully"


# run async function generate_screenshot. Do we need this separate function?
async def run_twitter_screenshot(url, filename):
    s3_url = await generate_screenshot(url, filename)
    print(f'Screenshot uploaded to S3: {s3_url}')


# run TweetCapture to create screenshot, call upload_to_s3 to upload the file
async def generate_screenshot(encoded_url, filename):
    # Create a temporary directory to store the screenshot
    screenshot_path = f'/tmp/{filename}'

    # Use the encoded_url in your script logic
    tweet_capture = await TweetCapture().screenshot(encoded_url, screenshot_path)

    print(f'tweet_capture: {tweet_capture}')

    # Upload screenshot to S3
    s3_url = upload_to_s3(screenshot_path, filename)
    return s3_url


# upload the newly created img to s3 bucket
def upload_to_s3(screenshot_path, filename):
    print(f'screenshot path: {screenshot_path}')
    print(f'filename: {filename}')
    # Set up AWS S3 client (you should configure your credentials before using this)
    s3 = boto3.client('s3')

    # Specify the S3 bucket and key (path) where the image should be uploaded
    bucket_name = 'static.hiphopdx.com'

    # Get current year and month
    current_year_month = datetime.now().strftime('%Y/%m')

    # Our path to insert the screenshot
    key = f'assets/prod/img/tweets/{current_year_month}/{filename}'

    # Create our year/month subdirectory if it doesn't exist
    s3.put_object(Bucket=bucket_name, Key=f'assets/prod/img/tweets/{current_year_month}/')

    # Upload the file to S3
    s3.upload_file(screenshot_path, bucket_name, key)

    # Get the existing ACL
    acl = s3.get_object_acl(Bucket=bucket_name, Key=key)

    # Set the modified ACL back to the object
    s3.put_object_acl(
        ACL='public-read',
        Bucket=bucket_name,
        Key=key
    )

    s3_url = f'https://{bucket_name}/{key}'

    return s3_url


if __name__ == '__main__':
    print('we out here')
    app.run(host='0.0.0.0', port=5000)