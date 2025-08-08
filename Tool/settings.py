# Description: This file contains all the settings for the tool
import os
import sys
from loguru import logger
# Number of papers to be scraped from google scholar

TIMEZONE = 'Asia/Kolkata'
NUMBER_OF_PAPERS = 5

# Number of keywords needed from the pdf

NUMBER_OF_KEYWORDS = 5

# Paths

DATA_DIR = "/mnt/Data/"
PDF_DIR = "/mnt/Data/Summary_docs/"
CSV_FILE = "/mnt/Data/Analysed_Data.csv"
EXCEL_FILE = "/mnt/Data/Downloads/Artificial Intelligence and Machine Learning (AIML)-Enabled Medical Devices FDA.xlsx"
MEDICAL_FUTURIST_FILE = "/mnt/Data/medicalfuturist_data.csv"
REPORT_DIR = "/mnt/Data/Report/"

# Models used

NLP_MODEL = "distilbert-base-uncased-distilled-squad"
# NLP_MODEL = "deepset/roberta-base-squad2" # Not used
# NLP_MODEL = "deepset/roberta-large-squad2" # Not used
# NLP_MODEL = "deepset/bert-large-uncased-whole-word-masking-squad2" # not performing well
LLM_MODEL = "wizardlm-13b-v1.2.Q4_0.gguf"
# LLM_MODEL = "gpt4all-13b-snoozy-q4_0.gguf" Decent But not that great
# LLM_MODEL = "orca-2-13b.Q4_0.gguf" # Not that great
# LLM_MODEL = "nous-hermes-llama2-13b.Q4_0.gguf" # Bad

# Main Questions

QUESTION_1 = "What are the algorithms used?"
QUESTION_2 = "What are the techniques used?"
QUESTION_3 = "What are machine learning techniques used?"
QUESTION_4 = "What is the input format to the device?"
QUESTION_5 = "Does this talk about attacks on AI techniques?"

# URLs

FDA_URL = "https://www.fda.gov/medical-devices/software-medical-device-samd/artificial-intelligence-and-machine-learning-aiml-enabled-medical-devices"
DOWNLOAD_URL = "https://www.accessdata.fda.gov/cdrh_docs/pdf"
MEDICAL_FUTURIST_URL = "https://medicalfuturist.com/fda-approved-ai-based-algorithms/"

# Selenium Config and other Search Config

SELENIUM_URL = "http://browser:4444/wd/hub"
NO_SEARCH_RESULTS = 2
PAUSE_TIME = 3
DOWNLOAD_DIR = "/mnt/Data/Downloads"
TIMEOUT = 100

# LOGGING ENVIRONMENT

# DEBUG, INFO, WARNING, ERROR, CRITICAL  for loguru logging
LOG_LEVEL_CONSOLE = "DEBUG"
LOG_LEVEL_FILE = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL  for loguru logging
LOG_FILE = "/mnt/Data/Logs/Logs.log"
LOG_CONSOLE_FORMAT = "<green>{time: HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
LOG_FILE_FORMAT = "{time: HH:mm:ss} | {level: <8}| {name}:{function}:{line} - {message}"
LOG_ROTATION = "40 MB"

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL_CONSOLE,
           format=LOG_CONSOLE_FORMAT, colorize=True, backtrace=True)
logger.add(LOG_FILE, level=LOG_LEVEL_FILE, format=LOG_FILE_FORMAT,
           colorize=True, backtrace=True, rotation=LOG_ROTATION)

OPEN_AI_API_KEY = os.environ.get("OPEN_AI_API_KEY")
