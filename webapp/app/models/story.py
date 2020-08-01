from typing import Collection
from flask_continuum import VersioningMixin
from .. import db
import requests
from urllib.parse import urlencode


story_collections = db.Table('story_collections',
  db.Column('story_id', db.Integer, db.ForeignKey('stories.id'), primary_key=True),
  db.Column('collection_id', db.Integer, db.ForeignKey('collections.id'), primary_key=True)
)


user_collections = db.Table('user_collections',
  db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
  db.Column('collection_id', db.Integer, db.ForeignKey('collections.id'), primary_key=True)
)

class Collection(db.Model, VersioningMixin):
    __tablename__ = "collections"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    stories = db.relationship('Story', secondary=story_collections, backref=db.backref('collections', lazy=True), lazy='subquery')
    user = db.relationship('User', secondary=user_collections, backref=db.backref('collections', lazy=True), lazy='subquery') # TODO switch model to one-to-many
    public_id = db.Column(db.Integer, db.ForeignKey('lookup_values.id'))
    public = db.relationship('LookupValue', primaryjoin="and_(LookupValue.id==Collection.public_id, LookupValue.group=='bool')")


story_categories = db.Table('story_categories',
  db.Column('story_id', db.Integer, db.ForeignKey('stories.id'), primary_key=True),
  db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)


class Category(db.Model, VersioningMixin):
  __tablename__ = 'categories'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(64), unique=True)
  stories = db.relationship('Story', secondary=story_categories, backref=db.backref('categories', lazy=True), lazy='subquery')
  last_update_dt = db.Column(db.DateTime)
  last_update_user = db.Column(db.Integer, db.ForeignKey('users.id'))

  def __repr__(self):
    return self.name


class Story(db.Model, VersioningMixin):
    __tablename__ = 'stories'
    id = db.Column(db.Integer, primary_key=True)
    twitter_id = db.Column(db.Integer, unique=True)
    retweet_id = db.Column(db.Integer)
    quote_id = db.Column(db.Integer)
    text = db.Column(db.String(512))
    retweet_text = db.Column(db.String(512))
    quote_text = db.Column(db.String(512))
    oembed_min = db.Column(db.String(4096))
    oembed_full = db.Column(db.String(4096))
    sentiment = db.Column(db.Float)
    feature_set = db.Column(db.String(512))
    media_id = db.Column(db.Integer, db.ForeignKey('lookup_values.id'))
    media = db.relationship('LookupValue', primaryjoin="and_(LookupValue.id==Story.media_id, LookupValue.group=='bool')")
    comment_id = db.Column(db.Integer, db.ForeignKey('lookup_values.id'))
    comment = db.relationship('LookupValue', primaryjoin="and_(LookupValue.id==Story.comment_id, LookupValue.group=='bool')")
    thread_id = db.Column(db.Integer, db.ForeignKey('lookup_values.id'))
    thread = db.relationship('LookupValue', primaryjoin="and_(LookupValue.id==Story.thread_id, LookupValue.group=='bool')")
    visible_id = db.Column(db.Integer, db.ForeignKey('lookup_values.id'))
    visible = db.relationship('LookupValue', primaryjoin="and_(LookupValue.id==Story.visible_id, LookupValue.group=='bool')")
    origin = db.Column(db.String(128))
    curated_id = db.Column(db.Integer, db.ForeignKey('lookup_values.id'))
    curated = db.relationship('LookupValue', primaryjoin="and_(LookupValue.id==Story.curated_id, LookupValue.group=='bool')")
    last_update_dt = db.Column(db.DateTime)
    last_update_user = db.Column(db.Integer, db.ForeignKey('users.id'))

    @property
    def story_text(self):
        if self.retweet_id is not None:
            return self.retweet_text
        if self.quote_id is not None:
            return self.quote_text
        return self.text


    def generate_oembed(self, tid, maxwidth=220, hide=True):
        url = 'https://publish.twitter.com/oembed?'
        if hide:
            hide = 'true'
        else:
            hide = 'false'
        url = url + urlencode({'url': f"https://twitter.com/Interior/status/{tid}"})
        url = url + '&' + urlencode({'maxwidth': f"{str(maxwidth)}"})
        url = url + '&' + urlencode({'hide_media': f"{hide}"})
        url = url + '&' + urlencode({'hide_thread': f"{hide}"})
        url = url + '&' + urlencode({'omit_script': f"true"})
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Request ret urned an error: {response.status_code} URL:{url}")
        return response.json()

    def generate_oembeds(self, maxwidth):
        ret = True
        tid = self.twitter_id
        if self.quote_id is not None:
            tid = self.quote_id
        if self.retweet_id is not None:
            tid = self.retweet_id
        try:
            ret = self.generate_oembed(tid)
            self.oembed_min = ret['html']
        except Exception as e:
            print(f"Unable to generate mini oembed for story id {self.twitter_id} using tid {tid}")
            print(e)
            ret = False
        try:
            ret = self.generate_oembed(tid, hide=False, maxwidth=maxwidth)
            self.oembed_full = ret['html']
        except Exception as e:
            print(f"Unable to generate full oembed for story id {self.twitter_id} using tid {tid}")
            print(e)
            ret = False

        db.session.add(self)
        db.session.commit()
        return ret


class LookupValue(db.Model, VersioningMixin):
    __tablename__ = 'lookup_values'
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), nullable=False)
    value = db.Column(db.String(128), nullable=False)
    group = db.Column(db.String(64), nullable=False)
    last_update_dt = db.Column(db.DateTime)
    last_update_user = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def insert_defaults():
        lookupValues = [
            ("bool", "True", "Yes"),
            ("bool", "False", "No"),
        ]

        for l in lookupValues:
            lookupValue = LookupValue.query.filter_by(group=l[0], value=l[1]).first()
            if lookupValue is None:
                lookupValue = LookupValue(group=l[0], value=l[1], name=l[2])
            db.session.add(lookupValue)
        db.session.commit()
