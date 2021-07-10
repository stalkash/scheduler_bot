# -*- coding: utf-8 -*

import schedule
import datetime
from settings import DEBUG


class Scheduler:
    def __init__(self, schedule=schedule.schedule):
        self.schedule = schedule

    def get_schedule_day(self, group_name, sub_group, weekday, alldennum):
        print("group_name is", group_name);
        if group_name in self.schedule:
            list_of_classes = []
            for n_of_class in schedule.NUMBER_OF_CLASSES:
                list_of_classes.append(self.get_schedule_class(
                    group_name, sub_group, weekday, n_of_class, alldennum=alldennum))
            return list_of_classes
        return False

    def get_schedule_class(self, group_name, sub_group, weekday, n_of_class, alldennum):
        schedule_day = self.schedule.get(group_name).get(weekday)
        print("schedule day is ", schedule_day)
        schedule_t = False
        if schedule_day.get(n_of_class):
            if(DEBUG):
                print("subgroup is {0}", sub_group)
                print("if there schedule for second",
                      schedule_day[n_of_class].get(sub_group))

            if schedule_day[n_of_class].get(schedule.ALL_GROUP):
                if type(schedule_day[n_of_class][schedule.ALL_GROUP]) is dict:
                    schedule_t = schedule_day[n_of_class][schedule.ALL_GROUP].get(
                        alldennum)
                    print(schedule_day[n_of_class][schedule.ALL_GROUP].get(alldennum))
                else:
                    schedule_t = schedule_day[n_of_class][schedule.ALL_GROUP]

            if schedule_day[n_of_class].get(sub_group):
                if not schedule_t:
                    if type(schedule_day[n_of_class][sub_group]) is dict:
                        schedule_t = schedule_day[n_of_class][sub_group].get(
                            alldennum)
                    else:
                        schedule_t = schedule_day[n_of_class].get(sub_group)
        if(DEBUG):
            print("schedule_t is ", schedule_t)
        return schedule_t

    def get_schedule(self, group_name, sub_group, weekday=-1, n_of_class=False, all_week=False, alldennum=False):
        if not alldennum:
            alldennum = self.get_alldennum()
        if all_week:
            try:
                schedule_week = []
                for _weekday in schedule.WEEKDAYS:
                    classes = self.get_schedule_day(
                        group_name, sub_group, _weekday, alldennum)
                    schedule_week.append(classes)
                return schedule_week
            except Exception:
                print("error")
        if weekday != -1:
            return self.get_schedule_day(group_name, sub_group, weekday, alldennum=alldennum)

    def get_alldennum(self, date=False):
        if not date:
            date = datetime.date.today()
        number_of_week = date.isocalendar()[1]
        if number_of_week % 2 == 0:
            return schedule.DENUMERATOR
        return schedule.NUMERATOR


def main():
    scheduler = Scheduler(schedule.schedule)
    group_name = schedule.PI1752
    sub_group = schedule.FIRST_GROUP
    weekday = schedule.FRIDAY
    for class in scheduler.get_schedule(group_name, sub_group,
                                       weekday=weekday, alldennum=schedule.NUMERATOR):
        print(class)


if __name__ == '__main__':
    main()
