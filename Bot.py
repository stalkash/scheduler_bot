#coding=utf-8

import VK_LIB
import Scheduler
import time
import phrazes
import datetime
import pickle
import schedule
import settings
import traceback

import random

from importlib import reload
from schedule import WEEKDAYS
from schedule import GROUPS_NUMBERS
from schedule import GROUP_NAMES
from schedule import GROUP_NAMES_NUMBERS
from schedule import TIMES_OF_LESSONS
from schedule import WEEKDAY_RU_DICT
from schedule import WEEKDAYS_RU
from schedule import WEEKDAYS_RU_FOR_ADDED_TITLE
from schedule import GROUPS_FROM_SECOND_SHIFT

from schedule import PI_ISIT_175_1

from settings import *


class Bot_Scheduler:
    def __init__(self, vk_api, last_message_id, scheduler, users=False):
        self.vk_api = vk_api
        self.last_message_id = last_message_id
        self.scheduler = scheduler
        self.is_notifyied = False
        if not users:
            users = {}
        self.users = users
        self.users[ADMIN_ID][GROUP] = PI_ISIT_175_1
        self.vk_api.api_sendMessage(user_id=ADMIN_ID, message="Включаемся!")

    def main_loop(self):
        while True:
            data = self.vk_api.get_conversations("unread", self.last_message_id)

            for item in data["response"]["items"]:

                message_t = item["last_message"]
                user_id = message_t['from_id']
                message_id = message_t['id']
                message = message_t['text'].strip()
                self.last_message_id = message_id

                if DEBUG:
                    print(str.format(phrazes.message,
                                 message,
                                 message_id,
                                 user_id,
                                 time.strftime("%H %M %S")))


                self.vk_api.api_markAsRead(user_id, message_id)
                self.vk_api.set_activity(user_id)

                message = message.lower()
                
                if user_id == ADMIN_ID:
                    if message in ADM_COMMANDS:
                        self.handle_admin_commands(message)
                        continue

                complete = False
                for text in NEED_HELP:
                    if text in message:
                        message = str.format(
                            phrazes.message_help_template,
                            user_id,
                            message,
                            self.users[user_id][GROUP],
                            self.users[user_id][SUB_GROUP])
                        self.vk_api.api_sendMessage(
                            ADMIN_ID, message=message)
                        self.vk_api.api_sendMessage(
                            user_id, message=phrazes.message_help_reply)
                        complete = True
                        break

                if complete:
                    continue
                if "помощь" in message:
                    self.vk_api.api_sendMessage(
                        user_id, message=phrazes.help_message)
                    continue
                if user_id not in self.users:
                    self.register_user(user_id)
                    continue
                if not self.users[user_id][GROUP]:
                    response = self.register_user_group(user_id, message)
                    continue
                if "забыть" in message or "забудь" in message:
                    responce = self.send_sticker(user_id)
                    if response:
                        self.vk_api.api_sendMessage(
                            user_id=user_id, message=response)
                    continue
                elif not self.users[user_id][SUB_GROUP]:
                    response = self.register_user_subgroup(
                        user_id, message)
                    if response:
                        group_name = self.users[user_id][GROUP]
                        subgroup_number = GROUPS_NUMBERS[self.users[user_id][SUB_GROUP]]

                        if self.users[user_id][GROUP] in schedule.GROUPS_WITH_THREE_SUBGROUPS:
                            # cause their subgroups numbers
                            # are 2 and 3, not just 1 and 2.
                            subgroup_number += 1
                        message = str.format(
                            phrazes.register_sumbit,
                            group_name,
                            subgroup_number)
                        self.vk_api.api_sendMessage(
                            user_id, message=message)
                        self.vk_api.api_sendMessage(
                            user_id, message=phrazes.help_message)
                    continue
                
                elif "время" in message:
                    response = self.get_time()
                    if response:
                        self.vk_api.api_sendMessage(
                            user_id=user_id, message=response)
                    continue
                elif "какая" in message:
                    response = self.get_week(message)
                    if response:
                        self.vk_api.api_sendMessage(user_id=user_id,
                                                    message=response)
                    continue
                elif "покажи группы" in message or "группы" in message:
                    response = str.format(
                        phrazes.show_groups, self.get_groups())
                    self.vk_api.api_sendMessage(
                        user_id=user_id, message=response)
                    continue
                elif "расписание" in message:
                    response = self.get_schedule_other_group(
                        user_id, message)
                    if response:
                        self.vk_api.api_sendMessage(
                            user_id=user_id, message=response)
                        continue
                    self.error(user_id)
                    continue
                elif "уведомлени" in message:
                    self.notify_change(user_id)
                    continue
                elif "моя группа" in message or "групп" in message:
                    self.show_the_group(user_id, message)
                    continue

                elif "найди" in message:
                    responce = self.get_schedule_teacher(user_id, message)
                    if(responce):
                        self.vk_api.api_sendMessage(user_id=user_id, message=responce)
                    else:
                        self.error(user_id)
                    continue

                responce = self.get_schedule(user_id, message)
                if responce:
                    self.vk_api.api_sendMessage(
                        user_id, message=responce)

                else:
                    self.error(user_id)
                    continue

    def send_sticker(self, user_id):
        sticker_id = random.choice(STICKER_IDS)
        self.vk_api.api_sendMessage(user_id, "", sticker_id)

    def register_user(self, user_id):
        self.users[user_id] = {}
        self.users[user_id][GROUP] = False
        self.users[user_id][SUB_GROUP] = False
        self.users[user_id][NOTIFY] = False
        self.send_sticker(user_id)
        self.vk_api.api_sendMessage(user_id, message=phrazes.greeting)
        message = phrazes.register_group
        message += self.get_groups()
        message += phrazes.register_group_add
        self.vk_api.api_sendMessage(
            user_id, message=message)

    def register_user_group(self, user_id, message):
        message = message.upper()
        if DEBUG:
            print(message)
            print(schedule.GROUP_NAMES_NUMBERS)
            print(message in schedule.GROUP_NAMES_NUMBERS)
        group_name = self.get_group_name(message)
        if not group_name:
            message = phrazes.register_group
            message += self.get_groups()
            message += phrazes.register_group_add
            self.vk_api.api_sendMessage(
                user_id, message=message)
            return False
        if DEBUG:
            print(message)
        self.users[user_id][GROUP] = group_name
        if(group_name in schedule.GROUPS_WITHOUT_SUBGROUPS):
            self.users[user_id][SUB_GROUP] = Scheduler.schedule.NO_GROUP
            message = str.format(phrazes.register_submit_only_group, group_name)
            self.vk_api.api_sendMessage(user_id, message)
            self.vk_api.api_sendMessage(
                                user_id, message=phrazes.help_message)
            return True   #Do nothing if group has no subgroups
        if self.users[user_id][GROUP] in schedule.GROUPS_WITH_THREE_SUBGROUPS:
            message = phrazes.register_sub_group_three
            self.vk_api.api_sendMessage(
            user_id, message=message)
        message = str.format(phrazes.register_sub_group)
        self.vk_api.api_sendMessage(user_id, message)
        return True

    def register_user_subgroup(self, user_id, message):
        subgroups = ["1", "2"]
        if self.users[user_id][GROUP] in schedule.GROUPS_WITH_THREE_SUBGROUPS:
            subgroups = ["2", "3"]
        if(self.users[user_id][GROUP] in schedule.GROUPS_WITHOUT_SUBGROUPS):
            self.users[user_id][SUB_GROUP] = Scheduler.schedule.NO_GROUP
            return True
        if not message.isdigit() or message not in subgroups:
            message = str.format(phrazes.register_sub_group,
                                 subgroups[0], subgroups[1], subgroups[0])
            if DEBUG:
                print(message)
                print(subgroups)
            self.vk_api.api_sendMessage(
                user_id, message=message)
            return False
        if message == subgroups[0]:
            self.users[user_id][SUB_GROUP] = Scheduler.schedule.FIRST_GROUP
        elif message == subgroups[1]:
            self.users[user_id][SUB_GROUP] = Scheduler.schedule.SECOND_GROUP
        return True

    def show_the_group(self, user_id, message):
        group_name = self.users[user_id][GROUP]
        subgroup_number = GROUPS_NUMBERS[self.users[user_id][SUB_GROUP]]

        if group_name in schedule.GROUPS_WITH_THREE_SUBGROUPS:
            # cause their subgroups numbers
            # are 2 and 3, not just 1 and 2.
            subgroup_number += 1
        message = str.format(phrazes.show_group, group_name, subgroup_number)
        self.vk_api.api_sendMessage(user_id=user_id, message=message)

    def get_groups(self):
        message = ""
        for i, group in enumerate(schedule.GROUP_NAMES):  # TODO GROUP
            message += str(i + 1) + ") " + group + "\n"
            if((i + 1) % 5 == 0):
                message += "-------\n"
        return message

    def forget_group(self, user_id, message):
        if "подгруппа" in message or "подгруппу" in message:
            self.users[user_id][SUB_GROUP] = False
            message = phrazes.register_sub_group
            if self.users[user_id][GROUP] in schedule.GROUPS_WITH_THREE_SUBGROUPS:
                message = phrazes.register_sub_group_three
            self.vk_api.api_sendMessage(user_id, message=message)
        elif "группа" in message or "группу" in message:
            self.users[user_id][GROUP] = False
            self.users[user_id][SUB_GROUP] = False
            self.vk_api.api_sendMessage(user_id, message=phrazes.forget_group)
            message = phrazes.register_group
            message += self.get_groups()
            message += phrazes.register_group_add
            self.vk_api.api_sendMessage(user_id, message=message)

        else:
            self.error(user_id)

    def get_week(self, message=False):
        next_week = False
        if message and "след" in message:
            next_week = True

        week = self.scheduler.get_alldennum()
        if week == schedule.NUMERATOR:
            if not next_week:
                return phrazes.schedule_numerator
            else:
                return phrazes.schedule_denumerator_next_week
        elif week == schedule.DENUMERATOR:
            if not next_week:
                return phrazes.schedule_denumerator
            else:
                return phrazes.schedule_numerator_next_week

    def get_time(self):
        response = "Время пар:\n"
        for i, lesson in enumerate(schedule.TIMES_OF_LESSONS):
            response += str.format(phrazes.get_time, i + 1, lesson)
        return response

    def get_group_name(self, group_name):
        if group_name.isdigit():
            group_number = int(group_name) - 1 # cause user enters numbers from 1 to N, so we need to decrease to use it like index
            if group_number < len(GROUP_NAMES):
                return GROUP_NAMES[group_number]
            return False
        group_names = [x.upper() for x in GROUP_NAMES]
        group_name = group_name.upper()
        if group_name in group_names:
            return GROUP_NAMES[group_names.index(group_name)]
        if group_name in schedule.HIDDEN_GROUP_NAMES:
            return group_name
        return False

    def get_schedule_teacher(self, user_id, message):
        teacher_name = message.split()[1][:-1].lower()
        if teacher_name not in GROUP_NAMES:
            return False
        return self.get_schedule(user_id, message, teacher_name, "first_group")

    def get_schedule_other_group(self, user_id, message):
        message = message.split()
        if(len(message) == 1):
            return phrazes.get_schedule_help
        if(len(message) < 2):
            return False
        if DEBUG:
            print(message)
        if(len(message) >= 3):
            group_name = " ".join([message[1], message[2]]).upper()
            found = False
            name = self.get_group_name(group_name)
            if DEBUG:
                print(name)
            if name:
                found = True
                group_name = name
            if found:
                temp = [message[0], group_name]
                temp.extend(message[3:])
                message = temp
                if DEBUG:
                    print(group_name)
                    print(message)
        if((message[1] in GROUP_NAMES or message[1] in GROUP_NAMES_NUMBERS)):
            query = "пары"
            group_name = self.get_group_name(message[1])
            if(len(message) > 2 and message[2].isdigit()):
                sub_group = message[2]
                if int(sub_group) not in (1, 2):
                    return phrazes.error_get_schedule_other_group_SUB_GROUP
                if(len(message) > 3):
                    query = " ".join(message[3:])
            else:
                sub_group = False
                if(len(message) > 2):
                    query = " ".join(message[2:])

            if(not sub_group):
                schedule1 = self.get_schedule(
                    user_id, query,
                    group_name=group_name,
                    sub_group=schedule.FIRST_GROUP,
                    hide_empty_pairs=True)
                schedule2 = self.get_schedule(
                    user_id, query,
                    group_name=group_name,
                    sub_group=schedule.SECOND_GROUP,
                    hide_empty_pairs=True)

                response = "{0}\n\nПодгруппа 1:\n{1}{3}Подгруппа 2:\n{2}"

                response = str.format(
                    response,
                    group_name,
                    schedule1,
                    schedule2,
                    phrazes.split_line)
            else:
                response = self.get_schedule(
                    user_id,
                    query,
                    group_name=group_name,
                    sub_group=schedule.SUBGROUP_NUMBERS[sub_group])
                response = str.format(
                    "{0}, подгруппа {1}\n{2}", group_name, sub_group, response)
            return response
        else:
            return phrazes.error_get_schedule_other_group_GROUP

    def get_schedule(self, user_id, message,
                     group_name=False,
                     sub_group=False,
                     hide_empty_pairs=False):

        message = message.lower()
        if DEBUG:
            print(message)

        if(not group_name and not sub_group):
            group_name = self.users[user_id][GROUP]
            sub_group = self.users[user_id][SUB_GROUP]
            if group_name in GROUPS_FROM_SECOND_SHIFT:
                hide_empty_pairs = True
        if DEBUG:
            print(message)
            print(sub_group)

        message = message.replace("?", "")
        message = message.replace(".", "")
        message = message.split()
        date = datetime.date.today()

        found = False
        all_week = False
        add_to_title = False

        if "неделя" in message or "неделю" in message:
            found = True
            all_week = True
            if DEBUG:
                print(message, all_week)

        next_week = False
        if "следующую" in message or "следующий" in message or "следующая" in message:
            date = date + datetime.timedelta(7)
            next_week = True
        elif "сегодня" in message:
            found = True
            add_to_title = "сегодня"
        elif "завтра" in message:
            date = date + datetime.timedelta(1)
            found = True
            add_to_title = "завтра"
        elif "послезавтра" in message:
            date = date + datetime.timedelta(2)
            found = True
            add_to_title = "послезавтра"
        weekday = WEEKDAYS[date.weekday()]
        if DEBUG:
            print(date)
        if not found:  # TODO убрать в функцию, упростить
            for weekday_t in WEEKDAY_RU_DICT:
                if found:
                    break
                for m_t in message:
                    m_t = m_t.strip()
                    if m_t in WEEKDAY_RU_DICT[weekday_t]:
                        if weekday_t != date.weekday():
                            while date.weekday() != weekday_t:
                                if not next_week:
                                    date = date + datetime.timedelta(1)
                                else:
                                    date = date - datetime.timedelta(1)
                            if next_week:
                                date += datetime.timedelta(7)
                        weekday = WEEKDAYS[weekday_t]
                        found = True
                        break

        # command "пары"
        if len(message) == 1 and "пар" in message[0]:
            found = True
            if int(time.strftime("%H")) > 13:
                date += datetime.timedelta(1)
        if date.weekday() == 6:  # if today's day is Sunday, then return schedule for Monday
            date += datetime.timedelta(1)
        weekday = WEEKDAYS[date.weekday()]

        # command "пары"
        if(date == datetime.date.today()):
            add_to_title = "сегодня"
        if(date == (datetime.date.today() + datetime.timedelta(1))):
            add_to_title = "завтра"

        if "найди" in message:
            found = True

        if not found:
                return False

        alldennum = self.scheduler.get_alldennum(date)
        if DEBUG:
            print(weekday)
        schedule = self.scheduler.get_schedule(
            group_name,
            sub_group,
            weekday,
            all_week=all_week,
            alldennum=alldennum)

        if not all_week:
            return self.proccess_schedule(schedule,
                                          date,
                                          add_to_title=add_to_title,
                                          hide_empty_pairs=hide_empty_pairs)
        else:
            if DEBUG:
                print(date)
            while(date.weekday() != 0):
                date = date - datetime.timedelta(1)
            if DEBUG:
                print(date)
            response = ""

            for j in range(len(schedule)):
                if DEBUG:
                    print(j)
                    print(schedule[j])
                if(j < 6):
                    item = self.proccess_schedule(
                        schedule[j],
                        date + datetime.timedelta(j),
                        hide_empty_pairs=all_week)
                    response += phrazes.split_line + item.lstrip("\n")
            if DEBUG:
                print(response)
            return response

    def proccess_schedule(self, schedule, date, hide_empty_pairs=False, add_to_title=False):
        date_s = str.format("{0}.{1}", str(date.day), str(date.month))

        weekday_ru = WEEKDAYS_RU[date.weekday()]
        if add_to_title:
            weekday_ru = WEEKDAYS_RU_FOR_ADDED_TITLE[date.weekday()]
            response = str.format(
                phrazes.schedule_title_long, add_to_title, weekday_ru, date_s)
        else:
            response = str.format(phrazes.schedule_title, weekday_ru, date_s)
        for i, lesson in list(enumerate(schedule)):
            if DEBUG:
                print(lesson)
            if lesson:
                lesson_template = phrazes.schedule_item
                if DEBUG:
                    print("lesson is", lesson)
                if not lesson[1]:
                    lesson[1] = ""
                    lesson_template = phrazes.schedule_item_no_teacher

                item = str.format(lesson_template, i + 1,
                                lesson[0],
                                lesson[1],
                                lesson[2],
                                TIMES_OF_LESSONS[i])

                response += item
            else:
                if not hide_empty_pairs:
                    if(i < 4):  # check if it isn't a fifth lesson
                        item = str.format(phrazes.schedule_no_lesson,
                                      i + 1, "Нет пары", TIMES_OF_LESSONS[i])
                        response += item
        return response

    def notify(self):
        print("Начинаем уведомлять...")
        print(time.strftime("%H %M %S"))
        count = 0
        for user_id in self.users:
            if self.users[user_id][NOTIFY]:
                message = "пары сегодня"
                response = self.get_schedule(user_id, message)
                self.vk_api.api_sendMessage(user_id, message=response)
                count += 1
                time.sleep(0.4)
        self.is_notifyied = True
        print("Уведомлений отправлено %s", count)

    def notify_change(self, user_id):
        if True:  # TODO fix notifying
            self.users[user_id][NOTIFY] = not self.users[user_id][NOTIFY]
            message = phrazes.notify_on if self.users[user_id][NOTIFY] else phrazes.notify_off
            self.vk_api.api_sendMessage(user_id, message)
        else:
            self.vk_api.api_sendMessage(user_id, phrazes.notify_broken)

