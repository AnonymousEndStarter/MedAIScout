#!/usr/bin/env python3

import scholarly
import settings
import time
import sys  # , requests, proxyscrape
from loguru import logger


# This code section is to make use of available proxies for scraping more quicker without getting blocked
# Fairly simple code which checks whether a proxy (in this case fetched through free proxies list available online) is available and if so added to scholarly objects
# pg = scholarly.ProxyGenerator()

# def get_random_proxy():
#     collector = proxyscrape.create_collector('default','http')
#     proxy_list = collector.get_proxy()
#     if proxy_list == None:
#         settings.settings.print_1("No proxy found")
#         return None
#     return "http://"+proxy_list.host+":"+proxy_list.port
# def make_request(url, proxy):
#     try:
#         response = requests.get(url, proxies=proxy, timeout=5)
#         response.raise_for_status()
#         settings.settings.print_1(f"Request successful. Status Code: {response.status_code}")
#         return response.text
#     except requests.exceptions.RequestException as e:
#         settings.settings.print_1(f"Request failed. Error: {e}")
#         return None

# url = 'https://scholar.google.com'
# max_attempts = 10  # Adjust as needed

# for attempt in range(max_attempts):
#     proxy = get_random_proxy()

#     if proxy:
#         result = make_request(url, proxy)

#         if result:
#             success = True
#             pg.SingleProxy(http="http://"+proxy.host+":"+proxy.port)
#             if success:
#                 scholarly.use_proxy(pg)
#             else:
#                 settings.settings.print_1("Proxy failed")
#                 exit(0)
#             break  # Break the loop if the request is successful
#     else:
#         break


class scholarly_scraper:
    """
    A class for scraping scholarly papers from Google Scholar.
    """

    def __init__(self):
        logger.remove()
        logger.add(sys.stderr, level=settings.LOG_LEVEL_CONSOLE,
                   format=settings.LOG_CONSOLE_FORMAT, colorize=True, backtrace=True)
        logger.add(settings.LOG_FILE, level=settings.LOG_LEVEL_FILE, format=settings.LOG_FILE_FORMAT,
                   colorize=True, backtrace=True, rotation=settings.LOG_ROTATION)

    def complete_info(self, search_query) -> list:
        """
        Searches for papers through Google Scholar and returns a list of complete information for each paper.

        Parameters:
            search_query (SearchQuery): An instance of the SearchQuery class for searching papers.

        Returns:
            list: A list of complete information for each paper.
        """
        logger.debug("Searching for papers through google scholar")
        complete_info = []
        if search_query == None:
            return complete_info
        for i in range(settings.NUMBER_OF_PAPERS):
            article = next(search_query, None)
            time.sleep(settings.PAUSE_TIME)
            if article == None:
                break
            complete_info.append(article)
        logger.debug("Search complete")
        return complete_info

    def __check_survey(self, paper) -> bool:
        """
        Checks if a paper is a survey paper.

        Parameters:
            paper (dict): A dictionary representing a paper with 'bib' and 'abstract' keys.

        Returns:
            bool: True if the paper is a survey paper, False otherwise.
        """
        if paper["bib"]["title"].lower().find("survey") != -1:
            return True
        elif paper["bib"]["abstract"].lower().find("survey") != -1:
            return True
        return False

    def get_info(self, query) -> list[list[str]]:
        """
        Scrapes scholarly papers from Google Scholar based on the given query and returns a list of lists containing paper titles, abstracts, and URLs.

        Parameters:
            query (str): The query to search for papers.

        Returns:
            list[list[str]]: A list of lists containing paper titles, abstracts, and URLs.
        """
        extract = []
        try:

            search_query = scholarly.scholarly.search_pubs(query)
            complete_info = self.complete_info(search_query)
            i = -1
            while (
                len(extract) < min(settings.NUMBER_OF_PAPERS, len(complete_info))
                and i < len(complete_info) - 1
            ):
                i = i + 1
                if self.__check_survey(complete_info[i]):
                    logger.debug("Survey paper found, Skipping")
                    continue
                # entry = "{0}:  {1}:   {2}\n".format(complete_info[i]['bib']['title'],complete_info[i]['bib']['abstract'],complete_info[i]['pub_url'])
                entry = [
                    complete_info[i]["bib"]["title"],
                    complete_info[i]["bib"]["abstract"],
                    complete_info[i]["pub_url"],
                ]
                extract.append(entry)
                logger.debug(entry)

        except Exception as e:
            logger.error(e)
            logger.error("No results found")
        return extract
