#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Библиотеки распознавания и синтеза речи
import speech_recognition as sr

# Воспроизведение речи

from urllib2 import urlopen
import urllib

import os
import time
import datetime
import webbrowser
import subprocess
from robot_base import cmd_parser

import rospy
import tf
from geometry_msgs.msg import PoseStamped
from actionlib_msgs.msg import GoalID

import pygame
from pygame import mixer
mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)


import sys
reload(sys)
sys.setdefaultencoding('utf-8')


goal_topic = "move_base_simple/goal"

def set_pos(data):
    global goal_pub
    goal = PoseStamped()
    goal.header.stamp = rospy.Time.now()
    goal.header.frame_id = "map"
    goal.pose.position.x = data['x']
    goal.pose.position.y = data['y']
    goal.pose.position.z = data['z']

    quaternion = tf.transformations.quaternion_from_euler(0.0, 0.0, data['phi'])
    goal.pose.orientation.x = quaternion[0]
    goal.pose.orientation.y = quaternion[1]
    goal.pose.orientation.z = quaternion[2]
    goal.pose.orientation.w = quaternion[3]
    print("send goal:", goal)
    goal_pub.publish(goal)

def stop_cmd():
    global goal_cancel

    goalId = GoalID()
    goal_cancel.publish(goalId)
    print("Stop goal")

