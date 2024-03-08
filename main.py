from datetime import datetime
import os
import traceback
import boto3
from flask import Flask, request, jsonify
from tweetcapture.screenshot import TweetCapture
from fake_useragent import UserAgent
# start up flask
app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello():
    response_data = {'success': True}
    return jsonify(response_data)


# Get params from request, create image file in /tmp/,
# upload to s3, return s3 url
@app.route('/get_twitter_embed', methods=['GET', 'POST'])
async def get_twitter_embed():
    params_whitelist = [
        'url',
        'filename'
    ]

    # Get params from request
    params = {param: request.args.get(param, default=None, type=str) for param in params_whitelist}

    # Whitelist and sanitize params
    params = whitelist_and_sanitize(params, params_whitelist)
    url, filename = params.get('url', ''), params.get('filename', '')

    # append .png to filename and create temp filepath
    filename_with_extension = f'{filename}.png'
    screenshot_path = f'/tmp/{filename_with_extension}'

    # debug log
    app.logger.info('getting screenshot at url %s', url)
    app.logger.info('filename: %s', filename)

    # create image file
    try:
        tweet = TweetCapture()
        tweet.add_chrome_argument("--enable-javascript")  # needed to capture video thumbnails
        tweet.add_chrome_argument("--disable-extensions")  # needed to capture video thumbnails
        tweet.add_chrome_argument("--no-sandbox")
        tweet.add_chrome_argument("--disable-gpu")
        tweet_screenshot_path = await tweet.screenshot(url, screenshot_path)
    except Exception as error:
        traceback.print_exc(error)
        return

    app.logger.info('tweet capture: %s', tweet_screenshot_path)

    # upload image and get url
    image_url = await upload_to_s3(tweet_screenshot_path, filename_with_extension)

    app.logger.info('image url: %s', image_url)

    # remove the file created in /tmp/
    os.remove(tweet_screenshot_path)

    return image_url


# upload the newly created img to s3 bucket
async def upload_to_s3(screenshot_path, filename):
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


# run our app with specified host & port
if __name__ == '__main__':
    app.debug = True
    # run flask on the local IP of our ec2 instance
    app.run(host='127.0.0.1', port=8000)
