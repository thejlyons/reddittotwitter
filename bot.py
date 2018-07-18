from datetime import datetime, timedelta
from time import sleep
import random
import os
from urllib.parse import urlparse
import urllib.request
import json
import urllib.request
import shutil
import psycopg2
import pytz
import tweepy

api = None
post_types = ['jpg', 'gif', 'gifv', 'png']
times = os.environ.get('TIMES').split(",")


def time_to_tweet():
    for time in times:
        time = [int(t) for t in time.split(":")]
        now = datetime.now(pytz.timezone('US/Mountain'))
        start = now.replace(hour=time[0], minute=time[1], second=0) + timedelta(minutes=-5)
        end = start + timedelta(minutes=10)
        if start <= now < end:
            return True
    return False


def tweet(handle, text, media):
    user = '/u/{}'.format(handle)
    try:
        api.get_user(handle)
        user = '@{}'.format(handle)
    except Exception:
        pass
    min_delay = random.randint(1, 20 * 60)
    print("Tweeting in {} seconds.".format(min_delay))
    sleep(min_delay)

    message = "{}: {} {}".format(user, text, get_hashtags(text))
    api.update_with_media(media, status=message)
    os.remove(media)


def get_hashtags(text):
    return "#funny #humor #hilarious #lol #haha #lmao #lmfao #rofl"


if __name__ == '__main__':
    print("Booting up at {:%H:%M}".format(datetime.now(pytz.timezone('US/Mountain'))))
    # Set up Twitter API connection
    CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
    ACCESS_KEY = os.environ.get('TWITTER_ACCESS_KEY')
    ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
    api = tweepy.API(auth)

    result = urlparse(os.environ.get('DATABASE_URL'))
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname

    while True:
        if time_to_tweet():
            conn = psycopg2.connect(
                database=database,
                user=username,
                password=password,
                host=hostname
            )
            cur = conn.cursor()

            cur.execute("DELETE FROM {} WHERE stamp < NOW() - interval '25 hours'".format(os.environ['DB_TABLE']))
            cur.execute("SELECT * from {}".format(os.environ['DB_TABLE']))
            rows = cur.fetchall()
            in_db = [row[1] for row in rows]

            url = "https://www.reddit.com/r/{}/top/.json?t=day".format(os.environ['SUBREDDIT'])
            hdr = {'User-Agent': '/r/{} scraper by /u/{}'.format(os.environ['SUBREDDIT'], os.environ['REDDIT_USER'])}
            req = urllib.request.Request(url, headers=hdr)

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                for child in data['data']['children']:
                    post_type = child['data']['url'].split('.')[-1]
                    title = child['data']['title']
                    media_file = '{:%Y%m%d-%H%M}.{}'.format(datetime.now(), post_type)
                    if title not in in_db and post_type in post_types:
                        with urllib.request.urlopen(child['data']['url']) as post, \
                                open(media_file, 'wb') as out_file:
                            shutil.copyfileobj(post, out_file)
                        cur.execute("INSERT INTO {} (title) VALUES (%s)".format(os.environ['DB_TABLE']), title)
                        tweet(child['data']['author'], child['data']['title'], media_file)
                        break
            conn.commit()
            conn.close()
            sleep(60 * 6)
        sleep(60 * 5)
