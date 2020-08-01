#!/usr/bin/env python
import os
import subprocess

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Command, Server as _Server, Option, Shell
from redis import Redis
from rq import Connection, Queue, Worker

from app import app, db
from app.models import Role, User, Group, Story, Category, LookupValue
from config import Config

#app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

def make_shell_context():
   return dict(app=app, db=db, User=User, Role=Role)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.drop_all()
    db.create_all()
    db.session.commit()


@manager.option(
    '-n',
    '--number-users',
    default=10,
    type=int,
    help='Number of each model type to create',
    dest='number_users')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)


@manager.command
def setup():
    """Runs the set-up needed for production."""
    setup_general()

def load_saved_tweets():
  import json
  data = None
  with open('app/fullTweetsData.json') as json_file:
    data = json.load(json_file)
  return data

def process_tweets(tweets):
    import app.twitter_helper as th
    import sys
    tweetProcessor = th.PreProcessTweets()
    tweet_count = 0
    total_count = len(tweets)
    for tweet in tweets:
        if tweet_count % 50 == 0:
            sys.stdout.write(f"Tweets processed: {tweet_count}/{total_count}   \r")
            sys.stdout.flush()
        story = Story()
        story.twitter_id = tweet['id']
        if 'extended_tweet' in tweet.keys():
            story.text = tweet['extended_tweet']['full_text']
        else:
            story.text = tweet['text']
        if 'retweeted_status' in tweet.keys():
            story.retweet_id = tweet['retweeted_status']['id']
            if 'extended_tweet' in tweet['retweeted_status'].keys():
                story.retweet_text = tweet['retweeted_status']['extended_tweet']['full_text']
            else:
                story.retweet_text = tweet['retweeted_status']['text']
        if 'quoted_status' in tweet.keys():
            story.quote_id = tweet['quoted_status']['id']
            if 'extended_tweet' in tweet['quoted_status'].keys():
                story.quote_text = tweet['quoted_status']['extended_tweet']['full_text']
            else:
                story.quote_text = tweet['quoted_status']['text']
        
        text = th.parse_tweet_text([tweet])
        story.feature_set = ' '.join(tweetProcessor.processTweet(text[0]))
        # TODO sentiment and category processing
        try:
            if len(tweet['entities']['media']) > 0:
                story.media = LookupValue.query.filter_by(group="bool",value="True").first()
        except:
            story.media = LookupValue.query.filter_by(group="bool",value="False").first()
        if story.text.lower().startswith("rt "):
            story.comment = LookupValue.query.filter_by(group="bool",value="False").first()
        else:
            story.comment = LookupValue.query.filter_by(group="bool",value="True").first()
        story.thread = LookupValue.query.filter_by(group="bool",value="False").first()
        

        ret = story.generate_oembeds(Config.MAX_TWITTER_OEMBED_WIDTH)
        if ret:
            story.visible = LookupValue.query.filter_by(group="bool",value="True").first()
        else:
            story.visible = LookupValue.query.filter_by(group="bool",value="False").first()
        
        story.origin = "initial"
        story.curated = LookupValue.query.filter_by(group="bool",value="False").first()
        db.session.add(story)
        db.session.commit()
        tweet_count += 1


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    Role.insert_roles()
    LookupValue.insert_defaults()
    admin_query = Role.query.filter_by(name='Administrator')
    if admin_query.first() is not None:
        if User.query.filter_by(email=Config.ADMIN_EMAIL).first() is None:
            user = User(
                first_name=Config.ADMIN_FIRSTNAME,
                last_name=Config.ADMIN_LASTNAME,
                password=Config.ADMIN_PASSWORD,
                confirmed=True,
                role=admin_query.first(),
                email=Config.ADMIN_EMAIL)
            db.session.add(user)
            db.session.commit()
            print('Added administrator {}'.format(user.full_name()))
            for group in ['Reviewer']:
                g = Group(name=group,users=[user])
                db.session.add(g)
                db.session.commit()
                print('Added group {}'.format(group))

    user_query = Role.query.filter_by(name='User')
    if user_query.first() is not None:
        if User.query.filter_by(email=Config.USER_EMAIL).first() is None:
            user = User(
                first_name=Config.USER_FIRSTNAME,
                last_name=Config.USER_LASTNAME,
                password=Config.USER_PASSWORD,
                confirmed=True,
                role=user_query.first(),
                email=Config.USER_EMAIL)
            db.session.add(user)
            db.session.commit()
            print('Added user {}'.format(user.full_name()))
            for group in ['Reviewer']:
                g = Group.query.filter_by(name=group).first()
                g.users.append(user)
                db.session.add(g)
                db.session.commit()
                print('Added to group {}'.format(group))

    story_query = Story.query.all()
    if len(story_query) == 0:
        print("Processing pre-saved tweets")
        tweets = load_saved_tweets()
        process_tweets(tweets)
        print("Finishing processing tweets")
       

@manager.command
def run_worker():
    """Initializes a slim rq task queue."""
    listen = ['default']
    conn = Redis(
        host=app.config['RQ_DEFAULT_HOST'],
        port=app.config['RQ_DEFAULT_PORT'],
        db=0,
        password=app.config['RQ_DEFAULT_PASSWORD'])

    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()


@manager.command
def format():
    """Runs the yapf and isort formatters over the project."""
    isort = 'isort -rc *.py app/'
    yapf = 'yapf -r -i *.py app/'

    print('Running {}'.format(isort))
    subprocess.call(isort, shell=True)

    print('Running {}'.format(yapf))
    subprocess.call(yapf, shell=True)


if __name__ == '__main__':
    manager.run()
