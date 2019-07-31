#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os.path
import json
import random
import requests


class cmd_parser():

    def __init__(self, _path = os.path.dirname(__file__)+'/base.json'):

        self.path = _path
        f = open(self.path, 'r')
        self.data = json.loads(f.read())
        f.close()

        self.activate = True

        self.talk = False

    def is_pose(self, text):
        for x in self.data["pose"]["cmd"]:
            if text.find(x) != -1:
                return True
        return False

    def get_pose(self,text):
        for x in self.data["pose"]["names"]:
            for y in x["name"]:
                if text.find(y) != -1:
                    return {"answer": random.choice(x["answer"]), "pose": x["pose"]}
        return None

    def is_stop(self, text):
        for x in self.data["stop"]:
            if text.find(x) != -1:
                return True
        return False

    def is_activate(self,text):
        for x in self.data["robot_name"]:
            if text.find(x) != -1:
                return True
        return False

    def is_talk_on(self,text):
        for x in self.data["talk"]["activate"]:
            if text.find(x) != -1:
                return True
        return False

    def is_talk_off(self,text):
        for x in self.data["talk"]["diactivate"]:
            if text.find(x) != -1:
                return True
        return False

    def rand_answer_not_understand(self, key):
        return random.choice(self.data['not_understand'])

    def bot_talk(self,text):

        payload = {
            "Referer": "https://xu.su/%D0%92%D0%BB%D0%B0%D0%B4%D0%B8%D0%BA"
                  }
        # Adding empty header as parameters are being sent in payload

        r = requests.post("https://xu.su/api/send", data={"bot": "old", "text": text}, headers=payload)
        respText = json.loads(r.text[:300])
        responce = respText['text']
        return {"answer": responce, "pose": None}

    def parser(self, text):

        # check activation word
        if self.is_activate(text):
            self.activate = True

            #enable / disable chat bot
            if self.is_talk_on(text):
                self.talk = True
                print("Start chat bot")
            if self.is_talk_off(text):
                self.talk = False
                print("Stop chat bot")
                return {"answer": random.choice(self.data["talk"]["answer"]), "pose":None}
        else:
            if self.activate:
                self.activate = False

        if self.talk:
            # return bot answer
            return  self.bot_talk(text)

        if not self.activate:
            return None

        # return position
        if self.is_pose(text):
            pose = self.get_pose(text)
            if pose:
                print(pose)
                return pose

        return {"answer":self.rand_answer_not_understand(), "pose":None}
