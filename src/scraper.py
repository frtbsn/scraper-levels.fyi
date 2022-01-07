from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import requests
from time import sleep
from utils import *
import os
from datetime import datetime
import numpy as np


def scrape_category(category, driver, log_txt):
	log_txt += category + " : "
	path_file_category = os.path.join(FOLDER_DB, category + ".csv")
	prev_category_rows = pd.read_csv(path_file_category).values.tolist() if os.path.exists(path_file_category) else []
	category_rows = []

	driver.get(url_top + "?track=" + category)
	sleep(500 / 1000)
	i = 0
	#print(category)
	while True:
		i += 1
		soup = BeautifulSoup(driver.page_source, "html.parser")
		for tr in soup.find_all("tr", attrs={"data-has-detail-view": "true"}):
			for i, td in enumerate(tr.find_all("td")[1:]):
				td = td.text.strip().replace("\n\n", " ").split("\n")
				if i == 0:
					comp_name = td[0]
					d = td[1].split("|")
					date = format_date(d[1].strip())
					res = list(map(str.strip, d[0].split(',')))
					if len(res) == 2:
						res += ["United States"]
					comp_city, comp_region, comp_country = res[:3]
				elif i == 1:
					if len(td) == 1:
						tag = td if type(td) != list else td[0]
						level = np.NaN
					else:
						level, tag = td
				elif i == 2:
					yrs_comp, yrs_xp = [float(m) for m in map(str.strip, td[0].split('/'))]
				else:
					d = td[0].replace("  ", "").split(' ')
					dec, nego_up = 0, 0
					if len(d) == 7:
						nego_up = format_salary(d[0][2:])
						dec = 1
					tot_salary = format_salary(d[dec])
					try:
						base_salary = format_salary(d[dec + 1])
						stock_salary = format_salary(d[dec + 3])
						bonus_salary = format_salary(d[dec + 5])
					except IndexError:
						base_salary = np.NaN
						stock_salary = np.NaN
						bonus_salary = np.NaN

			new_row = [category, comp_name, comp_country, comp_region, comp_city, date, level, tag, yrs_comp,
			           yrs_xp, tot_salary, base_salary, stock_salary, bonus_salary, nego_up]

			bool_finished, final_rows = lap_finished(new_row, prev_category_rows, category_rows, tol=2)
			if bool_finished:
				log_txt += f"{len(category_rows)} (new) + {len(prev_category_rows)} (previous) = {len(final_rows)}\n"
				df_tmp = pd.DataFrame(final_rows, columns=DF_COLUMNS)
				df_tmp.to_csv(path_file_category, index=False)
				return df_tmp, log_txt
			else:
				category_rows.append(new_row)

		element = driver.find_element(By.CSS_SELECTOR, 'li.page-item:last-child')
		driver.execute_script("arguments[0].click();", element)
		sleep(1500 / 1000)
		if i == 100:
			send_mail_if_error(category)
			break


if __name__ == "__main__":

	os.chdir(FOLDER_PROJECT)

	log_txt = '\n-----' + str(datetime.now()).split('.')[0] + '-----\n'

	options = webdriver.ChromeOptions()
	options.add_argument('--headless')
	driver = webdriver.Chrome(options=options)

	soup = BeautifulSoup(requests.get(url_top).content, 'html.parser')
	category_jobs = [i.text for i in soup.find_all("option")]
	all_dfs = []
	for category in category_jobs:
		df_cat, log_txt = scrape_category(category, driver, log_txt)
		all_dfs.append(df_cat)

	all_dfs = pd.concat(all_dfs)
	all_dfs.to_csv(os.path.join(FOLDER_DB, "ALL.csv"), index=False)

	write_log_file(log_txt)
	driver.quit()