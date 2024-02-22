import asyncio
from datetime import datetime

import boto3
from flask import Flask, request, jsonify
from tweetcapture.screenshot import TweetCapture

# start up flask
app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello():
    response_data = {'success': True}
    return jsonify(response_data)


@app.route('/get_twitter_embed', methods=['GET', 'POST'])
def get_twitter_embed():
    params_whitelist = [
        'url',
        'filename'
    ]

    # Get params from request
    params = {param: request.args.get(param, default=None, type=str) for param in params_whitelist}

    # Whitelist and sanitize params
    params = whitelist_and_sanitize(params, params_whitelist)

    url = params.get('url', '')
    filename = params.get('filename', '')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # create the screenshot
    try:
        return loop.run_until_complete(generate_screenshot(url, filename))
    finally:
        loop.close()


# run TweetCapture to create screenshot, call upload_to_s3 to upload the file
async def generate_screenshot(encoded_url, filename):
    # append .png to filename
    filename = f'{filename}.png'

    # Create a temporary directory to store the screenshot
    screenshot_path = f'/tmp/{filename}'

    # Use the encoded_url in your script logic
    tweet_capture = await TweetCapture().screenshot(encoded_url, screenshot_path)

    # Upload screenshot to S3
    return upload_to_s3(screenshot_path, filename)


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


# Function to whitelist and sanitize params
def whitelist_and_sanitize(params, params_whitelist):
    # Whitelist params
    whitelisted_params = {key: params[key] for key in params_whitelist if key in params}
    # TODO: Add sanitization logic here if needed
    return whitelisted_params


if __name__ == '__main__':
    # run flask on the local IP of our ec2 instance
    app.debug = True
    app.run(host='127.0.0.1', port=8000)
