#!/usr/bin/env python3
import PyPDF2
import Table_Reader
import re
import settings


class Reader:

    def __init__(self, path):
        self.path = path
        self.reader = PyPDF2.PdfReader(path)

    def page_nos(self):

        return len(self.reader.pages)

    def page(self, pg_no):

        return self.reader.pages[pg_no].extract_text()

    def extract_paragraph(self, pg_no):

        paragraphs = []
        page_text = self.page(pg_no)
        page_paragraphs = page_text.split("\n\n")
        for paragraph in page_paragraphs:
            lines = paragraph.split("\n")
            for line in lines:
                words = line.split()
                line = ""
                for word in words:
                    if self.is_Sub_no(word):
                        settings.print_1(word)

            paragraph = "".join(lines)
            paragraphs.append(paragraph)
        return paragraphs

    def is_title(self, paragraph):

        title_pattern = r"^[A-Z][A-Za-z]+"
        return re.match(title_pattern, paragraph)

    def is_Sub_no(self, word):

        sub_no_pattern = r"K[0-9]+"
        return re.search(sub_no_pattern, word)

    def extract_table(self, pg_no):

        table = Table_Reader.tables(self.path, pg_no)
        return table

    def remove_non_ascii(text):

        return re.sub(r"[^\x00-\x7F]", " ", text)


# For Testing purposes
# pdf=Reader("./Summary_docs/K220851.pdf")
# pdf.extract_paragraph(8)
# Add input sanity functions to clean the pdf
