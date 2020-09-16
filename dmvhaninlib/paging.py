def get_pagination(curr_page, last_page):
    return [i for i in range(max(1, curr_page-2), min(last_page, curr_page+2)+1)]