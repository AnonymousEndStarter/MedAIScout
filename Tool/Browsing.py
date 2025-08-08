#!/usr/bin/env python3
from logging import getLogger
from math import log
from webbrowser import Chrome
from selenium import webdriver as WebDriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
import googlesearch
from settings import logger
import os
import re
import time
import settings
import csv
import requests
import bs4
import sys
from typing import Iterator

class browser:
    """
    browser Class to handle the selenium related operations
    """

    def __init__(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                opts = ChromeOptions()
                opts.add_argument('--ignore-ssl-errors=yes')
                opts.add_argument('--ignore-certificate-errors')
                opts.add_argument("--start-maximized")
                opts.add_argument("--headless")
                opts.add_argument("--no-sandbox")
                opts.add_argument("--disable-extensions")
                opts.add_argument("--disable-dev-shm-usage")
                opts.add_argument("--disable-gpu")
                opts.add_argument("--remote-debugging-port=9222")
                opts.add_argument("--disable-web-security")
                opts.add_argument("--disable-features=VizDisplayCompositor")
                
                logger.debug(f"Connecting to Selenium Server (attempt {attempt + 1})")
                
                # Increased timeout for connection
                self.driver = WebDriver.Remote(
                    command_executor=settings.SELENIUM_URL, 
                    options=opts,
                    keep_alive=True
                )
                
                # Set timeouts
                self.driver.set_page_load_timeout(60)
                self.driver.implicitly_wait(settings.TIMEOUT)
                
                logger.success("Connected to Selenium Server")
                time.sleep(2)  # Reduced pause time
                return
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to connect to Selenium after {max_retries} attempts")

    def get_google_search_results(self, query: str) -> Iterator[str]:
        """
        Searching for query in Google to get most relevant pages
        """
        logger.debug("Searching for {} in Google".format(query))
        query = query.strip()
        search_results = googlesearch.search(
            query, tld="com", pause=2)  # Reduced pause time
        logger.debug("Search Results Retrieved")
        return search_results

    def fetch_data(self) -> None:
        """
        Function to download the excel file from the FDA website using Selenium
        """
        if os.path.exists(settings.EXCEL_FILE):
            logger.info(f"Excel file already exists at {settings.EXCEL_FILE}, skipping download")
            return
            
        logger.info("Excel file not found, downloading from FDA website")
        
        try:
            self.driver.get(settings.FDA_URL)
            time.sleep(5)  # Wait for page load
            
            export_excel = WebDriverWait(self.driver, 20).until(
                lambda driver: driver.find_element(
                    By.XPATH, "/html/body/div[2]/div[1]/div/main/article/div/div[2]/div/div[1]/div[2]/div[2]/button"
                )
            )
            export_excel.click()
            logger.debug("Downloading Excel File")
            
            # Wait for download to complete with timeout
            timeout = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if 'Artificial Intelligence and Machine Learning (AIML)-Enabled Medical Devices FDA.xlsx' in os.listdir(settings.DOWNLOAD_DIR):
                    logger.debug("Excel File Downloaded")
                    return
                time.sleep(5)
                logger.debug("Waiting for download to complete")
            
            logger.error("Download timeout - file not found after 5 minutes")
            
        except Exception as e:
            logger.error(f"Error downloading Excel file: {str(e)}")

    def download_medicalfuturist_data(self) -> None:
        """
        Function to download the Medical Futurist data from the website
        """
        try:
            content = self.get_page(settings.MEDICAL_FUTURIST_URL)
            if content == "None":
                logger.error("Failed to get Medical Futurist page")
                return
                
            logger.debug("Retrieving Medical Futurist Data")
            soup = bs4.BeautifulSoup(content, 'html.parser')
            data_rows = soup.find_all('td', {'role': 'cell'})
            
            with open(settings.MEDICAL_FUTURIST_FILE, 'w', newline='', encoding='utf-8') as csv_file:
                csv_writer = csv.writer(csv_file)
                headers = ["Submission Number", "AI_Algo", "Name of device", "Desc"]
                csv_writer.writerow(headers)
                
                for i in range(0, len(data_rows), 10):
                    if i+5 < len(data_rows):
                        csv_writer.writerow([
                            data_rows[i+3].div.text if data_rows[i+3].div else "",
                            data_rows[i+5].div.text if data_rows[i+5].div else "",
                            data_rows[i].div.text if data_rows[i].div else "",
                            data_rows[i+2].div.text if data_rows[i+2].div else ""
                        ])
            logger.debug("Medical Futurist Data Retrieved")
            
        except Exception as e:
            logger.error(f"Error downloading Medical Futurist data: {str(e)}")

    def check_desc(self, query: str) -> bool:
        """
        Function to check whether the query is relevant to our search
        """
        result = False
        try:
            search_results = self.get_google_search_results(query)

            for i in range(min(settings.NO_SEARCH_RESULTS, 3)):  # Limit to 3 results
                page = next(search_results, None)
                if page is None:
                    logger.debug("No more pages to search")
                    break
                elif "fda.gov" in page or ".img" in page or ".pdf" in page:
                    logger.debug("Skipping FDA/image/pdf page")
                    continue
                    
                content = self.get_page(page)
                if content == "None":
                    continue
                    
                pattern = [
                    re.compile(r'(?i)machine\s*learning'),
                    re.compile(r'(?i)artificial\s*intelligence'),
                    re.compile(r'(?i)deep\s*learning'),
                    re.compile(r'(?i)neural\s*network'),
                    re.compile(r'(?i)classification\s*methods'),
                    re.compile(r'(?i)classifier'),
                    re.compile(r'(?i)computer\s*vision')
                ]
                
                for p in pattern:
                    matching = p.search(content)
                    if matching:
                        logger.debug(str(matching)+" found for "+query)
                        return True
                        
        except Exception as e:
            logger.error(f"Error in check_desc: {str(e)}")
            result = True
            
        return result

    def check_link(self, url: str) -> bool:
        """
        Check whether a link is valid
        """
        logger.debug("Checking if {} is valid".format(url))
        try:
            request = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if request.status_code == 404:
                logger.error("Invalid URL - 404")
                return False
            logger.debug("Valid URL")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return False

    def get_page(self, url: str) -> str:
        """
        Fetches a page using Selenium
        """
        if not self.check_link(url):
            return "None"
            
        logger.debug("Retrieving page {}".format(url))
        try:
            self.driver.get(url)
            time.sleep(3)  # Reduced wait time
            return self.driver.page_source
            
        except TimeoutException:
            logger.error("Unable to retrieve page because timeout")
            return "None"
            
        except WebDriverException as e:
            logger.error(f"WebDriverException: {str(e)}")
            try:
                logger.debug("Reinitializing Selenium Server")
                self.driver.quit()
                time.sleep(10)
                self.__init__(max_retries=2)  # Reduced retries for reinit
                return "None"
            except:
                logger.error("Failed to reinitialize")
                return "None"

    def __del__(self):
        logger.debug("Closing Selenium Server")
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                logger.debug("Selenium Server Closed")
        except Exception as e:
            logger.error(f"Unable to close Selenium Server: {str(e)}")
            pass