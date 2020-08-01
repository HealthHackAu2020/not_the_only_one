import requests
import json
import urllib.parse
from time import sleep
from pprint import pprint
from requests.auth import AuthBase
try:
  from .. import config
except:
  import config

######################## Consume Twitter Stuff ########################

consumer_key = config.Config.CONSUMER_KEY
consumer_secret = config.Config.CONSUMER_SECRET

stream_url = "https://api.twitter.com/labs/1/tweets/stream/filter"
rules_url = "https://api.twitter.com/labs/1/tweets/stream/filter/rules"

sample_rules = [
  { 'value': 'from:NTOO_Org', 'tag': 'NTOO Account' },
  { 'value': 'tag:NotTheOnlyOne', 'tag': 'NTOO Hashtag' },
]

class BearerTokenAuth(AuthBase):
  def __init__(self, consumer_key, consumer_secret):
    self.bearer_token_url = "https://api.twitter.com/oauth2/token"
    self.consumer_key = consumer_key
    self.consumer_secret = consumer_secret
    self.bearer_token = self.get_bearer_token()

  def get_bearer_token(self):
    response = requests.post(
      self.bearer_token_url, 
      auth=(self.consumer_key, self.consumer_secret),
      data={'grant_type': 'client_credentials'},
      headers={'User-Agent': 'NotTheOnlyOneApp'})

    if response.status_code != 200:
      raise Exception(f"Cannot get a Bearer token (HTTP %d): %s" % (response.status_code, response.text))

    body = response.json()
    return body['access_token']

  def __call__(self, r):
    r.headers['Authorization'] = f"Bearer %s" % self.bearer_token
    r.headers['User-Agent'] = 'TwitterDevFilteredStreamQuickStartPython'
    return r


def get_all_rules(auth):
  response = requests.get(rules_url, auth=auth)

  if response.status_code != 200:
    raise Exception(f"Cannot get rules (HTTP %d): %s" % (response.status_code, response.text))

  return response.json()


def delete_all_rules(rules, auth):
  if rules is None or 'data' not in rules:
    return None

  ids = list(map(lambda rule: rule['id'], rules['data']))

  payload = {
    'delete': {
      'ids': ids
    }
  }

  response = requests.post(rules_url, auth=auth, json=payload)

  if response.status_code != 200:
    raise Exception(f"Cannot delete rules (HTTP %d): %s" % (response.status_code, response.text))

def set_rules(rules, auth):
  if rules is None:
    return

  payload = {
    'add': rules
  }

  response = requests.post(rules_url, auth=auth, json=payload)

  if response.status_code != 201:
    raise Exception(f"Cannot create rules (HTTP %d): %s" % (response.status_code, response.text))

def stream_connect(auth):
  response = requests.get(stream_url, auth=auth, stream=True)
  for response_line in response.iter_lines():
    if response_line:
      pprint(json.loads(response_line))

def setup_rules(auth):
  current_rules = get_all_rules(auth)
  delete_all_rules(current_rules, auth)
  set_rules(sample_rules, auth)

def get_bearer_token():
    return BearerTokenAuth(consumer_key, consumer_secret)

def setup_stream_rules(bearer_token):
    return setup_rules(bearer_token)

def start_stream(bearer_token):
    timeout = 0
    while True:
        stream_connect(bearer_token)
        print(f"Received disconnect from stream! Timeout: {timeout}")
        sleep(2 ** timeout)
        timeout += 1


def search_twitter(bearer_token, query="from:NTOO_Org"):
    query = urllib.parse.quote(query)

    url = f"https://api.twitter.com/labs/2/tweets/search?query={query}&max_results=100&tweet_mode=extended"

    headers = {"Accept-Encoding": "gzip"}
    
    url = "https://api.twitter.com/1.1/tweets/search/fullarchive/OrgReturn.json"
    payload = {}
    payload['query'] = query
    payload['max_results']= 100

    response = requests.get(url, auth=bearer_token, headers = headers)

    if response.status_code != 200:
        raise Exception(f"Request reurned an error: {response.status_code} {response.text}")

    parsed = json.loads(response.text)
    pretty_print = json.dumps(parsed, indent=2, sort_keys=True)
    with open('searchTweetsData.json', 'a', encoding='utf-8') as f:
      json.dump(pretty_print, f)


def save_old_tweets():
  from searchtweets import load_credentials, gen_rule_payload, ResultStream
  import json

  premium_search_args = load_credentials("twitter_keys_fullarchive.yaml", yaml_key="search_tweets_api", env_overwrite=False)

  query = "from:NTOO_Org"
  rule = gen_rule_payload(query, results_per_call=100)

  rs = ResultStream(rule_payload=rule, max_results=1000, **premium_search_args)

  with open('fullTweetsData.json', 'a', encoding='utf-8') as f:
    for tweet in rs.stream():
      json.dump(tweet, f)
      f.write('\n')


######################## Process tweet content ########################

### Example

# import twitter_helper as th
# data = th.load_saved_tweets()
# text = th.parse_tweet_text(data)
# tweetProcessor = th.PreProcessTweets()
# preprocessedFeatureSet = tweetProcessor.processTweets(text)
# counts = th.word_count_list_lists(preprocessedFeatureSet)

import re
from nltk.tokenize import word_tokenize
from string import punctuation
from nltk.corpus import stopwords 

def load_saved_tweets():
  import json
  data = None
  with open('fullTweetsData.json') as json_file:
    data = json.load(json_file)

  return data

def parse_tweet_text(data):
  texts = []
  for entry in data:
    text = []
    if 'extended_tweet' in entry.keys():
      text.append(entry['extended_tweet']['full_text'])
    else:
      text.append(entry['text'])
    if 'retweeted_status' in entry.keys():
      if 'extended_tweet' in entry['retweeted_status'].keys():
        text.append(entry['retweeted_status']['extended_tweet']['full_text'])
      else:
        text.append(entry['retweeted_status']['text'])
    if 'quoted_status' in entry.keys():
      if 'extended_tweet' in entry['quoted_status'].keys():
        text.append(entry['quoted_status']['extended_tweet']['full_text'])
      else:
        text.append(entry['quoted_status']['text'])
    if len(text) > 0:
      texts.append(' '.join(text))
    else:
      print(f"No text for {entry['id']}")
  
  return texts

class PreProcessTweets:
  def __init__(self):
    self.stopwords = set(stopwords.words('english') + list(punctuation) + ['AT_USER','URL', 'rt', '``'])
      
  def processTweets(self, list_of_tweets):
    processedTweets=[]
    for tweet in list_of_tweets:
      processedTweets.append(self.processTweet(tweet))
    return processedTweets
  
  def processTweet(self, tweet):
    tweet = tweet.encode('ascii', errors='ignore').strip().decode('ascii') # strip unicode
    tweet = tweet.lower() # convert text to lower-case
    tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))', 'URL', tweet) # remove URLs
    tweet = re.sub('@[^\s]+', 'AT_USER', tweet) # remove usernames
    tweet = re.sub(r'#([^\s]+)', r'\1', tweet) # remove the # in #hashtag
    tweet = word_tokenize(tweet) # remove repeated characters
    return [word for word in tweet if word not in self.stopwords]

def word_count_list_lists(lst):
    counts = dict()
    words = []

    for ls in lst:
      for word in ls:
        words.append(word)

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return {k: v for k, v in sorted(counts.items(), key=lambda item: item[1])}