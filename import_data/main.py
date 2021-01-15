import os
import csv
import glob
import pygsheets
import statistics

import os.path
from os import path

import import_data as data
from termcolor import colored

# on prend les fichiers un par un:
# parse_new_data:
# 	rcs_prices = get_last_prices("rcs")
# 	items_prices = get_last_prices("items")
#
# 	list all the files available, and then open them one after the other (A->Z)
#
# 	new_prices = parse_csv_file(file)
#
# 	## For Gdoc:
# 	if rcs: iterate on new_prices and update last_rcs_prices with new values, if an object doesn't exist, append it
# 	if rcs: iterate on new_prices and update last_items_prices with new values, if an object doesn't exist, append it
# 	send_prices_to_gdoc("rcs")
# 	send_prices_to_gdoc("items")
#
# 	## For Panda:
# 	update_object_csv(new_prices):
# 		iterate over new_prices, if the csv of the object exist, append the new line on it, otherwise create object_csv
# 	
# 	

c = pygsheets.authorize()
sht = c.open_by_key("1yqubGRRZRZz25GHC1_UOdwHgG3sh-FhbLXh0Dv3-5n0")

wks_name = sht.worksheet_by_title("Full_DB")
list_name = wks_name.get_col(1)

wks_type = sht.worksheet_by_title("Catégories")
list_type = wks_type.get_col(1)

rcs_prices = data.get_last_obj_prices("rcs")
items_prices = data.get_last_obj_prices("items")


def is_obj_in_list(obj, list):
	for i in range(len(list)):
		if(obj[0] == list[i][0]):
			return i
	return -1

def create_row(obj, type):
	name = obj[0]
	#print(name)
	item = []
	if(type == "items"):
		item.append(obj[3]) # date
		item.append(obj[4]) # average_sold_price
		# list of items on sell
		items_prices = obj[5:]
		items_prices = list(filter(None, items_prices))
		#print(items_prices)
		item.append(min(items_prices) if len(items_prices) >= 1 else "") # min_selling_price
		item.append(max(items_prices) if len(items_prices) >= 1 else "") # max_selling_price
		item.append(len(items_prices)) # number_on_sell
		item.append(int(statistics.mean(items_prices)) if len(items_prices) > 1 else "") # mean
		item.append(int(statistics.median(items_prices)) if len(items_prices) > 1 else "") # median
		item.append(int(statistics.variance(items_prices)) if len(items_prices) > 1 else "") # variance
		item.append(int(statistics.stdev(items_prices)) if len(items_prices) > 1 else "") # stdev
	else:
		item.append(obj[3]) # date
		item.append(obj[4]) # average_sold_price
		item.append(obj[8]) # min_selling_price
		item.append(obj[5]) # per_1
		item.append(obj[6]) # per_10
		item.append(obj[7]) # per_100

	return item

def update_obj_csv(obj, type):
	name = obj[0].replace(' ', '_').replace("'", '')
	path_name = "./obj_csv/" + name + ".csv"

	if(path.exists(path_name)):
		new_row = create_row(obj, type)
		date_new_row = data.get_datetime_from_string(obj[3])

		# check if record already exist:
		record_exist = False
		with open(path_name, 'r') as f:
			csv_reader = csv.reader(f)
			next(csv_reader) # remove first line
			for row in csv_reader:
				date_csv_obj = data.get_datetime_from_string(row[0])
				if(date_csv_obj == date_new_row):
					record_exist = True

		if(not record_exist):
			with open(path_name, 'a') as f:
				write = csv.writer(f)
				write.writerow(new_row)
				#print("%s add record" %(name))
	else: # first time, file doesn't exist
		with open(path_name, 'w+') as f:
			write = csv.writer(f)

			if(type == "rcs"):
				write.writerow(["", "average_sold_price", "min_selling_price", "per_1", "per_10", "per_100"])
			else:
				write.writerow(["", "average_sold_price", "min_selling_price", "max_selling_price", "number_on_sell", "mean", "median", "variance", "stdev" ])

			write.writerow(create_row(obj, type))
			#print("%s add first record" %(name))


# let's parse csv in chronological order
for filename in sorted(glob.glob('../DATA_TEST/*.csv')):
	print("PARSING %s" %(filename))
	new_final_prices = []
	new_prices_list = []
	not_imported_list = []
	new_prices_list, not_imported_list = data.parse_csv_file(filename, list_name, list_type)
	if(len(new_prices_list) > 0):
		obj_type = ""
		if(len(new_prices_list[0]) == 9): # rcs
			obj_type = "rcs"
		else:
			obj_type = "items"
		#===============================================================================================
		# PANDA
		for obj in new_prices_list:
			update_obj_csv(obj, obj_type)
		continue

		#===============================================================================================
		# GDOC
		if(obj_type == "rcs"):
			print("Ressources prices")
			new_final_prices = rcs_prices
		else:
			print("Items prices")
			new_final_prices = items_prices

		# now let's update prices:
		updated_obj_counter = 0
		appened_obj_counter = 0
		for new_item in new_prices_list:
			# check if already in list
			idx = is_obj_in_list(new_item, new_final_prices)
			if(idx == -1):
				new_final_prices.append(new_item)
				appened_obj_counter+=1
			else:
				date_new_obj = data.get_datetime_from_string(new_item[3])
				date_old_obj = data.get_datetime_from_string(new_final_prices[idx][3])
				if(date_new_obj > date_old_obj):
					new_final_prices[idx] = new_item
					updated_obj_counter+=1
					#print("Update %s" %(new_final_prices[idx][0]))

		if(obj_type == "rcs"): # rcs
			#print("RCS UPDATE")
			wks_rcs = sht.worksheet_by_title("Prix HDV - Rcs")
			wks_rcs.update_values('B3', new_final_prices)
		else: # items
			#print("ITEMS UPDATE")
			wks_items = sht.worksheet_by_title("Prix HDV - Items")
			wks_items.update_values('B3', new_final_prices)
		
		print("Total new: %d, %d not in list, %d updated" %(len(new_prices_list), appened_obj_counter, updated_obj_counter))

		if(len(not_imported_list) > 0):
			# Let's check in the big list (13k rows) if we can find the unfinded ones
			wks_all = sht.worksheet_by_title("All_items")
			full_list_all_name = wks_all.get_col(1)
			not_imported_list_filtered = []
			not_imported_list_no_match = []

			for n in not_imported_list:
				name = data.filter_name(n[0], full_list_all_name)
				if(name != "?"):
					not_imported_list_filtered.append([name])
				else:
					if(len(n)>0):
						not_imported_list_no_match.append(n)

			#print("==============================================================================================")
			#print("not_imported_list_filtered")
			#print(not_imported_list_filtered)
			if(len(not_imported_list_filtered)>0):
				wks_ni_filtered = sht.worksheet_by_title("fin_rcs")
				l = wks_ni_filtered.get_values(start='A', end='B500', returnas='matrix')
				wks_ni_filtered.update_values((len(l)+1, 1), not_imported_list_filtered)
			
			#print("==============================================================================================")
			#print("not_imported_list_no_match")
			#print(not_imported_list_no_match)
			if(len(not_imported_list_no_match)>0):
				wks_bug_import = sht.worksheet_by_title("bug_import")
				l = wks_bug_import.get_values(start='A', end='B500', returnas='matrix')
				wks_bug_import.update_values((len(l)+1, 1), not_imported_list)
