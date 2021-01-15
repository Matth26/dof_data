import re
import os
import csv
import glob
import urllib
import pygsheets

from bs4 import BeautifulSoup
from termcolor import colored
from datetime import datetime
from Levenshtein import distance as levenshtein_distance

####################################################################################################
# obj_type = "rcs" or "items"
# return a matrix with all the previous logged price (on gdoc)
def get_last_obj_prices(obj_type):
	c = pygsheets.authorize()
	sht = c.open_by_key("1yqubGRRZRZz25GHC1_UOdwHgG3sh-FhbLXh0Dv3-5n0")
	ret = []
	if(obj_type == "rcs"):
		wks = sht.worksheet_by_title("Prix HDV - Rcs")
		ret = wks.get_values(start='B3', end='J4000', returnas='matrix')
	else:
		wks = sht.worksheet_by_title("Prix HDV - Items")
		ret = wks.get_values(start='B3', end='CP4000', returnas='matrix')
	return ret

####################################################################################################
# obj_row: a row in the matrix returned by get_last_obj_prices function
# return the datetime python object
def get_last_update_datetime(obj_row):
	return datetime.strptime(obj_row[3].replace('-', '/'), '%d/%m/%Y %H:%M:%S')

####################################################################################################
# take a raw_name (raw because from sikuli), and a list of name where it will check for filtering
# the raw_name
def filter_name(raw_name, list_name):
	ld_list = [levenshtein_distance(e, raw_name) for e in list_name]
	min_ld = min(ld_list)
	filtered_name = "?"
	if(min_ld > 2):
		name_lenght = len(raw_name)
		if(name_lenght >= 30):
			print(colored("[1] %s (= %s) min_ld = %d" %(raw_name, list_name[ld_list.index(min_ld)], min_ld), 'yellow'))
			# the name might be truncated:
			ld_list = [levenshtein_distance(e[0:name_lenght], raw_name) for e in list_name]
			min_ld = min(ld_list)
			if(min_ld > 4):
				print(colored("[2] %s (= %s) min_ld = %d" %(raw_name, list_name[ld_list.index(min_ld)], min_ld), 'red'))
			else:
				print(colored("[2] %s (= %s) min_ld = %d" %(raw_name, list_name[ld_list.index(min_ld)], min_ld), 'green'))
				filtered_name = list_name[ld_list.index(min_ld)]
		else:
			print(colored("[1] %s (= %s) min_ld = %d" %(raw_name, list_name[ld_list.index(min_ld)], min_ld), 'red'))
	else:
		filtered_name = list_name[ld_list.index(min_ld)]
		#print("%s => %s" %(name, filtered_name))
	return filtered_name

####################################################################################################
# take unit price (p1), price per 10 (p10) and per 100 (p100) and return the min
def get_min_price(p1, p10, p100):
	if(p1 == "-" and p10 == "-" and p100 == "-"):
		return "-"
	else:
		return int(min([p1 if p1 != "-" else 100000000, p10/10 if p10 != "-" else 100000000, p100/100 if p100 != "-" else 100000000]))

####################################################################################################
# parse the file in argument
# for each row it searchs if it can match the name of the item with the DB (in gdoc)
# return a matrix with one item per row
def parse_csv_file(filename, list_name, list_type):
	final_obj_list = []
	not_imported_list = []
	with open(filename, 'r') as csvfile: # open in readonly mode
		csvReader = csv.reader(csvfile, delimiter=';')
		for row in csvReader:
			#print(row)
			arr = []

			name_raw = row[0]
			filtered_name = filter_name(name_raw, list_name)

			arr.append(filtered_name)
			if(filtered_name == ""):
				continue
			elif (filtered_name == "?"):
				not_imported_list.append(name_raw)
				continue

			type_raw = row[1]
			filtered_type = filter_name(type_raw, list_type)
			arr.append(filtered_type)

			lvl_raw = row[2]
			if(lvl_raw.isdigit()):
				arr.append(int(lvl_raw))
			else:
				arr.append("-")

			date_hour = row[4] + '/' + row[3] + '/' + row[5] + ' ' + row[6] + ':' + row[7] + ':' + row[8]
			arr.append(date_hour)

			price_mean = row[10].replace("kamas/u.", "").replace(" ", "")
			if(price_mean.isdigit()):
				arr.append(int(price_mean))
			else:
				arr.append("-")

			#=====================================================
			# Now specific if item or rcs:
			if(len(row) == 14):
				price_1_raw = row[11].replace(" ", "")
				price_1 = "-"
				if(price_1_raw.isdigit()):
					price_1 = int(price_1_raw)
				arr.append(price_1)

				price_10_raw = row[12].replace(" ", "")
				price_10 = "-"
				if(price_10_raw.isdigit()):
					price_10 = int(price_10_raw)
				arr.append(price_10)

				price_100_raw = row[13].replace(" ", "")
				price_100 = "-"
				if(price_100_raw.isdigit()):
					price_100 = int(price_100_raw)
				arr.append(price_100)

				arr.append(get_min_price(price_1, price_10, price_100))
			else:
				row_size = len(row)
				for i in range(11, row_size):
					price_raw = row[i].replace(" ", "")
					price = "-"
					if(price_raw.isdigit()):
						price = int(price_raw)
					arr.append(price)
				
			# then append it:
			final_obj_list.append(arr)
	
	return final_obj_list, not_imported_list






"""not_imported_list = []


c = pygsheets.authorize()
sht = c.open_by_key("1yqubGRRZRZz25GHC1_UOdwHgG3sh-FhbLXh0Dv3-5n0")

wks_name = sht.worksheet_by_title("Full_DB")
list_name = wks_name.get_col(1)

wks_type = sht.worksheet_by_title("Catégories")
list_type = wks_type.get_col(1)

final_rcs_array = []
final_item_array = []


print("==============================================================================================")
# Let's check in the big list (13k rows) if we can find the unfinded ones
wks_all = sht.worksheet_by_title("All_items")
full_list_all_name = wks_all.get_col(1)
not_imported_list_filtered = []
not_imported_list_no_match = []

print("not_imported_list")
print(not_imported_list)

for n in not_imported_list:
	name = filter_name(n, full_list_all_name)
	if(name != "?"):
		not_imported_list_filtered.append([name])
	else:
		if(len(n)>0):
			not_imported_list_no_match.append([n])

print("==============================================================================================")
print("not_imported_list_filtered")
print(not_imported_list_filtered)
if(len(not_imported_list_filtered)>0):
	wks_1 = sht.worksheet_by_title("fin_rcs")
	wks_1.update_values('A1', not_imported_list_filtered)
print("==============================================================================================")
print("not_imported_list_no_match")
print(not_imported_list_no_match)
if(len(not_imported_list_no_match)>0):
	wks_2 = sht.worksheet_by_title("bug_import")
	wks_2.update_values('A1', not_imported_list_no_match)
print("==============================================================================================")


if(len(final_rcs_array)>0):
	wks = sht.worksheet_by_title("Prix HDV - Rcs")
	wks.update_values('A3', final_rcs_array)

if(len(final_item_array)>0):
	wks = sht.worksheet_by_title("Prix HDV - Items")
	wks.update_values('A3', final_item_array)"""