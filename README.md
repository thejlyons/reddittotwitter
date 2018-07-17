# reddittotwitter
Bot that takes top posts on a given subreddit and tweets them

## Postgres DB
```
CREATE TABLE rfunny (id SERIAL NOT NULL UNIQUE, title text, stamp TIMESTAMP DEFAULT Now());
```