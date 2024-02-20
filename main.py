from datetime import datetime
from tweetcapture.screenshot import TweetCapture
from flask import Flask, request, jsonify
import boto3
import asyncio

# start up flask
app = Flask(__name__)


@app.route('/')
def hello():
    response_data = {'success': True}
    return jsonify(response_data)

@app.route('/get_twitter_screenshot', methods=['GET', 'POST'])
def get_twitter_screenshot():
    params_whitelist = [
        'url',
        'filename'
    ]

    # Get params from request
    params = {param: request.args.get(param, default=None, type=str) for param in params_whitelist}
    print(f'Params: {params}')

    # Whitelist and sanitize params
    params = whitelist_and_sanitize(params, params_whitelist)

    url = params.get('url', '')
    filename = params.get('filename', '')

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # create the screenshot
    try:
        image_url = loop.run_until_complete(run_twitter_screenshot(url, filename))
        response_code = 200 # replace with actual response code
        errors = []
        payload = prepare_payload(params, image_url, response_code, errors)
        return jsonify(payload)
    finally:
        loop.close()


# run async function generate_screenshot. Do we need this separate function?
async def run_twitter_screenshot(url, filename):
    s3_url = await generate_screenshot(url, filename)
    print(f'Screenshot uploaded to S3: {s3_url}')
    return s3_url


# run TweetCapture to create screenshot, call upload_to_s3 to upload the file
async def generate_screenshot(encoded_url, filename):
    # Create a temporary directory to store the screenshot
    screenshot_path = f'/tmp/{filename}'

    # Use the encoded_url in your script logic
    tweet_capture = await TweetCapture().screenshot(encoded_url, screenshot_path)

    print(f'tweet_capture: {tweet_capture}')

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


# Function to prepare the payload
def prepare_payload(params, result, response_code, errors):
    payload = {
        'params': params,
        'timestamp': datetime.utcnow().strftime('%a %b %d %Y %H:%M:%S UTC'),
        'success': response_code == 200,
        'code': response_code,
        'errors': errors,
        'api_version': 1,
        'data': result
    }

    return payload


# Function to whitelist and sanitize params
def whitelist_and_sanitize(params, params_whitelist):
    # Whitelist params
    whitelisted_params = {key: params[key] for key in params_whitelist if key in params}
    # TODO: Add sanitization logic here if needed
    return whitelisted_params



if __name__ == '__main__':
    print('we out here')
    app.run(host='127.0.0.1', port=8000, debug=True)