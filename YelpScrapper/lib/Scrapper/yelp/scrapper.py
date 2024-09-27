import csv
import re
import os

from uuid import uuid4, UUID
from utils.utils import clean_text, is_english
from typing import TextIO
from .review import Review, BusinessInfo, Location

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import undetected_chromedriver as uc


from loguru import logger
from time import sleep
from pendulum import datetime
import random


class YelpScrapper:
    original_window: str
    location: str = "San Jose, CA" # Can be externally passed in.
    search_query: str
    driver: WebDriver
    global_path: str = "{Download directory}"


    def init_driver(self):
      
        chrome_options = uc.ChromeOptions()

        # Disable automation controlled flag
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        # Exclude automation controlled switches
       # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # Turn-off userAutomationExtension
       # chrome_options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(
            options=chrome_options,
            service=Service(executable_path="/usr/bin/chromedriver"),
        )
        # Change the navigator value for driver to undefined
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        self.driver.delete_all_cookies()
        self.driver.get("https://www.yelp.com")
        logger.success("Connected to Yelp successfully. Driver init complete.")


    def __init__(self, search_query: str | None, location: str = "San Jose, CA"):

        self.init_driver()
        # logger.debug(driver.title)
        assert "Yelp" in self.driver.title
        logger.success(f"Website connected successfully {self.driver.current_url}")


        """
            Reqest and set search query from user
        """
        if not search_query:
            self.search_query = input("Search query: ")
        else:
            self.search_query = search_query
        self.location = location # We should be able to pass this from stdio

        self.create_root_directory()

        
        """ 
            Search for provided query 
        """
        elem = self.driver.find_element(By.ID, "search_description")
        #locale_elem = self.driver.find_element(By.ID, "search_location")
        self.send_keys_delayed(self.search_query, elem)
        #self.send_keys_delayed(self.location, locale_elem)
        elem.send_keys(Keys.ENTER)
        sleep(2 + random.random() * 0.5)
        # Often there will be a captcha at this point.
        self.check_for_captcha()
        self.original_window = self.driver.current_window_handle


        # ------ DEBUG output HTML ------
        # html_source = self.driver.page_source
        # with open("debug.html", "w", encoding="utf-8") as file:
        #   file.write(html_source)


    def create_root_directory(self):
        """
            #### Create a download directory.

            If the queried directory exists, use the existing directory.
        """
        try:
            if not os.path.exists(f"{self.global_path}/{self.search_query}"):
                os.makedirs(name=f"{self.global_path}/{self.search_query}", exist_ok=True)
                logger.info(f"Created directory for query: {self.search_query}")
            else:
                logger.info(f"Using existing directory {self.global_path}/{self.search_query}")
        except Exception as e:
            logger.exception(f"Could not create directory! {e}")

    def create_or_append_business_csv(business: BusinessInfo):
        #TODO - Add a path for the file
        with open('business.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['name', 'imgs', 'rating', 'num_ratings', 'reviews', 'offerings', 'price_range', 'locations'])

            # Write header only if file is empty
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(business.to_csv())
    
    def create_or_append_review_csv(review: Review):
        #TODO - Add a path for the file
        with open('reviews.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['buis_id', 'username', 'rating', 'text', 'date'])

            # Write header only if file is empty
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(review.to_csv())



    def send_keys_delayed(self, query: str, elem: WebElement):
        """
            #### Helper function for text input.
        """
        elem.click()
        for i in query:
            # logger.debug(i)
            sleep(random.random() * 0.03 + 0.01)
            elem.send_keys(i)
        return
    

    def check_for_captcha(self):
        """
            Helper function for captcha situations.
        """
        try:
            # Attempt to find the CAPTCHA iframe or any element that indicates a CAPTCHA is present
            captcha_iframe = self.driver.find_element(By.TAG_NAME, "iframe")

            # If found, log the presence of the CAPTCHA and wait for manual input
            logger.warning("CAPTCHA detected. Please solve it manually in the browser.")
            while True:
                sleep(2)
                # Check if the CAPTCHA is still present
                if not captcha_iframe.is_displayed():
                    logger.success("CAPTCHA solved. Continuing script.")
                    sleep(1.5)
                    break
        except NoSuchElementException:
            # CAPTCHA is not present
            logger.info("No CAPTCHA detected.")


    """
        

        :rType: Status code after completion
    """
    def run(self) -> int:
        """
            Main loop
            
            Flow: N x Query Result Pages -> M x Buisness pages -> Z x Reviews 

            :rtype: Status code
        """
        logger.info("Beginning to run scrapper service.")

        
        """
            After successful navigation set local variables.
        """
        try:
            review_elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".container__09f24__FeTO6.hoverable__09f24___UXLO.y-css-way87j"
            ) 
            logger.debug(
                f"{len(review_elements)}  results found on page: {self.driver.current_url} from driver: {self.driver}"
            )
            pagination_button = self.driver.find_element(
                By.XPATH, '//*[@id="main-content"]/ul/li[21]/div/div/div[11]/span/a'
            )
            next_page_disabled: bool = (
                pagination_button.get_attribute("disabled") is None
            )  # True if button isn't disabled
        except NoSuchElementException:
            logger.exception("FATAL: No Query results found or page navigation error.")


        while next_page_disabled:
            

            """
              Open all results on current page
            """
            for result in review_elements:
                #logger.debug(f"Opening result: {result}")
                sleep(1 * random.random() * 0.05 ** random.random() + 0.4)
                result.click()
            sleep(1.5 + random.random() * 0.5)


            """
                For each business page (BP) opened, navigate to the 
                business page and begin collecting reviews. 
            """
            for window in self.driver.window_handles:
                
                """Navigate to Business Page"""
                if window == self.original_window:
                    continue
                self.driver.switch_to.window(window)
                logger.debug(f"Switching to page: {self.driver.current_url}")
                
                
                # Get buisness data and 
                try:
                    buis: BusinessInfo = self.get_buis_info(driver=self.driver)
                except ValueError:
                    logger.error(
                        f"Error occurred when constructing business. Window: {self.driver.current_url}"
                    )
                    continue
                except Exception as e:
                    logger.error(f"Error occured when constructing business. {e}")
                    continue

                                
                # DEPRECATED: We will start hashing businesses info for a unique UUID to prevent collisions across machines.
                if os.path.exists(f"{self.global_path}/{self.search_query}/{buis.name}/reviews.txt"):
                    logger.info("Reviews already gathered. Skipping...")
                    continue


                # Download the images
                self.download_buisness_pics(buis_name=buis.name)

                # Add business info to the businesses csv file
                self.create_or_append_business_csv(business=buis)


                more_reviews: WebElement | None = self.get_more_reviews()
                review_page: int = 0
                while more_reviews:
                    sleep(2)
                    page_reviews = self.driver.find_elements(
                        By.XPATH,
                        "/html/body/yelp-react-root/div[1]/div[6]/div/div[1]/div[1]/main/div[3]/div/section/div[2]/ul/li[div]",
                    )
                    self.parse_reviews(
                        buis_id=buis.id,
                        page_reviews=page_reviews
                    )
                    more_reviews = self.get_more_reviews()
                    more_reviews.click()
                    review_page += 1

                self.driver.close()
                logger.success(f"Completed gathering reviews for buisness: {buis.name}")
            # END FOR


            # Navigate back to search result page
            self.driver.switch_to.window(self.original_window)


            # -------------- Get search result pages ---------------------
            # navigate to next SEARCH RESULT page
            sleep(3 + random.random() * 0.7)
            pagination_button.click()
            

            # Reassign local variables
            pagination_button = self.driver.find_element(
                By.XPATH,
                '//button[@type="submit" and @class="pagination-button__09f24__kbFYf y-css-1ewzev" and @data-activated="false" and @value="submit" and @data-button="true"]',
            )
            next_page_disabled: bool = (
                pagination_button.get_attribute("disabled") is None
            )
            self.original_window = self.driver.current_window_handle

            try:
                # Grab search results for this page
                review_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".container__09f24__FeTO6.hoverable__09f24___UXLO.y-css-way87j",
                )
                logger.debug(f"{len(review_elements)} results")
            except:
                logger.error("No results found on page.")

        self.driver.close()
        self.driver.stop_client()
        self.driver.quit()
        return 0
    

    def download_buisness_pics(self, buis_name: str):
        
        # Define the XPaths
        xpaths = [
            "/html/body/yelp-react-root/div[1]/div[4]/div[2]/div/div[1]/a/img",
            "/html/body/yelp-react-root/div[1]/div[4]/div[2]/div/div[2]/a/img",
            "/html/body/yelp-react-root/div[1]/div[4]/div[2]/div/div[3]/a/img",
        ]
        sources: list[str] = []

        # Get the image sources
        for path in xpaths:
            try:
                img_element = self.driver.find_element(By.XPATH, path)
                source = img_element.get_attribute("src")
                if source:
                    sources.append(source)
            except Exception as e:
                logger.error(f"Error finding the element with xpath: {path}: {e}")
                continue
        
        prev_window: str = self.driver.current_url
        for idx, source in enumerate(sources):
            try:
                self.driver.get(source)
                save_path = os.path.join(
                        f"{self.global_path}/{self.search_query}/{buis_name}/media/", f"image_{idx + 1}.jpg"
                    )
                
                with open(save_path, 'xb') as file:
                    file.write(self.driver.find_element(By.TAG_NAME, "img").screenshot_as_png)
            except Exception as e:
                logger.warning(f"Could not download the requested image resource: {e}")

        self.driver.get(prev_window)
        logger.success("Completed image downloads.")


    def get_more_reviews(self) -> WebElement | None:
        # Grab the more reviews button on business page, ensuring it exists.
        try:
            more_reviews_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                '[aria-label="Next"]'
            )
            class_attr = more_reviews_btn.get_attribute("class")
            if "navigation-button-icon--disabled__09f24__z98Q4" in class_attr:
                more_reviews_btn = None
           
        except:
            logger.warning("Could not locate the find reviews button!")
            more_reviews_btn = None
        return more_reviews_btn

    def get_buis_info(self, driver: WebDriver) -> BusinessInfo:
        """
            Function to gather business info from the page.
            
            :rtype: BusinessInfo object
        """

        """
            Gather critical business info.
        """
        try:
            buis_name = driver.find_element(By.XPATH, '//h1[@class="y-css-olzveb"]')
            # Get buisness overall rating
            rating_overall = driver.find_element(
                By.XPATH, '//span[@class=" y-css-kw85nd"]'
            )  # -- Rating /5
            ratings_total = driver.find_element(
                By.XPATH, '//a[@class="y-css-12ly5yx"]'
            )  # -- Num Ratings
            ratings_total_val = (
                ratings_total.text.replace("(", "")
                .replace(")", "")
                .replace(" reviews", "")
                .replace(",", "")
                .replace(" review", "")
            )
        except NoSuchElementException as e:
            raise NoSuchElementException


        """
            Price ranges are non-critical and can be ignored.
        """
        try:
            price_range = len(driver.find_element(
                By.XPATH, '/html/body/yelp-react-root/div[1]/div[4]/div[1]/div[1]/div/div[2]/span[2]/span'
            ).text)
        except (ValueError, NoSuchElementException) as e:
            logger.warning(f"Could not find price range. {e}")
            price_range = 0


        offerings = self.get_offerings()
        location = self.get_location()


        try:
            buis = BusinessInfo(
                id=uuid4(),
                name=buis_name.text,
                imgs=None,
                rating=float(rating_overall.text),
                offerings=offerings,
                price_range=price_range,
                num_ratings=int(ratings_total_val),
                reviews=None,
                location=location,
            )
        except Exception as e:
            logger.error(f"Error occurred when constructing business object: {e}")
            raise
        return buis
    

    def get_offerings(self) -> list[str]:
        xpaths = [
            "/html/body/yelp-react-root/div[1]/div[4]/div[1]/div[1]/div/div[2]/span[3]/span[1]/a",
            "/html/body/yelp-react-root/div[1]/div[4]/div[1]/div[1]/div/div[2]/span[3]/span[3]/a",
            "/html/body/yelp-react-root/div[1]/div[4]/div[1]/div[1]/div/div[2]/span[3]/span[2]/a"
        ]

        res: list[str] = []
        for path in xpaths:
            try:
                elem = self.driver.find_element(By.XPATH, path)
                res.append(elem.text)
            except Exception as e:
                logger.warning("Could not find offering element")
                continue
        return res


    def get_location(self) -> Location:
        logger.info("Gathering location information")
        address = self.driver.find_element(By.TAG_NAME, 'address')

        """
            Location is stored seperated inside <a/> tags.
            
            Ex: <a>San Jose</a>, <a>CA</>
        """
        a_elements = address.find_elements(By.TAG_NAME, 'a')

        street_addr = ""
        unit: str | None = None
        city = ""


        """
            Sometimes unit doesn't exist. Careful!
        """
        if a_elements and len(a_elements) < 3:
            for idx, elem in enumerate(a_elements):
                if idx == 0:
                    street_addr = elem.text
                if idx == 1:
                    city = elem.text
        else:
            for idx, elem in enumerate(a_elements):
                if idx == 0:
                    street_addr = elem.text
                if idx == 1:
                    unit = elem.text
                if idx == 2:
                    city = elem.text


        try:
            location = Location(id=uuid4(), unit=unit, street_addr=street_addr, city=city)
        except Exception as e:
            # Left as error to prevent total failure of script
            logger.error(f"Error occurred when constructing the location object. {e}")
            raise
        return location


    def parse_reviews(
        self,
        buis_id: UUID,
        page_reviews: list[WebElement]
    ):
        logger.debug(f"Begin parsing {len(page_reviews)} reviews...")
        for review in page_reviews:
            # Username. Possibly relevant in the future
            username = review.find_element(
                By.XPATH, ".//div/div[1]/div/div[1]/div/div/div[2]/div[1]/span/a"
            ).text

            # Rating information
            rating = review.find_element(
                By.XPATH, ".//div/div[2]/div/div[1]/span/div"
            ).get_attribute("aria-label")
            rating_parsed = re.search(r"(\d+)\s+star\s+rating", rating).group(1)

            # Get and set date variable
            date_posted: str = review.find_element(By.XPATH, ".//div/div[2]/div/div[2]/span").text

            text = None
            try:
                text = review.find_element(By.XPATH, ".//div/div[3]/p/span").text
            except Exception as e:
                logger.warning(f"Could not locate review comment on first pass..")
                pass
            if text == None:
                try:
                    text = review.find_element(By.XPATH, ".//div/div[4]/p/span").text
                except:
                    logger.error("No comment found, skipping review...")
                    continue

            if text and is_english(text):
                text = clean_text(text)
            else:
                continue

            try:
                review = Review(
                    id=uuid4(),
                    buis_id=buis_id,
                    username=username,
                    rating=float(rating_parsed),
                    text=text,
                    date_posted=date_posted,
                    images=None,
                )
            except Exception as e:
                logger.exception(f"Failed to construct review: {e}")
            logger.success("Created review")
            # WRITE the review to output file
            # logger.debug(f"Found review: {review.encode()}")
            self.create_or_append_review_csv(review=review)
        
