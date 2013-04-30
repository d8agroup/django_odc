/**
 * Title: Configuration instructions and examples for posting data to the Twitter Post V01 ODC Post Adapter Source
 * User: mg@metalayer.com
 * Date: 4/30/13
 */

/**
 * Below is an example of the JSON format you should use to encode tweets sent to this post adapted.
 * PLEASE NOTE THAT ALL FIELDS ARE REQUIRED
 */
var tweets = [
    {
        text: '', //The raw tweet
        id_str: '', //The tweet id as a string
        created_at: 'Wed Aug 27 13:08:45 +0000 2013', //UTC encoded datetime taken directly from twitter
        favorite_count: 0, //The number of times this tweet has been favorited
        lang: 'en', //The language of the tweet taken directly from twitter
        retweet_count: 0, //The number of times this tweet has been retweeted
        user: {
            id_str: '', //The unique id of the user who authored the tweet
            profile_image_url: '', //The url of the profile image of this user
            screen_name: '' //The screen name of this author
        }
    }
];

/**
 * NOTE: YOU MUST BATCH UP THE TWEETS YOU SEND TO THIS API, ANYTHING OVER A CALL EVERY COUPLE OF SECONDS
 * IS LIKELY TO BREAK IT!
 */

/**
 * The above tweets collection should be posted to the adapter in your favourite language as raw JSON
 */

/**
 * Here is an example using jQuery
 */
$.ajax({
    url:'http://something.com',  // The url you have been provided
    type:"POST",  //The type of request, must be POST
    data:JSON.stringify(tweets),  // JSON stringify the tweets from above
    contentType:"application/json; charset=utf-8",  // Set the content type like this
    dataType:"json",  // Specify json data type
    success: function(return_data){},
    error:function(jqXHR, status, error){}
});

/**
 * Here is a full example using python with the tweetstream package
 */
/*
from copy import deepcopy
import json
from threading import Thread
import urllib2
import tweetstream

""" Do not set these """
RUNNING = True
TWEETS = []

""" Set these """
URL = 'http://localhost:8000/odc/source/11/post'
TWITTER_USERNAME = ""
TWITTER_PASSWORD = ""


""" Utility functions """
def async(gen):
    def func(*args, **kwargs):
        it = gen(*args, **kwargs)
        result = it.next()
        Thread(target=lambda: list(it)).start()
        return result
    return func


def make_request(data):
    global RUNNING
    req = urllib2.Request(URL, data, {'Content-Type': 'application/json'})
    f = urllib2.urlopen(req)
    result = json.loads(f.read())
    print result
    f.close()
    if result['status'] == 'error':
        RUNNING = False


@async
def handle_tweet(tweet):
    yield
    global TWEETS
    t = {
        'text': tweet['text'],
        'id_str': tweet['id_str'],
        'created_at': tweet['created_at'],
        'favorite_count': tweet.get('favorite_count', 0),
        'lang': tweet.get('lang', 'en'),
        'retweet_count': tweet.get('retweet_count', 0),
        'user': {
            'id_str': tweet['user']['id_str'],
            'profile_image_url': tweet['user']['profile_image_url'],
            'screen_name': tweet['user']['screen_name']
        }
    }
    TWEETS.append(t)
    number_of_tweets = len(TWEETS)
    print number_of_tweets, 'Tweets'
    if number_of_tweets >= 10:
        tweets = deepcopy(TWEETS)
        TWEETS = []
        make_request(json.dumps(tweets))


""" Programme """
with tweetstream.FilterStream(TWITTER_USERNAME, TWITTER_PASSWORD, locations=["-84.321732,33.840149","-75.460449,36.588322"]) as stream:
    for tweet in stream:
        if not RUNNING:
            break
        handle_tweet(tweet)

*/