# ########################SYS#################################
    def handle_admin_commands(self, message):
        if "off" in message:
            self.off()
        elif "save" in message:
            self.save()
        elif "reload" in message:
            self.reload_modules()
        return

    def save(self):
        print("Сохраняю last_message_id...")
        f = open("last_message_id.txt", mode="w")
        f.write(str(self.last_message_id))
        f.close()
        print("Сохранено!")

        print("Сохраняю users...")
        f = open("users.dat", mode="wb")
        pickle.dump(self.users, f)
        f.close()
        print("Сохранено!")

        if DEBUG:
            self.vk_api.api_sendMessage(
                user_id=ADMIN_ID, message="Сохранение выполнено успешно!")

    def off(self):
        self.save()
        print("Выключаюсь...")
        self.vk_api.api_sendMessage(user_id=ADMIN_ID, message="Выключаюсь...")
        exit()

    def reload_modules(self):
        reload(phrazes)
        # reload(schedule)
        self.vk_api.api_sendMessage(
            user_id=ADMIN_ID, message="Модули перезагружены!")

    def error(self, user_id, message=""):
        self.vk_api.api_sendMessage(
            user_id, message=phrazes.error_message)


def load():
    last_message_id = 0
    users = {}
    try:
        print("Загрузжаю last_message_id.txt...")
        f = open('last_message_id.txt')
        last_message_id = int(f.read())
        print(str.format("last_message_id = {0}", last_message_id))
        f.close()
        print("Готово!")
    except Exception:
        print("файл last_message_id.txt не найден")
    try:
        print("Загрузжаю users.dat...")
        f = open("users.dat", mode="rb")
        users = pickle.load(f)
        f.close()
        print("Готово!")
    except Exception:
        print("файл users.dat не найден")
    try:
        print("Загрузжаю schedule.dat...")
        f = open("schedule.dat", mode="rb")
        schedule = pickle.load(f)
        f.close()
        print("Готово!")
    except Exception:
        print("файл schedule.dat не найден")
    return last_message_id, users, schedule


def main():
    last_message_id, users, schedule = load()
    VK_API = VK_LIB.VK_API(ACCESS_TOKEN)
    scheduler = Scheduler.Scheduler(schedule)
    bot = Bot_Scheduler(VK_API, last_message_id, scheduler, users=users)
    bot.main_loop()


if __name__ == '__main__':
    main()
