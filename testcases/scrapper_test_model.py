from models.scrapper import Scrapper

# Test Case
#
# Use whatever web you want to test

full_link = 'https://craftcms.stackexchange.com/questions/20745/custom-routes-with-url-parameters-and-pagination'
pagination_syntax = 'questions/20745'
pages = [20745, 20755] # can also use specific selective pages like [20745, 20750, 20755]


scrapper = Scrapper(full_link, pagination_syntax, page_numbers=pages, deprecate_later_syntax=True)
"""
    :param: deprecate_later_syntax: When set 'Ture' removes the route following the pagination_syntax 
            for next generated urls.
"""

for link in scrapper.construct_next_URIS():
    print(link)

#
# # for custom separators i.e:('page?=1', 'page/id=1')
# scrapper.set_separator("?=")
# scrapper.set_separator("/id=")
#

for content in scrapper.get_content():
    print(content)

