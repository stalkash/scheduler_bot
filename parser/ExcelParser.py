import pandas as pd
import time
import pprint
import pickle



DENUMERATOR = "denumerator"
NUMERATOR = "numerator" 
ALLDENNUM = "alldennum"

FIRST_GROUP = "first_group"
SECOND_GROUP = "second_group"

ALL_GROUP = "all_group"

MONDAY = "monday"
TUESDAY = "tuesday"
WEDNESDAY = "wednesday"
THURSDAY = "thursday"
FRIDAY = "friday"
SATURDAY = "saturday"
SUNDAY = "sunday"

WEEKDAYS = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY]

FIRST = "first"
SECOND = "second"
THIRD = "third"
FOURTH = "fourth"
FIFTH = "fifth"

LESSONS = [FIRST, SECOND, THIRD, FOURTH, FIFTH]

def combineTwoRows(first_row_dict, second_row_dict):
	time_dict = {
		FIRST_GROUP:
		{
			NUMERATOR: first_row_dict.get(FIRST_GROUP),
			DENUMERATOR: second_row_dict.get(FIRST_GROUP)
		},
		SECOND_GROUP:
		{
			NUMERATOR: first_row_dict.get(SECOND_GROUP),
			DENUMERATOR: second_row_dict.get(SECOND_GROUP)
		}
	}
	return time_dict

def parseOneTime(schedule, row_index):
	time_dict = {}

	item = str(schedule.iat[row_index, 2])
	if(item == "nan" or item.find("(") == -1):
		return {}

	lessonTeacher = item.rsplit(")", maxsplit=1)
	lesson = lessonTeacher[0].strip() + ")"
	teacher = lessonTeacher[1].strip()
	cab = schedule.iat[row_index, 3]
	if(str(cab) != "nan"):
		time_dict[FIRST_GROUP] = [lesson, teacher, cab]
		item = str(schedule.iat[row_index, 4])
		if(item != "nan"):
			lessonTeacher = item.split(")")
			lesson = lessonTeacher[0]
			teacher = lessonTeacher[1]
			cab = schedule.iat[row_index, 5]
			time_dict[SECOND_GROUP] = [lesson, teacher, cab]

		next_row_dict = parseOneTime(schedule, row_index+1)
		if(len(next_row_dict.keys()) > 0):
			time_dict = combineTwoRows(time_dict, next_row_dict)
			return time_dict
		return time_dict
	cab = schedule.iat[row_index, 5]
	time_dict[ALL_GROUP] = [lesson, teacher, cab]
	return time_dict


excel_info = [['imikn.xls', 2, 5], ["imikn2.xls", 0, 5]]

schedule_dict = {}
for excel_file in excel_info:

	excel_filename = excel_file[0]
	start_sheet = excel_file[1]
	end_sheet = excel_file[2]

	for sheet_number in range(start_sheet, end_sheet):
		schedule = pd.read_excel(excel_filename, sheet_name=sheet_number)

		group_row = 0
		while(not str(schedule.iat[group_row, 2]).startswith("Групп")):
			group_row += 1
		group_name = schedule.iat[group_row, 2]
		group_name = group_name.split('22')[1].strip()
		print("proccessing %s", group_name)

		monday_row = 0
		while(schedule.iat[monday_row, 0] != "Понедельник"):
			monday_row += 1

		print(schedule.iat[monday_row, 0])

		row_index = monday_row

		lesson_counter = 0;
		day_number = 0
		all_dict = {}
		day_dict = {}

		while(not str(schedule.iat[row_index, 0]).startswith("СОГЛ") and not str(schedule.iat[row_index, 0]).startswith("И.о")):
			rows_count_to_next_day = 1
			while(str(schedule.iat[row_index+rows_count_to_next_day, 0]) == "nan"):
				rows_count_to_next_day += 1
			
			parsed_lesson = parseOneTime(schedule, row_index)
			day_dict[LESSONS[lesson_counter]] = parsed_lesson
			lesson_counter += 1
			if(lesson_counter == 4):
				lesson_counter = 0
				row_index += 1
				all_dict[WEEKDAYS[day_number]] = day_dict
				day_number += 1
				day_dict = {}
			row_index += 2

		pprint.pprint(all_dict)
		schedule_dict[group_name] = all_dict


print("Сохраняю schedule...")
f = open("schedule.dat", mode="wb")
pickle.dump(schedule_dict, f)
f.close()
print("Сохранено!")

print("Загрузжаю schedule...")
f = open("schedule.dat", mode="rb")
schedule = pickle.load(f)
f.close()
print("Готово!")

print(schedule.keys())

	

