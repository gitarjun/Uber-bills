from PIL import Image
from io import BytesIO
from collections import OrderedDict

import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

class UberBill(object):
    def __init__(self,cookie_path):
        if not os.path.exists(cookie_path):
            print('[-] Cookie path is required for authentication and bypass reCAPTCHA')
            return
        with open(cookie_path,'r') as Fp:
            raw_cookie = Fp.read()

        self.cookie = eval(self._format_cookie(raw_cookie))

        self.driver = webdriver.Chrome()

        self._load_uber_auth()

        self.bill_dict = OrderedDict()

    def _format_cookie(self,raw_cookie):
        return raw_cookie.replace('false','False').replace('true','True')

    def _load_uber_auth(self):
        self.driver.get("https://riders.uber.com/")
        for cookie in self.cookie:
            self.driver.add_cookie(cookie)
        self.driver.get("https://riders.uber.com/trips")

    def update_date(self,date_str):
        try:
            from_date = datetime.strptime(date_str, '%d %B %Y')
            self.tardate = from_date
            return True
        except:
            return False

    def close_driver(self):
        try:
            self.driver.quit()
        except AttributeError:
            pass

    def _web_driver_wait(self,xpath, time=15):
        try:
            return WebDriverWait(self.driver, time).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except:
            return 0

    def _trip_collapse(self,item, index=None):
        size = item.size
        w, h = size['width'], size['height']

        if w / h < 2:
            if index:
                self.driver.execute_script(
                    "document.querySelector('div[data-identity=\"trip-container\"]:nth-child({})>div:nth-child(1)>div:nth-child(1)').click();".format(
                        index + 1))
            else:
                item.find_element_by_xpath('.//div/div').click()

    def _get_date_price(self,item):
        date, price = item.find_element_by_xpath('.//div[@class="an"]').text.split('\n')
        return datetime.strptime(date, '%d %B %Y, %I:%M%p'), price[1:]

    def _is_displayed(self,item):
        return item.find_element_by_xpath('.//div[2]/div[2]/div[1]/div/div').is_displayed()

    def _get_next_page(self):
        icon = self.driver.find_element_by_xpath(r'//div[@data-identity="pagination-next"]')
        if icon.get_attribute('disabled') == 'true':
            return
        else:
            self.driver.execute_script("document.querySelector('div[data-identity=\"pagination-next\"]').click();")

    def _get_prev_page(self):
        icon = self.driver.find_element_by_xpath(r'//div[@data-identity="pagination-prev"]')
        if icon.get_attribute('disabled') == 'true':
            return
        else:
            self.driver.execute_script("document.querySelector('div[data-identity=\"pagination-prev\"]').click();")

    def _trip_expand(self,item, index=None):
        size = item.size
        w, h = size['width'], size['height']

        if w / h > 2:
            if index:
                self.driver.execute_script(
                    "document.querySelector('div[data-identity=\"trip-container\"]:nth-child({})>div:nth-child(1)>div:nth-child(1)').click();".format(
                        index + 1))
            else:
                item.find_element_by_xpath('.//div/div').click()

    def _take_image(self,item, index=None):
        self._trip_expand(item, index)
        item.location_once_scrolled_into_view
        png = item.screenshot_as_png
        im = Image.open(BytesIO(png))
        self._trip_collapse(item, index)
        return im

    def load_page(self):
        self.driver.get("https://riders.uber.com/trips")
        x = self._web_driver_wait(r'//div[@data-identity="trip-list"]')
        trips = x.find_elements_by_xpath(r'//div[@data-identity="trip-container"]')
        self._trip_collapse(trips[0])
        while True:
            flag = 0
            x = self._web_driver_wait(r'//div[@data-identity="trip-list"]', 50)
            trips = x.find_elements_by_xpath(r'//div[@data-identity="trip-container"]')
            for index, x in enumerate(trips):
                # get dates
                d, p = self._get_date_price(x)
                if p.find('Cancelled') > -1:
                    continue
                if self.tardate > d:
                    flag = 1
                    break
                stringgg = d.strftime('%d %B %Y, %I:%M%p')
                image_png = self._take_image(x, index)
                self.bill_dict[stringgg]=image_png

            if flag == 1:
                break
            else:
                self._get_next_page()

    def save_bills(self,options):
        bills = list(self.bill_dict)
        bill_keys = [bills[int(x)-1] for x in options]
        for each in enumerate(reversed(bill_keys)):
            self.bill_dict[each[1]].save('('+str(each[0]+1)+')'+each[1].replace(' ','').replace(':','').replace(',','')+'.png')


if __name__=='__main__':
    obj = UberBill(r"C:\Users\Arjun\Desktop\cookie.txt") # initialize class with session cookie after logging in to Uber manually to bypass reCAPTCHA
    ans = input('Did You Login to the page? (Y/N) :').lower() # Confirmation after successful login
    if ans=='y':
        print('Great')
        print('Loading trips')
        for i in range(3):
            dates = input('Enter the date in Uber format Ex: 31 July 2019 Ans:')
            if obj.update_date(dates):
                break
            else:
                print('Date is not proper')
        else:
            obj.close_driver()
        obj.load_page()
        obj.close_driver()
        print('Choose Bills\n')
        for i,each in enumerate(list(obj.bill_dict.keys())):
            print('{}->{}'.format(i+1,each))
        bills = input('Input numbers Comma seperated :').split(',')

        obj.save_bills(bills)

    else:
        print('Oh! OK Bye')
        obj.close_driver()