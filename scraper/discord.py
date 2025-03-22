import requests

class DiscordApi:
    def __init__(self, token):
        self.token = token

        self.username = None
        self.id = None
        self.email = None
        self.phone = None

        self.HEADERS = {"authorization": self.token, "content-type": "application/json"}
        self._validate()

    def _validate(self) -> None:
        """This will check if the discord token works"""
        url = f"https://discord.com/api/users/@me"
        r = requests.get(url, headers=self.HEADERS)
        if r.status_code == 200:
            print(f"Valid token: {self.token}" )
            data = r.json()
            self.username = data['username'] + "#" + data['discriminator']
            self.id = data['id']
            self.email = data['email']
            self.phone = data['phone']
        else:
            print(f"Invalid token: {self.token}")
            exit()

    def get_messages(self, channel_id: str, page: int = 0) -> list:
        """It will get 25 messages from a channel"""
        offset = 25 * page
        url = f"https://discord.com/api/channels/{channel_id}/messages" #/search?offset={offset}"
        r = requests.get(url, headers=self.HEADERS)
        if r.status_code in [200, 201, 204]:
            return r.json()
        else:
            return []