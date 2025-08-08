#!/usr/bin/env python3
# import csv, pandas as pd
# import settings
# import csv
# import requests
# import time
# from settings import print_1

# #!/usr/bin/env python3
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options as ChromeOptions
# from selenium.webdriver.support.wait import WebDriverWait
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException, WebDriverException

# # from selenium_stealth import stealth
# # from googlesearch import search
# from settings import print_1
# from bs4 import BeautifulSoup
# from os import listdir, system
# import re, time, settings, csv, requests

# import Model

from loguru._defaults import LOGURU_FORMAT
print(LOGURU_FORMAT)

# from gpt4all import GPT4All
# model = GPT4All("wizardlm-13b-v1.2.Q4_0.gguf")
# with model.chat_session():

#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == "exit":
#             break
#         output = model.generate(user_input)
#         print(output)
# url = "http://www.ijpe-online.com/EN/Y2021/V17/I8/711"
# print_1("Checking if {} is valid".format(url))
# try:
#     request = requests.get(url,timeout=settings.TIMEOUT)
#     if request.status_code == 404:
#         print_1("Invalid URL")
# except requests.exceptions.Timeout:
#     print_1("Timeout")
# except requests.exceptions.ConnectionError:
#     print_1("Connection Timeout")
# except requests.exceptions.InvalidURL:
#     print_1("Invalid URL")

# print_1("Valid URL")
# Use a pipeline as a high-level helper
# Load model directly
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
# import undetected_chromedriver as uc
# options = uc.ChromeOptions()
# options.arguments.extend(["--no-sandbox", "--disable-setuid-sandbox"])     # << this
# driver = uc.Chrome(options)
# driver.get("https://www.google.com")

# question_5 = "Does this talk about attacks on AI techniques using Image processing?"
# boolean_model = "nfliu/roberta-large_boolq"
# context = "In recent years, technology has advanced to the fourth industrial revolution (Industry 4.0), where the Internet of things (IoTs), fog computing, computer security, and cyberattacks have evolved exponentially on a large scale. The rapid development of IoT devices and networks in various forms generate enormous amounts of data which in turn demand careful authentication and security. Artificial intelligence (AI) is considered one of the most promising methods for addressing cybersecurity threats and providing security. In this study, we present a systematic literature review (SLR) that categorize, map and survey the existing literature on AI methods used to detect cybersecurity attacks in the IoT environment. The scope of this SLR includes an in-depth investigation on most AI trending techniques in cybersecurity and state-of-art solutions. A systematic search was performed on various electronic databases (SCOPUS, Science Direct, IEEE Xplore, Web of Science, ACM, and MDPI). Out of the identified records, 80 studies published between 2016 and 2021 were selected, surveyed and carefully assessed. This review has explored deep learning (DL) and machine learning (ML) techniques used in IoT security, and their effectiveness in detecting attacks. However, several studies have proposed smart intrusion detection systems (IDS) with intelligent architectural frameworks using AI to overcome the existing security and privacy challenges. It is found that support vector machines (SVM) and random forest (RF) are among the most used methods, due to high accuracy detection another reason may be efficient memory. In addition, other methods also provide better performance such as extreme gradient boosting (XGBoost), neural networks (NN) and recurrent neural networks (RNN). This analysis also provides an insight into the AI roadmap to detect threats based on attack categories. Finally, we present recommendations for potential future investigations. "
# tokenizer = AutoTokenizer.from_pretrained(boolean_model)
# model = AutoModelForSequenceClassification.from_pretrained(boolean_model)
# input_text = f"{context} Question: {question_5}"
# input_ids = tokenizer.encode(input_text, return_tensors="pt")
# output = model(input_ids)
# logits = output.logits
# probabilities = logits.softmax(dim=1)
# predicted_label = "yes" if probabilities[0, 1] > probabilities[0, 0] else "no"
# settings.print_1(predicted_label)


"""
45.9 ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device: '/usr/local/lib/python3.10/dist-packages/tensorflow/include/external/llvm-project/mlir/_virtual_includes/X86VectorIncGen/mlir/Dialect'
"""
