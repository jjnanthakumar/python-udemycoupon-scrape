from bs4 import BeautifulSoup
import re
from datetime import datetime
import pandas as pd
import requests
from collections import OrderedDict

SCRAPING_URLS = ["https://techietweets.com/category/100-free-courses/",
                 "https://udemycoupon.learnviral.com/coupon-category/free100-discount/"]

CLIENT_ID = "XGrj8erkqNey7u8KSGLnUoFYSTZhiLycFTCA1ND7"
CLIENT_SECRET = "QCLFjzPag6bJiJrBmUSGLKPvYdr8mEz9knf5R2cLgsikBlYGcJRyUkymM3GtORBxavnqXzgfVWDIIQAf2kSG3CppSVC0DaNR8Z1HTTbOXxbbnAWkfuYrVVVS2ynsp312"
AUTH_HEADER = {
  "Accept": "application/json, text/plain, */*",
  "Authorization": "Basic WEdyajhlcmtxTmV5N3U4S1NHTG5Vb0ZZU1RaaGlMeWNGVENBMU5ENzpRQ0xGanpQYWc2YkppSnJCbVVTR0xLUHZZZHI4bUV6OWtuZjVSMmNMZ3Npa0JsWUdjSlJ5VWt5bU0zR3RPUkJ4YXZucVh6Z2ZWV0RJSVFBZjJrU0czQ3BwU1ZDMERhTlI4WjFIVFRiT1h4YmJuQVdrZnVZclZWVlMyeW5zcDMxMg==",
  "Content-Type": "application/json;charset=utf-8"
}

class UdemyScraper:
    def __init__(self, domain = 0):
        self.url = SCRAPING_URLS[domain % len(SCRAPING_URLS)]
        self.courseURLs = []
        self.couponURLs = []
        self.scraper = requests.session()
        self.domain = domain % len(SCRAPING_URLS)
        if self.domain == 0:
            self.getUdemyCourseURLs()
        elif self.domain == 1:
            # self.scraper = cfscrape.create_scraper(sess=self.scraper)
            self.getUdemyCouponURLs()

    def checkCouponValidForUser(self, client_id = CLIENT_ID, client_secret = CLIENT_SECRET):
        checkerSession = requests.session()
        checkerSession.headers = AUTH_HEADER
        # Not working as expected
        for coupon in list(map(lambda x: x['Coupon URL'],self.couponURLs)):
            response = checkerSession.get(coupon)
            soup = BeautifulSoup(response.text, 'html.parser')
            print(soup.find('div',{'class':'price-text--container--Ws-fP udlite-clp-price-text'}))
            break



    def getUdemyCourseURLs(self, pages=3):
        for i in range(1, pages+1):
            pageURL = f'{self.url}'
            if i > 1:
                pageURL += f'page/{i}/'
            response = self.scraper.get(pageURL)
            soup = BeautifulSoup(response.text, 'html.parser')
            for links in soup.find_all('a', {'class': 'btn_more'}):
                self.courseURLs.append(links.get('href'))
        self.getUdemyCouponURLs()

    def getUdemyCouponURLs(self, pages=10):
        if self.domain == 1:
            for i in range(1, pages+1):
                pageURL = f"https://udemycoupon.learnviral.com/coupon-category/free100-discount/"
                if i > 1:
                    pageURL += f'page/{i}/'
                    headers = OrderedDict({
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Host': "udemycoupon.learnviral.com",
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
                    })
                    tempres = self.scraper.get(pageURL, allow_redirects=True, headers=headers)
                    tempsoup = BeautifulSoup(tempres.text, 'html.parser')
                    print(tempsoup.prettify())
                    break
                    tempAction = tempsoup.find(
                        'form', {'class': 'challenge-form'}).get('action')
                    pageURL = f'{SCRAPING_URLS[self.domain]}{tempAction[1:]}'
                response = self.scraper.get(pageURL)
                soup = BeautifulSoup(response.text, 'html.parser')
                for data in soup.find_all('div', {'class': 'item-holder'}):
                    CouponUpdatedDate = data.find(
                        'div', {'class': 'content-holder'}).text.strip().split('//')[0].strip()
                    currentDate = datetime.utcnow().date()
                    couponPostedDate = datetime.strptime(
                        CouponUpdatedDate, "%B %d, %Y").date()
                    self.couponURLs.append({'Coupon URL': data.find(
                        'a', {'class': 'coupon-code-link btn promotion'}).get('href'), 'isValid': (currentDate-couponPostedDate).days < 2})
        else:
            for course_url in self.courseURLs:
                response = self.scraper.get(course_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                couponUpdatedDate = soup.find('div', attrs={
                                              'class': 'date_time_post font80 fontnormal lineheight15'}).text.strip()
                formatted_date = UdemyScraper.preProcessDate(couponUpdatedDate)
                couponPostedDate = datetime.strptime(
                    formatted_date, "%B %d, %Y").date()
                currentDate = datetime.utcnow().date()
                couponUrl = soup.find(
                    'a', text=re.compile(r'.*ENROLL.*')).get('href')
                self.couponURLs.append({'Coupon URL': couponUrl, 'isValid': (
                    currentDate-couponPostedDate).days < 2})
        self.saveCouponsasExcel()
        # self.checkCouponValidForUser()
        return self.couponURLs

    @staticmethod
    def preProcessDate(valid_date):
        parts = valid_date.split()
        parts[1] = parts[1].zfill(3)
        return ' '.join(parts)

    def saveCouponsasExcel(self):
        filtered_data = list(filter(lambda x: x['isValid'], self.couponURLs))
        df = pd.DataFrame(filtered_data)
        df.to_excel('CouponsData.xlsx', 'coupons', index=False)
        print('saved')


scraper = UdemyScraper()
