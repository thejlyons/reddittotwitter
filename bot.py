from urllib.parse import urlparse
from datetime import datetime, timedelta
from time import sleep
import random
import tweepy
import psycopg2
import pytz
import os

api = None
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


def tweet(text):
    min_delay = random.randint(1, 20 * 60)
    print("Tweeting in {} seconds.".format(min_delay))
    sleep(min_delay)

    api.update_status(text)


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

    result = urlparse(os.environ.get('DB_URL'))
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

            cur.execute("SELECT count(*) FROM tshirts")
            count = cur.fetchone()[0]

            cur.execute("SELECT * from tshirts WHERE priority_order = 0")
            top_row = cur.fetchone()
            tshirt = TShirt(top_row[1], top_row[2], top_row[3], top_row[4], top_row[5], top_row[6])

            tweet(tshirt.get_tweet())
            po = min(int(count * tshirt.priority()), count - 1)

            cur.execute('SELECT * FROM tshirts WHERE priority_order < {}'.format(po + 1))
            rows = cur.fetchall()
            for row in rows:
                cur.execute("UPDATE tshirts SET priority_order = %s WHERE id = %s", (max(0, row[-1] - 1), row[0]))

            cur.execute("UPDATE tshirts SET tweets = %s, new = %s, priority_order = %s where id = %s",
                        (tshirt.tweets, tshirt.new, po, top_row[0]))

            conn.commit()
            conn.close()
            sleep(60 * 6)
        sleep(60 * 5)
