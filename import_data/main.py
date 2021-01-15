import os
import csv
import glob
import pygsheets

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

# let's parse csv in chronological order
for filename in sorted(glob.glob('../DATA_TEST/*.csv')):
	new_final_prices = []
	new_prices_list = []
	not_imported_list = []
	new_prices_list, not_imported_list = data.parse_csv_file(filename, list_name, list_type)
	if(len(new_prices_list) > 0):
		
		if(len(new_prices_list[0]) == 9): # rcs
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
				date_new_obj = data.get_last_update_datetime(new_item)
				date_old_obj = data.get_last_update_datetime(new_final_prices[idx])
				if(date_new_obj > date_old_obj):
					new_final_prices[idx] = new_item
					updated_obj_counter+=1
					print("Update %s" %(new_final_prices[idx][0]))

		if(len(new_final_prices[0]) == 9): # rcs
			print("RCS UPDATE")
			wks_rcs = sht.worksheet_by_title("Prix HDV - Rcs")
			wks_rcs.update_values('B3', new_final_prices)
		else: # items
			print("ITEMS UPDATE")
			wks_items = sht.worksheet_by_title("Prix HDV - Items")
			wks_items.update_values('B3', new_final_prices)
		
		print("Total new: %d, %d not in list, %d updated" %(len(new_prices_list), appened_obj_counter, updated_obj_counter))

		if(len(not_imported_list) > 0):
			wks_bug_import = sht.worksheet_by_title("bug_import")
			l = wks_bug_import.get_values(start='A', end='B500', returnas='matrix')
			wks_bug_import.update_values((len(l)+1, 1), not_imported_list)