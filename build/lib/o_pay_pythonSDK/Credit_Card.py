import requests
import os
import json


class Pterodactyl_Application:
    def __init__(self, base_url, api_key):
        if base_url[-1] == "/":
            base_url = base_url[:-1]
        self.base_url = base_url
        self.api_key = api_key

