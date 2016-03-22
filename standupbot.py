import sys

import yaml
# import json
import os
import time

from slackclient import SlackClient


class Standup:
    def __init__(self, channel, slack_client):
        print("Standup Initialized")
        self.slack_client = slack_client
        self.channel = self.get_channel_info(channel)
        self.users = self.get_active_users()

        self.status = "INITIALIZED"

        # print(self.slack_client)

    def start_standup(self):
        # check to see if we're already started, if not, set status to STARTED.
        # If we're already doing a standup, throw out a message letting everyone know that something is happening.
        # go through list of users and set up DM channels, and keep track of them in the user.
        # fire off first round of questions.
        print("placeholder")

    def get_channel_info(self, channel_name):
        channel_object = self.slack_client.api_call("channels.info", channel=channel_name)
        return Channel(channel_object["channel"])

    def get_active_users(self):
        active_users = []
        for member in self.channel.members:
            status = self.slack_client.api_call("users.getPresence", user=member)

            # TODO: Only track if user is actually a user and not a bot.
            if status["presence"] is "active":
                user_object = self.slack_client.api_call("users.info", user=member)
                active_users.append(User(user_object["user"]))

        user_message = ""

        for user in active_users:
            user_message += "<@{}> ".format(user.id)

        self.broadcast_message(message="I'm currently tracking the following users: \n {}".format(user_message))

        return active_users

    def broadcast_message(self, message):
        self.slack_client.rtm_send_message(self.channel.id, message)


class Channel:
    def __init__(self, channel_info):
        self.id = channel_info["id"]
        self.name = channel_info["name"]
        self.members = channel_info["members"]
        print("Channel Initialized, ID: {} Name: {} Members: {}".format(self.id, self.name, self.members))


class User:
    def __init__(self, user_object):
        self.id = user_object["id"]
        self.name = user_object["name"]
        self.user_responses = {}


class StandupBot:
    def __init__(self, token):
        self.token = token
        self.slack_client = None
        self.standup = None
        self.last_ping = 0
        self.keepalive_timer = 3
        print("Standup Bot initialized.")

    def connect(self):
        self.slack_client = SlackClient(self.token)
        self.slack_client.rtm_connect()

    def keepalive(self):
        now = int(time.time())
        if now > self.last_ping + self.keepalive_timer:
            self.slack_client.server.ping()
            self.last_ping = now

    def start(self):
        self.connect()

        while True:
            for response in self.slack_client.rtm_read():
                self.response_handler(response)

            self.keepalive()
            time.sleep(.5)

    def message_handler(self, channel, message):
        if "!standup" in message:
            # check to see if self.Standup is already initialized, and if so, if the standup is already started.
            if self.standup is None:
                self.slack_client.rtm_send_message(channel=channel, message="Hello <!channel>, it's time for Standup!")
                self.standup = Standup(channel, self.slack_client)
            elif self.standup is not None & self.standup.status is "INITIALIZED":
                self.slack_client.rtm_send_message([channel, "I will restart the meeting."])
                self.standup = Standup(channel, self.slack_client)
        elif "!start" in message:
            if self.standup is not None:
                self.standup.start_standup()

    def response_handler(self, response):
        print(response)
        if "type" in response and "subtype" not in response:
            if "message" in response["type"]:
                self.message_handler(channel=response["channel"], message=response["text"])


def main_loop():
    try:
        bot.start()
    except KeyboardInterrupt:
        sys.exit(0)


# Startup

directory = os.path.dirname(sys.argv[0])

if not directory.startswith('/'):
    directory = os.path.abspath("{}/{}".format(os.getcwd(), directory))

config = yaml.load(open('standupbot.conf', 'r'))

bot = StandupBot(config["SLACK_TOKEN"])

main_loop()