class Speech_AI:

    def __init__(self):
        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone()


        now_time = datetime.datetime.now()
        self._wav_name = now_time.strftime("%d%m%Y%I%M%S") + ".wav"
        self._mp3_nameold='111'

        self.robot_parser = cmd_parser()



    def work(self):
        print("Минутку тишины, пожалуйста...")
        with self._microphone as source:
            self._recognizer.adjust_for_ambient_noise(source)

        print("Скажи что - нибудь!")
        with self._microphone as source:
            audio = self._recognizer.listen(source)
        print("Понял, идет распознавание...")

        try:
            statement = self._recognizer.recognize_google(audio, language="ru_RU")
            statement= statement.lower().encode('utf-8')
            print(statement)

            # get answer
            # останавливаемся
            if self.robot_parser.is_stop(statement):
                stop_cmd()
            else:
                answer = self.robot_parser.parser(statement)
                if answer != None:
                    self.say(answer['answer'].encode('utf-8'))
                    print(answer['answer'])

                    # send position
                    if answer['pose'] != None:
                        set_pos(answer['pose'])
                        print(answer['pose'])





            # Поддержание диалога
            if((statement.find("до свидания")!=-1) or (statement.find("досвидания")!=-1)):
                answer = "Пока!"
                self.say(str(answer))
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                sys.exit()

            print("Вы сказали: {}".format(statement))

        except sr.UnknownValueError:
            print("Упс! Кажется, я тебя не поняла, повтори еще раз")
        except sr.RequestError as e:
            print("Не могу получить данные от сервиса Google Speech Recognition; {0}".format(e))
        except KeyboardInterrupt:
            self._clean_up()
            print("Пока!")


    def generate_voice(self, text, audio_format='wav', speaker='ermil', key='b71d9cc3-e3b6-45f5-88b4-9db44cf8b2af', file_name='voice.wav'):
        """
        key = b71d9cc3-e3b6-45f5-88b4-9db44cf8b2af;
        text=<текст для генерации> - "гот%2bов"
        format=<формат аудио файла> - "mp3", "wav"
        lang=<язык> - "ru‑RU"
        speaker=<голос> - female: jane, omazh; male: zahar, ermil
        key=<API‑ключ>

        [emotion=<окраска голоса>] - neutral(нейтральный), evil (злой), , good - радостный
        [drunk=<окраска голоса>] - true, false
        [ill=<окраска голоса>] - true, false
        [robot=<окраска голоса>] - true, false
        """

        url = 'https://tts.voicetech.yandex.net/generate?' \
              'text={text}&' \
              'format={audio_format}&' \
              'lang=ru-RU&' \
              'speaker={speaker}&' \
              'key={key}&' \
              'emotion=evil&' \
              'drunk=false&' \
              'ill=false&' \
              'robot=true&' \
              'speed=1.0&'
        text = urllib.quote(text)

        url = url.format(
            text=text,
            audio_format=audio_format,
            speaker=speaker,
            key=key
        )

        try:
            download_content = urlopen(url).read()
            f = open(file_name, 'wb')
            f.write(download_content)
            f.close()
        except:
            print('Что-то не то с распознованием!')
        #     return False
        # return file

    def osrun(self, cmd):
        PIPE = subprocess.PIPE
        p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=subprocess.STDOUT)

    def openurl(self, url, ans):
        webbrowser.open(url)
        self.say(str(ans))
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    def say(self, phrase):
        # tts = gTTS(text=phrase, lang="ru")
        # tts.save(self._mp3_name)

        self.generate_voice(phrase, file_name=self._wav_name)


        # Play answer
        mixer.music.load(self._wav_name)
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(1.0)

        if(os.path.exists(self._wav_name)):
            os.remove(self._wav_name)

        now_time = datetime.datetime.now()
        self._wav_name = now_time.strftime("%d%m%Y%I%M%S") + ".wav"

    def other_answer(self, statement):
        # Команды для открытия различных внешних приложений

        if ((statement.find("калькулятор") != -1) or (statement.find("calculator") != -1)):
            self.osrun('calc')

        if ((statement.find("блокнот") != -1) or (statement.find("notepad") != -1)):
            self.osrun('gedit')

        if ((statement.find("paint") != -1) or (statement.find("паинт") != -1)):
            self.osrun('mspaint')

        if ((statement.find("google") != -1) or (statement.find("гугл") != -1)):
            self.openurl('http://google.ru', 'Открываю браузер')

        # Команды для открытия URL в браузере

        if (((statement.find("youtube") != -1) or (statement.find("youtub") != -1) or (
                statement.find("ютуб") != -1) or (statement.find("you tube") != -1)) and (
                statement.find("смотреть") == -1)):
            self.openurl('http://youtube.com', 'Открываю ютуб')

        if (((statement.find("новости") != -1) or (statement.find("новость") != -1) or (
                statement.find("на усть") != -1)) and (
                (statement.find("youtube") == -1) and (statement.find("youtub") != -1) and (
                statement.find("ютуб") == -1) and (statement.find("you tube") == -1))):
            self.openurl('https://www.youtube.com/user/rtrussian/videos', 'Открываю новости')

        if ((statement.find("mail") != -1) or (statement.find("майл") != -1)):
            self.openurl('https://e.mail.ru/messages/inbox/', 'Открываю почту')

        if ((statement.find("вконтакте") != -1) or (statement.find("в контакте") != -1)):
            self.openurl('http://vk.com', 'Открываю Вконтакте')

        # Команды для поиска в сети интернет

        if ((statement.find("найти") != -1) or (statement.find("поиск") != -1) or (statement.find("найди") != -1) or (
                statement.find("дайте") != -1) or (statement.find("mighty") != -1)):
            statement = statement.replace('найди', '')
            statement = statement.replace('найти', '')
            statement = statement.strip()
            self.openurl('https://yandex.ru/yandsearch?text=' + statement, "Я нашла следующие результаты")

        if ((statement.find("смотреть") != -1) and ((statement.find("фильм") != -1) or (statement.find("film") != -1))):
            statement = statement.replace('посмотреть', '')
            statement = statement.replace('смотреть', '')
            statement = statement.replace('хочу', '')
            statement = statement.replace('фильм', '')
            statement = statement.replace('film', '')
            statement = statement.strip()
            self.openurl('https://yandex.ru/yandsearch?text=Смотреть+онлайн+фильм+' + statement,
                         "Выберите сайт где смотреть фильм")

        if (((statement.find("youtube") != -1) or (statement.find("ютуб") != -1) or (
                statement.find("you tube") != -1)) and (statement.find("смотреть") != -1)):
            statement = statement.replace('хочу', '')
            statement = statement.replace('на ютубе', '')
            statement = statement.replace('на ютуб', '')
            statement = statement.replace('на youtube', '')
            statement = statement.replace('на you tube', '')
            statement = statement.replace('на youtub', '')
            statement = statement.replace('youtube', '')
            statement = statement.replace('ютуб', '')
            statement = statement.replace('ютубе', '')
            statement = statement.replace('посмотреть', '')
            statement = statement.replace('смотреть', '')
            statement = statement.strip()
            self.openurl('http://www.youtube.com/results?search_query=' + statement, 'Ищу в ютуб')

        if ((statement.find("слушать") != -1) and (statement.find("песн") != -1)):
            statement = statement.replace('песню', '')
            statement = statement.replace('песни', '')
            statement = statement.replace('песня', '')
            statement = statement.replace('песней', '')
            statement = statement.replace('послушать', '')
            statement = statement.replace('слушать', '')
            statement = statement.replace('хочу', '')
            statement = statement.strip()
            self.openurl('https://my.mail.ru/music/search/' + statement, "Нажмите плэй")

    def _clean_up(self):
        def clean_up():
            os.remove(self._wav_name)




if __name__ == "__main__":

    # init ros node
    rospy.init_node('ai_control_node', anonymous=True)
    rate = rospy.Rate(50)  # 10hz
    ai = Speech_AI()

    # start subscriber
    # rospy.Subscriber(vel_topic, TwistStamped, vel_clb)
    # rospy.Subscriber(goal_topic, PoseStamped, goal_clb)
    # rospy.Subscriber(pose_topic, PoseStamped, current_pose_clb)
    goal_pub = rospy.Publisher(goal_topic, PoseStamped, queue_size=10)
    goal_cancel = rospy.Publisher('move_base/cancel', GoalID, queue_size=10)

    try:
        while not rospy.is_shutdown():
            ai.work()
            rate.sleep()

    except KeyboardInterrupt:   # if put ctr+c
        exit(0)
