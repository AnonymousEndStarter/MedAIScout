# usr/bin/python3

import camelot


# Access individual tables if there are multiple


class Table_Reader:
    def __init__(self):
        pass

    def tables(self, path, pg_no):
        tables = camelot.read_pdf(path, pages=pg_no)
        for i in range(len(tables)):
            tables.to_csv("table_{}_{}.csv".format(path, pg_no))
        if len(tables) == 0:
            return None
        return tables
