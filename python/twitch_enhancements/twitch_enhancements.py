#WIP, Uploaded for reference, please don't use.

import requests

from datetime import datetime, timedelta, date, time

import hexchat

__module_name__ = "Twitch enhancements"
__module_version__ = "0.2"
__module_description__ = "Prints jtv messages, provides stream information"

liveChannels = []
firstRun = True

def checkmessage_cb(word, word_eol, userdata):
	string = ' '.join(word[0:3])
	string = string.replace(string[0:1],'')
	
	if(string == 'jtv!jtv@jtv.tmi.twitch.tv PRIVMSG ' + hexchat.get_info('nick')):
		format(word_eol[3], special=1)
		return hexchat.EAT_ALL
	
	return hexchat.EAT_NONE

def userstate_cb(word, word_eol, userdata):
	return hexchat.EAT_ALL

def stream_cb(word, word_eol, userdata):
	stream()

def stream():
	CHANNEL = hexchat.get_info("channel")

	if (hexchat.get_info("host") != "irc.twitch.tv"):
		hexchat.prnt("/STREAM works only in irc.twitch.tv chats")
		return
	
	obj = loadJSON('https://api.twitch.tv/kraken/streams/' + CHANNEL.strip('#'))
	
	if (obj is None):
		format(CHANNEL.title() + " is not live on twitch.tv.", special=1)
	else:
		if (obj["stream"] == None):
			format(CHANNEL.title() + " is not live on twitch.tv.", special=1)
		else:
			format(CHANNEL.title() + " is streaming for " + str(obj["stream"]["viewers"]) + " viewers on " + obj["stream"]["channel"]["url"], special=1)	

def checkStreams_cb(userdata):
	checkStreams()
	return 1 # Keep it going...


def checkStreams():
	global firstRun
	if(firstRun):
		hexchat.unhook(timerHook)
		hexchat.hook_timer(300000, checkStreams_cb)
		firstRun = False

	channels = hexchat.get_list("channels")
	realChannels = []
	channelObjects = {}
	for channel in channels:
		if(channel.server == "tmi.twitch.tv" and channel.channel[0] == '#'):
			realChannels.append(channel.channel.strip('#'))
			channelObjects[channel.channel.strip('#')] = channel
	if len(realChannels) > 0:
		streams = ",".join(realChannels)
		obj = loadJSON('https://api.twitch.tv/kraken/streams?channel=' + streams)
		# Returns only streams that are currently live, but returns them all in one go.
		if (obj is not None):
			streamData = {}
			for stream in obj["streams"]:
				streamData[stream["channel"]["name"]] = stream
			for channel in realChannels:
				newTopic = "\00318{0}\00399 - \00320\002OFFLINE\002\00399 | \035Stream is offline\017".format(channel)
				if (channel in streamData):
					newTopic = "\00318{0}\00399 - \00319\002LIVE\002\00399 for {1} viewers | Now playing: \00318{2}\00399 | {3}".format(streamData[channel]["channel"]["display_name"], streamData[channel]["viewers"], streamData[channel]["channel"]["game"], streamData[channel]["channel"]["status"])
				if (get_topic(channelObjects[channel]) is not None):
					if (hexchat.strip(newTopic) != hexchat.strip(get_topic(channelObjects[channel]))):
						set_topic(channelObjects[channel], newTopic)
				else:
					set_topic(channelObjects[channel], newTopic)
					

def set_topic(ctx, message):
	ctx.context.command("RECV :{0}!Topic@twitch.tv TOPIC {0} :{1}".format(ctx.channel, message))
	
def get_topic(ctx):
	return ctx.context.get_info("topic")

def uptime_cb(word, word_eol, userdata):
	uptime()


def uptime():
	user = hexchat.get_info("channel").strip('#')
	url = 'https://api.twitch.tv/kraken/channels/' + user + '/videos?limit=1&broadcasts=true'

	try:
		obj = loadJSON('https://api.twitch.tv/kraken/streams/' + user)
		if(obj["stream"] == None):
			raise Exception
		
		latestbroadcast = loadJSON(url)['videos'][0]['_id']
		secondurl = 'https://api.twitch.tv/kraken/videos/' + latestbroadcast
		starttimestring = loadJSON(secondurl)['recorded_at']

		timeFormat = "%Y-%m-%dT%H:%M:%SZ"
		startdate = datetime.strptime(starttimestring, timeFormat)
		currentdate = datetime.utcnow()
		combineddate = currentdate - startdate - timedelta(microseconds=currentdate.microsecond)		
		format(user.title() + " has been streaming for " + str(combineddate))
	except Exception:
		format(user.title() + " is not streaming.")

def unload_cb(userdata):
	hexchat.prnt("\00304" + __module_name__ + " " +  __module_version__ + " successfully unloaded.\003")

def format(string, special=0):
	if(special):
		string = string.replace(string[:1],'')
	string = '\002\035' + string
	hexchat.prnt(string)

def loadJSON(url):
	try:
		r = requests.get(url, timeout=3)
		return r.json()
	except Exception as e:
		hexchat.prnt('Exception: ' + e.message)
		return None

hexchat.hook_server('PRIVMSG', checkmessage_cb)
hexchat.hook_server('USERSTATE', userstate_cb)
hexchat.hook_command('STREAM', stream_cb, help ="/STREAM Use in twitch.tv chats to check if the stream is online.")
hexchat.hook_command('UPTIME', uptime_cb)

hexchat.hook_unload(unload_cb)

timerHook = hexchat.hook_timer(10000, checkStreams_cb)


hexchat.prnt("\00304" + __module_name__ + " " + __module_version__ + " successfully loaded.\003")
