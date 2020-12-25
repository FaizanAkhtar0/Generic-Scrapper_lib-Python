import random
import requests
from itertools import cycle

from bs4 import BeautifulSoup
from fake_useragent import UserAgent, FakeUserAgentError


# noinspection PyComparisonWithNone
class Scrapper:
    __proxy_url = 'https://www.sslproxies.org/'
    __index_separators = ['=', '-', '/', '?', '?=']

    def __init__(self, Web_URI, pagination_route_syntax, page_numbers=None, deprecate_later_syntax=False):
        """
        >>> Initializes the basic requirements for scrapping.

        :param Web_URI: Link to web page that is to be scrapped.
        :param pagination_route_syntax: Route Syntax defined by the web that is used to navigate to next page i.e:('page/1', 'page=1').
        :param page_numbers: {List: [starting, ending] -> Range OR List: [1, 3, 6, ...] -> Selective} Number of pages to be scrapped from the website. By default page_numbers=None.
        :param deprecate_later_syntax: Enable this to cut off the paths following after the "pagination_route_syntax" in original URI. deprication may be helpful in cases where paths after 'pagination_syntax' are invalid for next pages.
        In case page_numbers=None, deprecation is useless as provided link is used for scrapping.
        """
        self._WEB_URI = Web_URI
        self._PAGE_NO = page_numbers
        self._ROUTE_SYNTAX = pagination_route_syntax
        self._DEPRECATION = deprecate_later_syntax

    def set_separator(self, separator):
        """Sets custom separators for different kinds of pagination_syntax

           >>> for custom separators i.e:('page?=1', 'page/id=1') -> ['?=', '/id=']
        """
        if separator != None and separator != '':
            if separator not in self.__index_separators:
                self.__index_separators.append(separator)

    def __get_page_index_in_str(self):
        """
        >>> Returns the index of the starting character of the page_number provided in the original link.

        >>> This index is then used to override the provided page_number in link with the given set of page_numbers
        >>> initialized during the object creation.
        """

        fixed_link_ending_index = self._WEB_URI.index(self._ROUTE_SYNTAX)
        route_length = 0
        for item in Scrapper.__index_separators:
            separated_route = self._ROUTE_SYNTAX.split(item)
            if separated_route.__len__() == 1:
                continue
            else:
                route_length = separated_route[0].__len__() + 1
                self._PRESENT_PAGE_NO = separated_route[1]
                break

        if route_length != 0:
            return fixed_link_ending_index + route_length
        else:
            return None

    def construct_next_URIS(self):
        """
        >>> Constructs the URLS for scrapping with in the specified range or list specified while object construction."""
        start_index = self.__get_page_index_in_str()
        ending_index = (self._WEB_URI.index(self._PRESENT_PAGE_NO) + self._PRESENT_PAGE_NO.__len__())

        if self._DEPRECATION and self._PAGE_NO != None:
            if self._PAGE_NO.__len__() > 2:
                return [('' + self._WEB_URI[:start_index] + str(number)) for number in
                        self._PAGE_NO]
            else:
                return [('' + self._WEB_URI[:start_index] + str(number)) for number in
                        range(self._PAGE_NO[0], self._PAGE_NO[1] + 1, 1)]
        elif self._PAGE_NO != None:
            if self._PAGE_NO.__len__() > 2:
                return [('' + self._WEB_URI[:start_index] + str(number) + self._WEB_URI[ending_index:]) for number in
                        self._PAGE_NO]
            else:
                return [('' + self._WEB_URI[:start_index] + str(number) + self._WEB_URI[ending_index:]) for number in
                        range(self._PAGE_NO[0], self._PAGE_NO[1] + 1, 1)]
        else:
            return [self._WEB_URI]

    def __proxies_pool(self):
        """
        >>> Creates a proxies by using the specified self.__proxy_url
        :return: list(str('IP:PORT'), ...)
        """
        with requests.Session() as res:
            proxies_page = res.get(self.__proxy_url)

        soup = BeautifulSoup(proxies_page.content, 'html.parser')
        proxies_table = soup.find(id='proxylisttable')

        proxies = []
        for row in proxies_table.tbody.find_all('tr'):
            proxies.append('{}:{}'.format(row.find_all('td')[0].string, row.find_all('td')[1].string))
        return proxies

    def __random_header(self):
        """
        >>> Creates a random header based on equal probability distribution
        :return: dict{'User-Agent': value, 'Accept': value}
        """
        accepts = {"Firefox": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                   "Safari, Chrome": "application/xml,application/xhtml+xml,text/html;q=0.9, text/plain;q=0.8,image/png,*/*;q=0.5"}
        try:
            # Getting a user agent using the fake_useragent package
            ua = UserAgent()
            if random.random() > 0.5:
                self.__random_user_agent = ua.chrome
            else:
                self.__random_user_agent = ua.firefox
        except FakeUserAgentError  as error:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
                "Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1"]
            self.__random_user_agent = random.choice(user_agents)
        finally:
            valid_accept = accepts['Firefox'] if self.__random_user_agent.find('Firefox') > 0 else accepts['Safari, Chrome']
            headers = {"User-Agent": self.__random_user_agent, "Accept": valid_accept}
        return headers

    def __create_pools(self):
        """
        >>> Creates proxies_pool and headers_pool
        :return: tuple(list(iterable), list(iterable))
        """
        proxies = self.__proxies_pool()
        headers = [self.__random_header() for index in range(len(proxies))]

        proxies_pool = cycle(proxies)
        headers_pool = cycle(headers)
        return proxies_pool, headers_pool

    def __get_pages_response(self, page_uris):
        """
        >>> Returns a response Generator object for the provided page list URIS."""
        proxie_pool, header_pool = self.__create_pools()
        for uri in page_uris:
            current_proxy = next(proxie_pool)
            current_header = next(header_pool)

            print(f"IP: {current_proxy} : HEADER: {current_header}")

            with requests.session() as req:
                try:
                    yield req.get(uri,
                                  proxies={"http": current_proxy, "https": current_proxy},
                                  headers=current_header, timeout=30)
                except:
                    print(f"Server: {current_proxy} - timed out at 30secs")
                    continue

    def get_content(self):
        """
        >>> Returns the content Generator for provided response Generator object."""
        for response in self.__get_pages_response(self.construct_next_URIS()):
            yield response.content.decode("utf-8")

