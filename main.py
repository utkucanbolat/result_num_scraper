from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from datetime import datetime
from time import sleep, time
from re import findall
from csv import writer
from os import stat


class FrequencyScrapper:
    def __init__(self):
        self.url = "https://www.google.com"
        self.save_path = "crypto_freq_data.csv"

        self.google_search_bar_xpath_first = '/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div/div[2]/input'
        self.google_search_bar_xpath_not_first = '/html/body/div[4]/div[2]/form/div[1]/div[1]/div[2]/div[1]/div/div[2]/input'

        self.is_first_call = True  # first search is different from the rest. True if it's the first search, false otherwise.
        self.intrinsic_wait = 1  # wait between search, enter keys, etc. to settle.
        self.search_time = 10  # wait this much, if it still cannot scrape, re-initilize the browser
        
        self._init_driver()

        self.coin_list = []
        with open("coin_list.csv", "r") as f:
            for line in f.readlines():
                for var in line.split(";")[0:2]:
                    self.coin_list.append(var)

        self.search_key_modifiers = [""]  # ["", "coin", "crypto"]

        self.extended_coin_list, self.search_values = [], []

        for coin_name in self.coin_list:
            for modifier in self.search_key_modifiers:
                self.full_name = coin_name + " " + modifier
                self.extended_coin_list.append(self.full_name)

    def _init_driver(self):
        loop_flag = True
        while loop_flag:
            try:
                self.options = Options()
                self.options.headless = True
                self.driver = webdriver.Firefox(options=self.options, executable_path=r'geckodriver')
                self.driver.set_page_load_timeout(10)
                self.driver.get(self.url)
                # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.is_first_call = True  # since browser is restarted the new search will be first search
                loop_flag = False
            except Exception:
                sleep(self.search_time)

    def scrap(self):
        for var in self.extended_coin_list:
            print("Scrapping: \t" + var)
            self.search_values.append(self._num_result_finder(var))

    def _num_result_finder(self, search_key):
        t1 = time()  # track time. if time elapsed for searching exceeds self.search_time initilize browser again
        loop_flag = True
        while loop_flag:
            try:
                if self.is_first_call:
                    input_element = self.driver.find_element(By.XPATH, self.google_search_bar_xpath_first)
                    self.is_first_call = False
                else:
                    input_element = self.driver.find_element(By.XPATH, self.google_search_bar_xpath_not_first)

                input_element.clear()

                # find text field by xpath to search
                input_element.send_keys(search_key)
                sleep(self.intrinsic_wait)
                input_element.send_keys(Keys.ENTER)
                sleep(self.intrinsic_wait)

                # find the text that contains num result info
                num_search_result = self.driver.find_element(By.XPATH, '//*[@id="result-stats"]')
                num_search_result_text = num_search_result.text

                # divide text into two halves because it also contains both search number and duration
                separative_key = "bulundu"  # bulundu is only for Turkish. Be careful!
                num_search_result_text_num_only = num_search_result_text.split(separative_key)[0]

                result = findall(r'(\d)', num_search_result_text_num_only)
                num_result = "".join(result)  # finally, scraped number of search in string format to write csv file.

                loop_flag = False

                return num_result

            except Exception as err:
                print("#" * 50)
                print(err)
                print("#" * 50)
                if abs(t1-time()) > self.search_time:
                    self.close_drivers()
                    sleep(2)
                    self._init_driver()
                    sleep(2)
                else:
                    print(f"Error occured. Waiting for {self.intrinsic_wait} seconds to proceed. ")
                    sleep(self.intrinsic_wait)

    def close_drivers(self):
        self.driver.close()
        self.driver.quit()

    def read_and_write_csv(self):
        now = datetime.now()
        time_now = now.strftime("%d/%m/%Y %H:%M")

        with open(self.save_path, mode='a') as f:
            f = writer(f, delimiter=';', lineterminator='\n')
            if stat(self.save_path).st_size == 0:
                f.writerow([" "] + self.extended_coin_list)
            f.writerow([time_now] + self.search_values)


if __name__ == "__main__":
    coin_freq_scrap = FrequencyScrapper()
    coin_freq_scrap.scrap()
    coin_freq_scrap.close_drivers()
    coin_freq_scrap.read_and_write_csv()
