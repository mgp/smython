import hashlib
import urllib2
import json

from datetime import datetime


# Nit: While Smython is a good name for the project, this might be more descriptive as SmiteClient. Mayyyyybe.
class Smython(object):
    # The first line of this docstring, which refers to the "python tool," is really describing everything in this file.
    # Therefore you could move it to the verrry top of this file, where it will be a docstring for the module.
    # The remaining lines that describe dev_id, auth_key, and lang actually describe the parameters for __init__.
    # So move them into their own docstring under __init__, similar to how you have docstrings for the other methods below.
    """
    A python tool to make client API requests to the Smite API
    Attributes:
        dev_id: Your private developer ID supplied by Hi-rez. Can be requested here: https://fs12.formsite.com/HiRez/form48/secure_index.html
        auth_key: Your authorization key
        lang: the language code needed by some queries, defaults to english.
    """
    
    # Sweet, I like how you pulled these strings out into constants.
    # Since they're meant to be used only by this implementation, and not by the user of this class, and are private,
    # prefix them with an underscore (so _BASE_URL, etc). That's the best you can do in Python, which doesn't have a
    # "private" access modififer.
    BASE_URL = 'http://api.smitegame.com/smiteapi.svc/'
    RESPONSE_FORMAT = 'json'
    SESSION = None

    def __init__(self, dev_id, auth_key, lang=1):
        self.dev_id = str(dev_id)
        self.auth_key = str(auth_key)
        self.lang = lang

    # The client should not call this method correctly, correct?  Instead the client shoudld call one of the
    # docstring'd methods below? If so, name this _make_request.
    def make_request(self, methodname, parameters=None):
        # Ahh, this is interesting. You're referring to self.SESSION here, but because SESSION is in all-caps,
        # which made me think that it's a static/class-wide variable. But really each Smython instance can have its
        # own session. Remove SESSION above, and in __init__, do "self._session = None". Then refer to "self._session".
        if not self.SESSION or not self._test_session(self.SESSION):
            self.SESSION = self._create_session()

        # Nice job breaking out the URL building into its own method.
        url = self._build_url(methodname, parameters)
        return json.loads(urllib2.urlopen(url).read())

    # You're building URLs in other places, but this is only used by _make_request.
    # Maybe name this "_build_request_url".
    def _build_url(self, methodname, parameters=None):
        # To make it clear that BASE_URL is a class constant, make the rhs Smython.BASE_URL.
        base = self.BASE_URL
        signature = self._create_signature(methodname)
        timestamp = self._create_now_timestamp()
        session_id = self.SESSION.get("session_id")

        # Ditto for changing self.RESPONSE_FORMAT to Smython.RESPONSE_FORMAT
        path = [methodname + self.RESPONSE_FORMAT, self.dev_id, signature, session_id, timestamp]
        # If in the list of arguments, you use "parameters=()" instead of "parameters=None", you can actually remove
        # this conditional.
        if parameters:
            # Can do path += [str(param) for param in parameters]
            path = path + [str(param) for param in parameters]
        # By the time I've gotten here, I've forgotten what "base" is. Maybe eliminate base and just make this:
        # return Smython.BASE_URL + '/'.join(path)
        return base + '/'.join(path)

    def _create_session(self):
        signature = self._create_signature('createsession')
        # You interpolate once, then concatenate the other times! Probably more typical (and faster to do):
        # url = (%screatesessionjson%s/%s%s' % (self.BASE_URL, self.dev_id, signature, self._create_now_timestamp())
        # Or, you could do:
        # '{0}createsessionjson/{1}/{2}{3}'.format(self.BASE_URL, self.dev_id, signature, self._create_now_timestamp())
        # Which might be more readable here. Actually, looking at that, if you remove the trailing / from BASE_URL it's:
        # '{0}/createsessionjson/{1}/{2}{3}'.format(self.BASE_URL, self.dev_id, signature, self._create_now_timestamp())
        # Which I think flows better. Whew :)
        url = self.BASE_URL + "createsessionjson/" + self.dev_id + "/%s/" % signature + self._create_now_timestamp()
        return json.loads(urllib2.urlopen(url).read())

    def _create_now_timestamp(self):
        # I would kinda want to rename dt to datetime_now.
        dt = datetime.utcnow()
        return dt.strftime("%Y%m%d%H%M%S")

    def _create_signature(self, methodname):
        # Again nice job breaking this out into its own method.
        now = self._create_now_timestamp()
        return hashlib.md5(self.dev_id + methodname + self.auth_key + now).hexdigest()

    def _test_session(self, session):
        methodname = 'testsession'
        timestamp = self._create_now_timestamp()
        signature = self._create_signature(methodname)
        # Here you're building a URL that's kind of similar to what's being built in _create_session.
        #
        # Maybe make a method like:
        # def _build_url_with_parts(self, parts):
        #   all_parts = [self.BASE_URL] + parts
        #   return '/'.join(all_parts)
        #
        # And then _test_session and _create_session can use them both.
        # Or somehow get it to the point where this method calls _create_session -- since this method is testing the
        # validity of what _create_session creates? 
        path = "/".join(
            [methodname + self.RESPONSE_FORMAT, self.dev_id, signature, session.get("session_id"), timestamp])
        url = self.BASE_URL + path
        return "successful" in urllib2.urlopen(url).read()

    def get_data_used(self):
        """
        :return : Returns a dictionary of daily usage limits and the stats against those limits
        """
        return self.make_request('getdataused')

    def get_gods(self):
        """
        :return: Returns all smite Gods and their various attributes
        """
        return self.make_request('getgods', self.lang)

    def get_items(self):
        """
        :return: Returns all Smite items and their various attributes
        """
        return self.make_request('getitems', [self.lang])

    def get_god_recommended_items(self, god_id):
        """
        :param god_id: ID of god you are quering against. Can be found in get_gods return result.
        :return: Returns a dictionary of recommended items for a particular god
        """
        return self.make_request('getgodrecommendeditems', [god_id])

    def get_esports_proleague_details(self):
        """
        :return: Returns the matchup information for each matchup of the current eSports pro league session.
        """
        return self.make_request('getesportsproleaguedetails')

    def get_top_matches(self):
        """
        :return: Returns the 50 most watch or most recent recorded matches
        """
        return self.make_request('gettopmatches')

    def get_match_details(self, match_id):
        """
        :param match_id: The id of the match
        :return: Returns a dictionary of the match and it's attributes.
        """
        return self.make_request('getmatchdetails', [match_id])

    def get_team_details(self, clan_id):
        """
        :param clan_id: The id of the clan
        :return: Returns the details of the clan in a python dictionary
        """
        return self.make_request('getteamdetails', [clan_id])

    def get_team_match_history(self, clan_id):
        """
        :param clan_id: The ID of the clan.
        :return: Returns a history of matches from the given clan.
        """
        return self.make_request('getteammatchhistory', [clan_id])

    def get_team_players(self, clan_id):
        """
        :param clan_id: The ID of the clan
        :return: Returns a list of players for the given clan.
        """
        return self.make_request('getteamplayers', [clan_id])

    def search_teams(self, search_team):
        """
        :param search_team: The string search term to search against
        :return: Returns high level information for clan names containing search_team string
        """
        return self.make_request('searchteams', [search_team])

    def get_player(self, player_name):
        """
        :param player_name: the string name of a player
        :return: Returns league and non-league high level data for a given player name
        """
        return self.make_request('getplayer', [player_name])

    def get_friends(self, player):
        """
        :param player: The player name or a player ID
        :return: Returns a list of friends
        """
        return self.make_request('getfriends', [player])

    def get_god_ranks(self, player):
        """
        :param player: The player name or player ID
        :return: Returns the rank and worshippers value for each God the player has played
        """
        return self.make_request('getgodranks', [player])

    def get_match_history(self, player):
        """
        :param player: The player name or player ID
        :return: Returns the recent matches and high level match statistics for a particular player.
        """
        return self.make_request('getmatchhistory', [str(player)])

    def get_queue_stats(self, player, queue):
        """
        :param player: The player name or player ID
        :param queue: The id of the game mode
        :return: Returns match summary statistics for a player and queue
        """
        return self.make_request('getqueuestats', [str(player), str(queue)])
