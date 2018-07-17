# reddittotwitter
Bot that takes top posts on a given subreddit and tweets them

## Postgres DB
```
CREATE TABLE rfunny (id SERIAL NOT NULL UNIQUE, title text, stamp TIMESTAMP DEFAULT Now());
```

## Heroku Scale Worker
Heroku Hobby defaults to one web engine and zero workers. For this script to run, you need to spin up a worker to run the bot.
```commandline
heroku ps:scale worker=1
```