# -*- coding: utf-8 -*

import requests
import json

VK_VERSION = "5.85"
VK_API_ENDPOINT = "https://api.vk.com/method/"
TIME_OFFSET = 30


class VK_API:
    def __init__(self, token):
        self.token = token

    def api_call(self, method, **options):
        options["access_token"] = self.token
        options["v"] = VK_VERSION
        url = VK_API_ENDPOINT + method + "?"
        response = requests.post(url, data=options)
        data = json.loads(response.text)
        return data

    def api_sendMessage(self, user_id, message, sticker_id=-1, **options):
        if message != "":
            return self.api_call("messages.send", user_id=user_id, message=message, options=options)
        else:
            return self.api_call("messages.send", user_id=user_id, sticker_id=sticker_id, options=options)

    def api_markAsRead(self, user_id, start_message_id, **options):
        return self.api_call("messages.markAsRead", user_id=user_id, start_message_id=start_message_id, options=options)

    def api_getDialogs(self, count=200, offset=0, **options):
        return self.api_call("messages.getDialogs", count=count, offset=offset, options=options)

    def api_get(self, last_message_id, time_offset=0, **options):
        options["filter"] = 0
        return self.api_call("messages.get", last_message_id=last_message_id, time_offset=time_offset, options=options)

    def get_conversations(self, Filter:str, start_message_id: int, **options): 
        return self.api_call("messages.getConversations", filter=Filter, start_message_id=start_message_id, options=options)

    def get_conversations_ByID(self):
        return self.api_call("messages.getConversationsByID", peer_ids=2000000100)

    def get_by_id(self):
        return self.api_call("messages.getById", message_ids=1086583)

    def set_activity(self, user_id):
        return self.api_call("messages.setActivity", peer_id=user_id, type="typing")


def main():
    ACCESS_TOKEN = "//////"
    vk_bot = VK_API(ACCESS_TOKEN)
    print(vk_bot.get_conversations("unread", 3709, group_id = 80906674, fields="conversations, users", extended=1))


if __name__ == '__main__':
    main()
