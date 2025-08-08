#!/usr/bin/env python3
import pandas as pd
import transformers
import csv
import time
import os
import re
import sys
import traceback
from typing import Optional, Tuple, List, Union

try:
    import settings
    import Browsing
    import PDF_Reader_2
    import Scholar_scraper
    import Helper_functions
    import LLM
    from settings import logger
except ImportError as e:
    print(f"Critical import error: {e}")
    sys.exit(1)

# For logger to recognize correct timezone
try:
    os.environ['TZ'] = getattr(settings, 'TIMEZONE', 'UTC')
    time.tzset()
except Exception as e:
    print(f"Timezone setup failed: {e}")

def safe_file_operations():
    """Initialize file operations with error handling and ensure directory exists"""
    try:
        # Ensure the directory exists
        csv_dir = os.path.dirname(settings.CSV_FILE)
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
            logger.info(f"Created directory: {csv_dir}")
        
        # Create/open CSV file
        csvfile = open(settings.CSV_FILE, "w", newline="", encoding='utf-8')
        fieldnames = [
            "Submission Number",
            "Device", 
            "Company",
            "Category",
            "Date of Approval",
            "Level 1 - Algorithms Found",
            "Level 2 - Filtered Keywords",
            "Level 4 - Input Format",
            "Alt Keywords Level 2",
            "Security Attacks Found",
        ]
        writer = csv.writer(csvfile)
        writer.writerow(fieldnames)
        csvfile.flush()  # Ensure header is written immediately
        logger.success(f"CSV file initialized: {settings.CSV_FILE}")
        return csvfile, writer
    except Exception as e:
        logger.error(f"Failed to initialize CSV file: {e}")
        raise

def safe_data_loading():
    """Load input data with error handling"""
    try:
        data = pd.read_excel(settings.EXCEL_FILE)
        if data.empty:
            raise ValueError("Excel file is empty")
        logger.success(f"Loaded {len(data)} records from Excel file")
    except Exception as e:
        logger.error(f"Failed to load Excel file: {e}")
        raise
    
    try:
        medfut_data = pd.read_csv(
            settings.MEDICAL_FUTURIST_FILE,
            skiprows=[0],
            names=["Submission Number", "AI_Algo", "Name of device", "Desc"],
            encoding='utf-8'
        )
        logger.info(f"Loaded {len(medfut_data)} records from Medical Futurist file")
    except Exception as e:
        logger.error(f"Failed to load Medical Futurist file: {e}")
        medfut_data = pd.DataFrame(columns=["Submission Number", "AI_Algo", "Name of device", "Desc"])
    
    return data, medfut_data

# Initialize file operations and data loading
csvfile, writer = safe_file_operations()
data, medfut_data = safe_data_loading()

