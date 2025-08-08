#!/usr/bin/env python3
import fitz
import re


class Reader:
    """
    A class for reading and extracting information from PDF files.
    """

    def __init__(self, path: str):
        """
        Initializes the Reader class with the given PDF file path.

        Args:
            path (str): The path to the PDF file.

        Attributes:
            path (str): The path to the PDF file.
            reader (fitz.Document): The PDF document object.
        """
        self.path = path
        self.reader = fitz.open(path)

    def page_nos(self) -> int:
        """
        Returns the total number of pages in the PDF.

        Returns:
            int: The total number of pages in the PDF.
        """
        return len(self.reader.pages)

    def extract_paragraphs(self) -> list[str]:
        """
        Extracts and returns a list of paragraphs from the PDF.

        Returns:
            list[str]: A list of paragraphs extracted from the PDF.
        """
        paragraphs = []
        for i in range(2, len(self.reader)):
            page = self.reader.load_page(i)
            paragraph = ""
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if b["type"] == 0:
                    for l in b["lines"]:
                        if (
                            ("Page" in l["spans"][0]["text"])
                            or ("Premarket" in l["spans"][0]["text"])
                            or ("page" in l["spans"][0]["text"])
                        ):
                            continue
                        cleaned_text = self.__clean_paragraph(
                            l["spans"][0]["text"])
                        if cleaned_text != "":
                            paragraph += cleaned_text.strip() + "\n"
            paragraphs.append(paragraph)
        return paragraphs

    # List of rows of tables obtained from the pdf
    def extract_tables(self) -> list[list[str]]:
        """
        Extracts and returns a list of rows of tables from the PDF.

        Returns:
            list[list[str]]: A list of rows of tables extracted from the PDF.
        """
        tables = []
        for i in range(2, len(self.reader)):
            page = self.reader.load_page(i)
            tables += page.find_tables()  # list of tables on page i
        for i in range(len(tables)):
            tables[i] = tables[i].extract()
            for j in tables[i]:
                for k in range(len(j)):
                    j[k] = self.__clean_paragraph(j[k])
        return tables

    def __clean_paragraph(self, paragraph) -> str:
        """
        Cleans the given paragraph by removing non-ASCII characters, specific substrings, punctuation, and grammar-related words.

        Args:
            paragraph (str): The paragraph to be cleaned.

        Returns:
            str: The cleaned paragraph.
        """
        if paragraph == None or paragraph.strip() == "":
            return ""
        paragraph = self.__remove_non_ascii(paragraph)
        paragraph = self.__remove_sub_no(paragraph)
        paragraph = self.__remove_punc(paragraph)
        paragraph = self.__remove_grammar(paragraph)
        # add more cleaning functions here
        return paragraph

    def __remove_punc(self, text: str) -> str:
        """
        Removes punctuation from the given text.

        Args:
            text (str): The text to be cleaned.

        Returns:
            str: The cleaned text without punctuation.
        """
        text = text.replace("\n", " ")
        return re.sub("[,;:.\n\t\r)(*%]+", " ", text)

    def __remove_grammar(self, text: str) -> str:
        """
        Removes specific grammar-related words from the given text.

        Args:
            text (str): The text to be cleaned.

        Returns:
            str: The cleaned text without grammar-related words.
        """
        text = re.sub(r"the", " ", text)
        text = re.sub(r"an", " ", text)
        return text

    def __remove_sub_no(self, text: str) -> str:
        """
        Removes specific substrings from the given text.

        Args:
            text (str): The text to be cleaned.

        Returns:
            str: The cleaned text without specific substrings.
        """
        return re.sub(r"[Kk][0-9]+", " ", text)

    def __remove_non_ascii(self, text: str) -> str:
        """
        Removes non-ASCII characters from the given text.

        Args:
            text (str): The text to be cleaned.

        Returns:
            str: The cleaned text without non-ASCII characters.
        """
        return re.sub(r"[^\x00-\x7F]", " ", text)