def fetch_medfut_data(index: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetches the AI algorithm and description from the Medical Futurist dataset with error handling"""
    try:
        algorithm = None
        description = None
        
        if medfut_data.empty:
            logger.warning("Medical Futurist dataset is empty")
            return algorithm, description
            
        medfut_row = medfut_data[medfut_data["Submission Number"] == index]
        
        if not medfut_row.empty:
            logger.success("Medical Futurist Data Found")
            medfut_row = medfut_row.iloc[0]
            description = str(medfut_row.get("Desc", "")).strip() if pd.notna(medfut_row.get("Desc")) else None
            
            ai_algo = medfut_row.get("AI_Algo", "Not Available")
            logger.debug(f"AI Algorithm: {ai_algo}")
            
            if str(ai_algo) == "Not Available" or pd.isna(ai_algo):
                logger.warning("No AI Algorithm found")
            else:
                logger.debug(f"The algorithm is {ai_algo}")
                algorithm = str(ai_algo).strip()
        else:
            logger.warning("No Data found in Medical Futurist")
            
    except Exception as e:
        logger.error(f"Error fetching Medical Futurist data for {index}: {e}")
        
    return algorithm, description

def process_document(index: str) -> Tuple[List[str], List[str]]:
    """Process the document with comprehensive error handling and ensure complete analysis"""
    try:
        path = f"{settings.PDF_DIR}{index}.pdf"
        
        if not os.path.exists(path):
            logger.error(f"PDF file not found: {path}")
            return ["File not found"], ["No search results available"]
        
        logger.info(f"Processing document: {index}")
        
        # Step 1: Fetch additional data
        algorithm, description = fetch_medfut_data(index)
        
        # Step 2: Extract PDF content
        try:
            pdf = PDF_Reader_2.Reader(path)
            pages = pdf.extract_paragraphs()
            logger.debug(f"Extracted {len(pages)} paragraphs from PDF")
        except Exception as e:
            logger.error(f"PDF extraction failed for {index}: {e}")
            pages = []
        
        if description:
            pages.append(description)
            logger.debug("Added Medical Futurist description to pages")
        
        if not pages:
            logger.warning(f"No content extracted from {index}")
            return ["No content extracted"], ["No search results available"]
        
        # Step 3: Level 1 Analysis
        try:
            logger.info("Starting Level 1 Analysis...")
            all_answers = globals()['Analyser_1'].level_1(pages)
            logger.success(f"Level 1 completed with {len(all_answers)} results")
        except Exception as e:
            logger.error(f"Level 1 analysis failed for {index}: {e}")
            all_answers = []
        
        # Step 4: Add algorithm if found in Medical Futurist
        if algorithm and all_answers:
            try:
                if not Helper_functions.check_presence(algorithm, all_answers):
                    all_answers.insert(0, (1.0, algorithm))
                    logger.debug(f"Added Medical Futurist algorithm: {algorithm}")
            except Exception as e:
                logger.error(f"Algorithm insertion failed: {e}")
        
        logger.debug(f"All answers: {all_answers}")
        
        # Step 5: Level 2 Alternative Analysis (LLM filtering)
        try:
            logger.info("Starting Level 2 Alternative Analysis...")
            alt_keywords = globals()['Analyser_1'].level_2_alt(all_answers) if all_answers else []
            logger.success(f"Level 2 Alt completed with {len(alt_keywords)} keywords")
        except Exception as e:
            logger.error(f"Level 2 alt analysis failed: {e}")
            alt_keywords = []
        
        # Step 6: Level 2 Analysis (Browser validation)
        try:
            logger.info("Starting Level 2 Analysis...")
            filtered_answer = globals()['Analyser_1'].level_2(all_answers) if all_answers else []
            logger.success(f"Level 2 completed with {len(filtered_answer)} filtered results")
        except Exception as e:
            logger.error(f"Level 2 analysis failed: {e}")
            filtered_answer = []
        
        # Step 7: Combine results for Level 3
        combined_answer = filtered_answer.copy()
        for answer in alt_keywords:
            combined_answer.append((0.9, answer))
        
        # Step 8: Level 3 Analysis (Paper search)
        try:
            logger.info("Starting Level 3 Analysis...")
            all_papers = globals()['Analyser_1'].level_3(combined_answer) if combined_answer else []
            logger.success(f"Level 3 completed")
        except Exception as e:
            logger.error(f"Level 3 analysis failed: {e}")
            all_papers = []
        
        # Step 9: Level 4 Analysis (Attack classification)
        try:
            logger.info("Starting Level 4 Analysis...")
            attack_papers, rejections = globals()['Analyser_1'].level_4(all_papers) if all_papers else ([], [])
            logger.success(f"Level 4 completed")
        except Exception as e:
            logger.error(f"Level 4 analysis failed: {e}")
            attack_papers, rejections = [], []
        
        # Step 10: Compile results
        try:
            results = globals()['Analyser_1'].return_results()
            
            # Format alternative keywords
            alt_keywords_string = "\n".join([f"{i+1}. {keyword}" for i, keyword in enumerate(alt_keywords)])
            if not alt_keywords_string:
                alt_keywords_string = "No alternative keywords found"
            
            # Ensure we have 4 result fields (Level 1, Level 2, Level 4, Alt Keywords)
            while len(results) < 3:
                results.append("No data found")
            
            results.append(alt_keywords_string)
            
        except Exception as e:
            logger.error(f"Results compilation failed: {e}")
            results = ["Error in analysis", "Error in analysis", "Error in analysis", "No alternative keywords found"]
        
        # Step 11: Process search results
        try:
            search_results = process_search_results(attack_papers, filtered_answer)
            if rejections:
                search_results.append("Rejected Papers:")
                search_results.extend(process_search_results(rejections, filtered_answer))
            
            if not search_results:
                search_results = ["No security vulnerabilities found"]
                
        except Exception as e:
            logger.error(f"Search results processing failed: {e}")
            search_results = ["Error processing search results"]
        
        logger.success(f"Document processing completed for {index}")
        return results, search_results
        
    except Exception as e:
        logger.error(f"Document processing failed for {index}: {e}")
        logger.error(traceback.format_exc())
        return ["Processing failed"], ["No search results available"]

def process_search_results(results: List, answers: List[Tuple[float, str]]) -> List[str]:
    """Process the search results with error handling"""
    try:
        if not results or not answers:
            return []
        
        search_results = []
        prefix = [
            "Security Attacks on ",
            "Inference time attacks on ", 
            "Training time attacks on ",
        ]
        
        for i in range(len(results)):
            if i >= len(prefix):
                break
            for j in range(len(results[i])):
                if j >= len(answers) or not results[i][j]:
                    continue
                
                temp = [f"{prefix[i]}{answers[j][1]}"]
                for k in range(len(results[i][j])):
                    if results[i][j][k] and len(results[i][j][k]) > 0:
                        temp.append(" ".join(str(x) for x in results[i][j][k]))
                
                if len(temp) > 1:  # Only add if we have actual content
                    search_results.append("\n".join(temp))
        
        return search_results
        
    except Exception as e:
        logger.error(f"Error processing search results: {e}")
        return ["Error processing search results"]

def create_row(index: str, row: pd.Series) -> bool:
    """Creates a row in the csv file with error handling and ensures data is written"""
    try:
        logger.info(f"Creating CSV row for {index}...")
        
        # Process the document
        results, search_results = process_document(index)
        
        # Build the CSV row
        csv_row = [
            str(row.get("Submission Number", index)),
            str(row.get("Device", "Unknown Device")),
            str(row.get("Company", "Unknown Company")),
            str(row.get("Panel (lead)", "Unknown Category")),
            str(row.get("Date of Final Decision", "Unknown Date")),
        ]
        
        # Add analysis results (ensure we have exactly 4 result fields)
        for i in range(4):
            if i < len(results):
                # Clean and format the result
                result_str = str(results[i]).replace('\n', ' | ').replace('\r', '')
                csv_row.append(result_str)
            else:
                csv_row.append("No data available")
        
        # Add search results (combine all into one field)
        if search_results:
            combined_attacks = " || ".join([str(sr).replace('\n', ' | ').replace('\r', '') for sr in search_results])
            csv_row.append(combined_attacks)
        else:
            csv_row.append("No security attacks found")
        
        # Write to CSV
        logger.info(f"Writing row to CSV for {index}")
        writer.writerow(csv_row)
        csvfile.flush()  # Force write to disk
        
        logger.success(f"✅ Successfully written {index} to CSV")
        print(f"✅ Row created for {index} - Data saved to {settings.CSV_FILE}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create row for {index}: {e}")
        logger.error(traceback.format_exc())
        
        # Write error row to maintain CSV structure
        try:
            error_row = [
                str(index), 
                "Error", 
                "Error", 
                "Error", 
                "Error", 
                f"Processing failed: {str(e)[:100]}", 
                "Error in analysis", 
                "Error in analysis", 
                "Error in analysis",
                "No attacks found due to processing error"
            ]
            writer.writerow(error_row)
            csvfile.flush()
            logger.warning(f"⚠️ Error row written for {index}")
        except Exception as write_error:
            logger.error(f"Failed to write error row: {write_error}")
        
        return False

class Model:
    """Enhanced Model class with error handling"""

    def __init__(self, model_name: str):
        """Constructor with error handling"""
        try:
            logger.info(f"Loading Model {model_name}...")
            self.model_name = model_name
            self.nlp = transformers.pipeline(
                "question-answering", 
                model=model_name, 
                tokenizer=model_name,
                return_all_scores=False
            )
            logger.success(f"Model {model_name} loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def analyse_pages(self, pages: List[str], question: str) -> List[Tuple[float, str]]:
        """Analyse pages with comprehensive error handling"""
        try:
            logger.debug(f"Analysing Pages for the question {question}...")
            answer = []
            
            if not pages or not question:
                logger.warning("Empty pages or question provided")
                return answer
            
            for input_paragraph in pages:
                try:
                    if not input_paragraph or input_paragraph.strip() == "":
                        continue
                    
                    QA_input = {"question": question, "context": input_paragraph}
                    res = self.nlp(QA_input)
                    
                    if res and res.get("score", 0) > 1e-2:
                        score = float(res["score"])
                        ans_text = str(res["answer"]).strip().replace("\n", " ")
                        logger.debug(f"{score}: {ans_text}")
                        answer.append((score, ans_text))
                        
                except Exception as e:
                    logger.warning(f"Error processing paragraph: {e}")
                    continue
            
            answer.sort(reverse=True)
            logger.debug("Analysed Pages")
            return answer
            
        except Exception as e:
            logger.error(f"Error in analyse_pages: {e}")
            return []

class Analyser:
    """Enhanced Analyser class with comprehensive error handling"""

    def __init__(self):
        """Constructor with error handling"""
        try:
            self.nlp_model = Model(settings.NLP_MODEL)
            self.scraper = Scholar_scraper.scholarly_scraper()
            self.browser = Browsing.browser()
            self.LLM = LLM.LLM(settings.LLM_MODEL)
            self.initial_results = []
            self.filtered_results = []
            self.additional_results = []
            self.neglected_results = []
            logger.success("Analyser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Analyser: {e}")
            raise

    def level_1(self, pages: List[str]) -> List[Tuple[float, str]]:
        """Level 1 analysis with error handling"""
        try:
            logger.info("Level 1 Analysis Started")
            answer = []
            
            if not pages:
                logger.error("No pages provided for analysis")
                return answer
            
            # Question 1: Algorithms
            try:
                answer_1 = self.nlp_model.analyse_pages(pages, settings.QUESTION_1)
                answer.extend(answer_1)
                logger.debug(f"Question 1 found {len(answer_1)} answers")
            except Exception as e:
                logger.error(f"Question 1 analysis failed: {e}")
            
            # Question 2: Techniques
            try:
                answer_2 = self.nlp_model.analyse_pages(pages, settings.QUESTION_2)
                answer.extend(answer_2)
                logger.debug(f"Question 2 found {len(answer_2)} answers")
            except Exception as e:
                logger.error(f"Question 2 analysis failed: {e}")
            
            # Question 3: ML Techniques
            try:
                answer_3 = self.nlp_model.analyse_pages(pages, settings.QUESTION_3)
                answer.extend(answer_3)
                logger.debug(f"Question 3 found {len(answer_3)} answers")
            except Exception as e:
                logger.error(f"Question 3 analysis failed: {e}")
            
            # Question 4: Input Format
            try:
                answer_4 = self.nlp_model.analyse_pages(pages, settings.QUESTION_4)
                self.additional_results = answer_4
                logger.debug(f"Question 4 found {len(answer_4)} answers")
            except Exception as e:
                logger.error(f"Question 4 analysis failed: {e}")
                self.additional_results = []
            
            answer.sort(reverse=True)
            
            if len(answer) <= 0:
                logger.error("No answer found")
                self.initial_results = []
                return answer
            
            # Remove duplicates
            self.initial_results = [answer[0]]
            for i in range(1, len(answer)):
                try:
                    if not Helper_functions.check_presence(answer[i][1], self.initial_results):
                        self.initial_results.append(answer[i])
                except Exception as e:
                    logger.warning(f"Error checking presence: {e}")
                    continue
            
            logger.success(f"Level 1 Analysis Completed with {len(self.initial_results)} unique results")
            return self.initial_results
            
        except Exception as e:
            logger.error(f"Level 1 analysis failed: {e}")
            return []

    def level_2_alt(self, results: List[Tuple[float, str]]) -> List[str]:
        """Alternative Level 2 with error handling"""
        try:
            logger.info("Level 2 Alternative Analysis Started")
            
            if not results:
                logger.warning("No results provided for Level 2 alt")
                return []
            
            logger.debug("Filtering Results with LLM")
            list_of_keywords = [str(i[1]) for i in results if len(i) > 1]
            
            if not list_of_keywords:
                return []
            
            # Use LLM to filter keywords
            keywords_response = self.LLM.keyword_completion(list_of_keywords)
            
            if keywords_response.success:
                keywords = keywords_response.data
                logger.debug(f"LLM returned {len(keywords)} filtered keywords")
            else:
                logger.error(f"LLM keyword completion failed: {keywords_response.error}")
                keywords = list_of_keywords[:5]  # Fallback to top 5
            
            filtered_keywords = []
            for keyword in keywords:
                if not self.find_genericwords(str(keyword)):
                    filtered_keywords.append(str(keyword))
                else:
                    logger.debug(f"Generic word found and removed: {keyword}")
            
            logger.success(f"Level 2 Alternative Analysis Completed with {len(filtered_keywords)} keywords")
            return filtered_keywords
            
        except Exception as e:
            logger.error(f"Level 2 alternative analysis failed: {e}")
            return []

    def find_genericwords(self, text: str) -> bool:
        """Find generic words with error handling"""
        try:
            if not text or not isinstance(text, str):
                return False
            
            pattern = [
                re.compile(r"(?i)machine\s*learning"),
                re.compile(r"(?i)artificial\s*intelligence"),
                re.compile(r"(?i)510\s*k"),
                re.compile(r"(?i)A\.I\."),
            ]
            return Helper_functions.regex_search(text, pattern)
        except Exception as e:
            logger.warning(f"Error in find_genericwords: {e}")
            return False

    def level_2(self, results: List[Tuple[float, str]]) -> List[Tuple[float, str]]:
        """Level 2 analysis with error handling"""
        try:
            logger.info("Level 2 Analysis Started")
            
            if not results:
                logger.warning("No results provided for Level 2")
                return []
            
            logger.debug("Filtering Results with Browser validation")
            self.filtered_results = []
            self.neglected_results = []
            
            max_keywords = getattr(settings, 'NUMBER_OF_KEYWORDS', 10)
            
            for i in results:
                if len(self.filtered_results) >= max_keywords:
                    break
                
                try:
                    keyword = str(i[1]) if len(i) > 1 else ""
                    if not keyword:
                        continue
                    
                    logger.debug(f"Processing keyword: {keyword}")
                    
                    if self.find_genericwords(keyword):
                        logger.debug("Generic word found, skipping")
                        continue
                    
                    if self.browser.check_desc(keyword):
                        self.filtered_results.append(i)
                        logger.debug(f"Keyword validated: {keyword}")
                    else:
                        self.neglected_results.append(i)
                        logger.debug(f"Keyword not validated: {keyword}")
                        
                except Exception as e:
                    logger.warning(f"Error processing keyword {i}: {e}")
                    continue
            
            logger.success(f"Level 2 Analysis Completed with {len(self.filtered_results)} validated keywords")
            return self.filtered_results
            
        except Exception as e:
            logger.error(f"Level 2 analysis failed: {e}")
            return []

    def level_3(self, results: List[Tuple[float, str]]) -> List:
        """Level 3 analysis with error handling"""
        try:
            logger.info("Level 3 Analysis Started")
            
            if not results:
                logger.warning("No results provided for Level 3")
                return []
            
            logger.debug("Searching for security attack papers")
            prefix = [
                "Security Attacks on ",
                "Inference time attacks on ",
                "Training time attacks on ",
            ]
            
            answers = []
            for i, search_prefix in enumerate(prefix):
                objects = []
                logger.debug(f"Searching with prefix: {search_prefix}")
                
                for j in range(len(results)):
                    try:
                        keyword = str(results[j][1]) if len(results[j]) > 1 else ""
                        if keyword:
                            search_term = search_prefix + keyword
                            logger.debug(f"Searching: {search_term}")
                            result = self.scraper.get_info(search_term)
                            objects.append(result)
                            logger.debug(f"Found {len(result)} papers for: {keyword}")
                        else:
                            objects.append([])
                    except Exception as e:
                        logger.warning(f"Error searching for {search_prefix}{keyword}: {e}")
                        objects.append([])
                
                answers.append(objects)
            
            logger.success("Level 3 Analysis Completed")
            return answers
            
        except Exception as e:
            logger.error(f"Level 3 analysis failed: {e}")
            return []

    def level_4(self, results: List) -> Tuple[List, List]:
        """Level 4 analysis with error handling"""
        try:
            logger.info("Level 4 Analysis Started")
            
            if not results:
                logger.warning("No results provided for Level 4")
                return [], []
            
            logger.debug("Classifying attack papers")
            rejected_results = []
            
            for i in range(len(results)):
                rejected_results.append([])
                for j in range(len(results[i])):
                    rejected_results[i].append([])
                    filtered_results = []
                    
                    for k in range(len(results[i][j])):
                        try:
                            paper_info = results[i][j][k]
                            if len(paper_info) < 3:
                                continue
                            
                            logger.debug(f"Classifying paper: {paper_info[1]}")
                            page = self.browser.get_page(str(paper_info[2]))
                            paper_type = self.__find_attack_type(page)
                            
                            if paper_type == 0 or paper_type == 1:
                                paper_copy = list(paper_info)
                                paper_copy.append(f"Attack Type {paper_type}")
                                filtered_results.append(paper_copy)
                                logger.debug(f"Paper classified as attack type {paper_type}")
                            else:
                                rejected_results[i][j].append(paper_info)
                                logger.debug("Paper rejected - not attack related")
                                
                        except Exception as e:
                            logger.warning(f"Error classifying paper: {e}")
                            continue
                    
                    results[i][j] = filtered_results
            
            logger.success("Level 4 Analysis Completed")
            return results, rejected_results
            
        except Exception as e:
            logger.error(f"Level 4 analysis failed: {e}")
            return results if 'results' in locals() else [], []

    def __find_attack_type(self, text: str) -> int:
        """Find attack type with error handling"""
        try:
            if not text or not isinstance(text, str):
                return -1
            
            pattern_inference_time = [
                re.compile(r"(?i)adversarial\s*example"),
                re.compile(r"(?i)evasion"),
                re.compile(r"(?i)privacy attack"),
                re.compile(r"(?i)membership\s*inference"),
                re.compile(r"(?i)model inversion"),
            ]
            pattern_training_time = [
                re.compile(r"(?i)training\s*time"),
                re.compile(r"(?i)poisoning"),
                re.compile(r"(?i)data\s*manipulation"),
            ]
            
            if Helper_functions.regex_search(text, pattern_inference_time):
                return 0  # Inference time attack
            elif Helper_functions.regex_search(text, pattern_training_time):
                return 1  # Training time attack
            
            return -1
            
        except Exception as e:
            logger.warning(f"Error in find_attack_type: {e}")
            return -1

    def return_results(self) -> List[str]:
        """Return results with error handling"""
        try:
            results = [self.initial_results, self.filtered_results, self.additional_results]
            answers = []
            
            for i, result_list in enumerate(results):
                answer_string = ""
                point = 1
                for j in result_list:
                    try:
                        keyword = str(j[1]) if len(j) > 1 else "Unknown"
                        score = float(j[0]) if len(j) > 0 else 0.0
                        answer_string += f"{point}. {keyword} (Score: {score:.3f})\n"
                        point += 1
                    except Exception as e:
                        logger.warning(f"Error formatting result: {e}")
                        continue
                
                if not answer_string:
                    answer_string = f"No results found for Level {i+1}"
                
                answers.append(answer_string.strip())
            
            return answers
            
        except Exception as e:
            logger.error(f"Error returning results: {e}")
            return ["Error in Level 1", "Error in Level 2", "Error in Level 4"]

def process_individual_pdf(analyser):
    """Process individual PDF with validation and CSV writing"""
    try:
        index = input("Enter the Submission Number: ").strip()
        if not index:
            print("Please enter a valid submission number")
            return
        
        if not Helper_functions.check_pdf_path(index):
            print(f"❌ PDF not found for submission {index}")
            return
        
        matching_rows = data[data["Submission Number"] == index]
        if matching_rows.empty:
            print(f"❌ No data found for submission {index} in Excel file")
            return
        
        row = matching_rows.iloc[0]
        print(f"\n🔄 Processing {index}...")
        print(f"Device: {row.get('Device', 'Unknown')}")
        print(f"Company: {row.get('Company', 'Unknown')}")
        
        success = create_row(index, row)
        if success:
            print(f"\n✅ Successfully processed {index}")
            print(f"📁 Data saved to: {settings.CSV_FILE}")
            print("\nYou can now check the CSV file for the analysis results!")
        else:
            print(f"\n❌ Failed to process {index}")
            
    except Exception as e:
        logger.error(f"Error processing individual PDF: {e}")
        print(f"❌ Error occurred: {e}")

def process_range_pdfs(analyser):
    """Process range of PDFs with validation and CSV writing"""
    try:
        start = int(input("Enter the start index: "))
        end = int(input("Enter the end index: "))
        
        if start < 0 or end < start:
            print("❌ Invalid range")
            return
        
        if end >= len(data):
            print(f"⚠️ End index {end} is beyond data range. Max index: {len(data)-1}")
            end = len(data) - 1
        
        print(f"\n🔄 Processing {end-start+1} documents from index {start} to {end}...")
        
        processed = 0
        failed = 0
        
        for i in range(start, end + 1):
            try:
                row = data.iloc[i]
                index = str(row["Submission Number"])
                
                print(f"\n📄 Processing {i+1}/{end+1}: {index}")
                
                if not Helper_functions.check_pdf_path(index):
                    print(f"⚠️ Skipping {index} - PDF not found")
                    failed += 1
                    continue
                
                success = create_row(index, row)
                if success:
                    processed += 1
                    print(f"✅ {index} completed ({processed}/{end-start+1})")
                else:
                    failed += 1
                    print(f"❌ {index} failed")
                    
                # Save progress periodically
                if processed % 5 == 0:
                    csvfile.flush()
                    print(f"💾 Progress saved - {processed} completed")
                    
            except Exception as e:
                logger.error(f"Error processing index {i}: {e}")
                failed += 1
                print(f"❌ Error processing index {i}: {e}")
                continue
        
        # Final save
        csvfile.flush()
        print(f"\n🎉 Batch processing completed!")
        print(f"✅ Successful: {processed}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Results saved to: {settings.CSV_FILE}")
        
    except ValueError:
        print("❌ Please enter valid numbers")
    except Exception as e:
        logger.error(f"Error processing range: {e}")
        print(f"❌ Error occurred: {e}")

def process_from_file(analyser):
    """Process PDFs from input file with validation and CSV writing"""
    try:
        path = input("Enter the path to the file containing submission numbers: ").strip()
        
        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return
        
        with open(path, "r", encoding='utf-8') as file:
            submissions = [x.strip() for x in file.readlines() if x.strip()]
        
        if not submissions:
            print("❌ No submissions found in file")
            return
        
        print(f"\n🔄 Processing {len(submissions)} submissions from file...")
        
        processed = 0
        failed = 0
        
        for i, submission in enumerate(submissions):
            try:
                print(f"\n📄 Processing {i+1}/{len(submissions)}: {submission}")
                
                if not Helper_functions.check_pdf_path(submission):
                    print(f"⚠️ Skipping {submission} - PDF not found")
                    failed += 1
                    continue
                
                matching_rows = data[data["Submission Number"] == submission]
                if matching_rows.empty:
                    print(f"⚠️ Skipping {submission} - No data found in Excel file")
                    failed += 1
                    continue
                
                row = matching_rows.iloc[0]
                success = create_row(submission, row)
                
                if success:
                    processed += 1
                    print(f"✅ {submission} completed ({processed}/{len(submissions)})")
                else:
                    failed += 1
                    print(f"❌ {submission} failed")
                
                # Save progress periodically
                if processed % 5 == 0:
                    csvfile.flush()
                    print(f"💾 Progress saved - {processed} completed")
                    
            except Exception as e:
                logger.error(f"Error processing submission {submission}: {e}")
                failed += 1
                print(f"❌ Error processing {submission}: {e}")
                continue
        
        # Final save
        csvfile.flush()
        print(f"\n🎉 File processing completed!")
        print(f"✅ Successful: {processed}")
        print(f"❌ Failed: {failed}")
        print(f"📁 Results saved to: {settings.CSV_FILE}")
        
    except Exception as e:
        logger.error(f"Error processing from file: {e}")
        print(f"❌ Error occurred: {e}")

def get_user_input() -> int:
    """Get user input with validation"""
    while True:
        try:
            print("\n" + "="*50)
            print("Medical Device Analysis System")
            print("="*50)
            print("1. Analyze individual PDF")
            print("2. Analyze range of PDFs") 
            print("3. Analyze PDFs from input file")
            print("4. Exit")
            print("="*50)
            
            inp = input("Enter your choice (1-4): ").strip()
            if inp == '4':
                return 4
            
            inp = int(inp)
            if 1 <= inp <= 4:
                return inp
            else:
                print("❌ Please enter 1, 2, 3, or 4")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return 4

def cleanup_resources():
    """Clean up resources safely"""
    try:
        if 'Analyser_1' in globals():
            del Analyser_1
            logger.info("Analyser cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up Analyser: {e}")
    
    try:
        if 'csvfile' in globals() and csvfile and not csvfile.closed:
            csvfile.close()
            logger.info("CSV file closed")
            print(f"📁 Final results saved to: {settings.CSV_FILE}")
    except Exception as e:
        logger.warning(f"Error closing CSV file: {e}")

def display_system_info():
    """Display system information and file locations"""
    print("\n" + "="*60)
    print("MEDICAL DEVICE ANALYSIS SYSTEM - INITIALIZATION")
    print("="*60)
    print(f"📂 PDF Directory: {settings.PDF_DIR}")
    print(f"📊 Excel File: {settings.EXCEL_FILE}")
    print(f"💾 Output CSV: {settings.CSV_FILE}")
    print(f"🤖 NLP Model: {settings.NLP_MODEL}")
    print(f"🧠 LLM Model: {settings.LLM_MODEL}")
    print(f"📈 Data Records Loaded: {len(data)}")
    print("="*60)

# Main execution with comprehensive error handling
def main():
    """Main execution function"""
    try:
        display_system_info()
        
        print("\n🔄 Initializing Analyser...")
        global Analyser_1
        Analyser_1 = Analyser()
        print("✅ Analyser initialized successfully")
        
        while True:
            try:
                inp = get_user_input()
                
                if inp == 4:
                    print("👋 Exiting system...")
                    break
                elif inp == 1:
                    process_individual_pdf(Analyser_1)
                elif inp == 2:
                    process_range_pdfs(Analyser_1)
                elif inp == 3:
                    process_from_file(Analyser_1)
                
                # Ask if user wants to continue
                if inp != 4:
                    continue_choice = input("\nDo you want to perform another analysis? (y/n): ").lower().strip()
                    if continue_choice not in ['y', 'yes']:
                        print("👋 Exiting system...")
                        break
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Operation cancelled by user")
                choice = input("Do you want to exit the system? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    break
                continue
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                print(f"❌ An error occurred: {e}")
                print("Returning to main menu...")
                continue

    except KeyboardInterrupt:
        logger.critical("Raised KeyboardInterrupt - Closing script...")
        print("\n\n👋 Script terminated by user")
        
    except Exception as e:
        logger.critical(f"Critical error in main execution: {e}")
        logger.critical(traceback.format_exc())
        print(f"💥 Critical error: {e}")
        print("Please check the logs for more details.")
        
    finally:
        cleanup_resources()
        print("\n🎉 Script execution completed")
        print(f"📁 Check your results in: {settings.CSV_FILE}")

if __name__ == "__main__":
    main()