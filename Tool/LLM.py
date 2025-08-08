#!/usr/bin/env python3

import gpt4all
import re
import sys
import settings
import openai
from settings import logger
from typing import Optional, List, Union
import traceback
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response wrapper for LLM operations"""
    success: bool
    data: Union[str, List[str], None]
    error: Optional[str] = None
    error_type: Optional[str] = None


class LLMError(Exception):
    """Custom exception for LLM operations"""
    pass


class LLM:  # Specialized Language Model using opensource GPT4All
    """
    Specialized Language Model using opensource GPT4All.
    
    Usage Example:
        llm = LLM("ggml-gpt4all-j-v1.3-groovy")
        
        # Generate response
        response = llm.generate("What is AI?")
        if response.success:
            print(response.data)
        else:
            print(f"Error: {response.error}")
            
        # Keyword completion
        keywords = ["machine learning", "neural networks", "healthcare"]
        completed = llm.keyword_completion(keywords)
        if completed.success:
            print(completed.data)
        else:
            print(f"Error: {completed.error}")
    """

    def __init__(self, model_name: str):
        """
        Initializes the LLM with the specified GPT4All model.

        Args:
            model_name (str): The name of the GPT4All model to be used.

        Attributes:
            model_name (gpt4all.GPT4All): The GPT4All model instance.
            
        Raises:
            LLMError: If model initialization fails
        """
        try:
            if not model_name:
                raise ValueError("Model name cannot be empty")
                
            self.model_name = gpt4all.GPT4All(model_name)
            logger.info(f"Successfully initialized GPT4All Model: {model_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize GPT4All model '{model_name}': {str(e)}"
            logger.error(error_msg)
            raise LLMError(error_msg) from e

    def chat_session(self) -> LLMResponse:
        """
        Starts a chat session with the model.

        Returns:
            LLMResponse: Response object containing session info or error details
            
        Usage:
            session = llm.chat_session()
            if session.success:
                # Use session.data for chat operations
                pass
        """
        try:
            session = self.model_name.chat_session()
            logger.info("Chat session started successfully")
            return LLMResponse(success=True, data=session)
            
        except Exception as e:
            error_msg = f"Failed to start chat session: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                success=False, 
                data=None, 
                error=error_msg, 
                error_type=type(e).__name__
            )

    def generate(self, prompt: str) -> LLMResponse:
        """
        Generates a response from the model for the given prompt.

        Args:
            prompt (str): The input prompt for the model.

        Returns:
            LLMResponse: Response object containing generated text or error details
            
        Usage:
            response = llm.generate("Explain quantum computing")
            if response.success:
                print(f"Generated text: {response.data}")
            else:
                print(f"Generation failed: {response.error}")
        """
        try:
            # Input validation
            if not prompt:
                raise ValueError("Prompt cannot be empty")
            
            if not isinstance(prompt, str):
                raise TypeError("Prompt must be a string")
                
            if len(prompt.strip()) == 0:
                raise ValueError("Prompt cannot be only whitespace")

            logger.debug(f"PROMPT: {prompt}")
            
            response = self.model_name.generate(prompt)
            
            if response is None:
                raise LLMError("Model returned None response")
                
            logger.debug(f"RESPONSE: {response}")
            return LLMResponse(success=True, data=response)
            
        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                success=False, 
                data=None, 
                error=error_msg, 
                error_type="ValidationError"
            )
            
        except Exception as e:
            error_msg = f"Failed to generate response: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return LLMResponse(
                success=False, 
                data=None, 
                error=error_msg, 
                error_type=type(e).__name__
            )

    def __list_format(self, response: str) -> List[str]:
        """
        Filters and formats the response into a list of strings.

        Args:
            response (str): The response from the model.

        Returns:
            list[str]: A list of strings containing the filtered and formatted response.
            
        Raises:
            ValueError: If response is invalid
        """
        try:
            if not response:
                logger.warning("Empty response provided to list_format")
                return []
                
            if not isinstance(response, str):
                raise TypeError("Response must be a string")

            logger.debug("Filtering the response for the list")
            
            # Clean and split the response
            response = response.replace("\n", ",")
            response_list = response.split(",")
            filtered_response = []
            
            for i, item in enumerate(response_list):
                try:
                    # Clean the item
                    item = item.strip()
                    
                    # Split on colon and take first part
                    item = item.split(":")[0].strip()
                    
                    # Split on " - " and take first part
                    item = item.split(" - ")[0].strip()
                    
                    # Skip invalid items
                    if (not item or 
                        "most relevant" in item.lower() or 
                        len(item) > 60):
                        logger.debug(f"Skipping invalid item {i}: '{item}'")
                        continue
                    
                    logger.debug(f"Processing item {i}: {item}")
                    
                    # Extract from numbered list format
                    match = re.match(r"\d+\.\s*(.*)", item)
                    if match:
                        item = match.group(1)
                    
                    if item:  # Final check for non-empty
                        filtered_response.append(item)
                        
                except Exception as e:
                    logger.warning(f"Error processing list item {i}: {str(e)}")
                    continue
            
            logger.debug(f"Filtered Response: {', '.join(filtered_response)}")
            return filtered_response
            
        except Exception as e:
            logger.error(f"Error in list formatting: {str(e)}")
            raise ValueError(f"Failed to format response as list: {str(e)}") from e

    def keyword_completion(self, keywords: List[str]) -> LLMResponse:
        """
        Completes the given keywords by asking the model.

        Args:
            keywords (List[str]): The list of keywords to be completed.

        Returns:
            LLMResponse: Response object containing completed keywords list or error details
            
        Usage:
            keywords = ["machine learning", "neural networks", "healthcare", "diagnostics"]
            result = llm.keyword_completion(keywords)
            if result.success:
                print(f"Relevant keywords: {result.data}")
            else:
                print(f"Keyword completion failed: {result.error}")
        """
        try:
            # Input validation
            if keywords is None:
                raise ValueError("Keywords list cannot be None")
                
            if not isinstance(keywords, list):
                raise TypeError("Keywords must be a list")
            
            if not keywords:
                logger.debug("No keywords provided, returning empty list")
                return LLMResponse(success=True, data=[])
            
            # Validate each keyword
            valid_keywords = []
            for i, keyword in enumerate(keywords):
                if not isinstance(keyword, str):
                    logger.warning(f"Keyword {i} is not a string, skipping: {keyword}")
                    continue
                    
                keyword = keyword.strip()
                if keyword:
                    valid_keywords.append(keyword)
            
            if not valid_keywords:
                logger.debug("No valid keywords after filtering")
                return LLMResponse(success=True, data=[])

            logger.debug("Completing the keywords")
            
            # Build prompt
            prompt = ("Following are some keywords extracted from a document. "
                     "Which of these are the most relevant to the context of AI-enabled medical devices? ")
            prompt += ", ".join(valid_keywords)
            prompt += "\nPlease list only the most relevant keywords, one per line."

            # Generate response
            response_result = self.generate(prompt)
            
            if not response_result.success:
                return LLMResponse(
                    success=False,
                    data=None,
                    error=f"Failed to generate keyword completion: {response_result.error}",
                    error_type=response_result.error_type
                )
            
            # Format the response
            try:
                formatted_keywords = self.__list_format(response_result.data)
                return LLMResponse(success=True, data=formatted_keywords)
                
            except Exception as e:
                error_msg = f"Failed to format keyword response: {str(e)}"
                logger.error(error_msg)
                return LLMResponse(
                    success=False,
                    data=None,
                    error=error_msg,
                    error_type="FormattingError"
                )
                
        except (ValueError, TypeError) as e:
            error_msg = f"Invalid input for keyword completion: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                success=False,
                data=None,
                error=error_msg,
                error_type="ValidationError"
            )
            
        except Exception as e:
            error_msg = f"Unexpected error in keyword completion: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return LLMResponse(
                success=False,
                data=None,
                error=error_msg,
                error_type=type(e).__name__
            )


class ChatGPT:
    """
    ChatGPT interface using OpenAI API.
    
    Usage Example:
        chatgpt = ChatGPT("gpt-3.5-turbo")
        
        response = chatgpt.prompt("Explain machine learning in healthcare")
        if response.success:
            print(response.data)
        else:
            print(f"Error: {response.error}")
    """
    
    def __init__(self, model_name: str):
        """
        Initialize ChatGPT with model name.
        
        Args:
            model_name (str): The OpenAI model to use
            
        Raises:
            LLMError: If initialization fails
        """
        try:
            if not model_name:
                raise ValueError("Model name cannot be empty")
                
            if not hasattr(settings, 'OPEN_AI_API_KEY'):
                raise AttributeError("OPEN_AI_API_KEY not found in settings")
                
            if not settings.OPEN_AI_API_KEY:
                raise ValueError("OpenAI API key is empty")

            self.client = openai.OpenAI(api_key=settings.OPEN_AI_API_KEY)
            self.model = model_name
            logger.info(f"Successfully initialized ChatGPT with model: {model_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize ChatGPT: {str(e)}"
            logger.error(error_msg)
            raise LLMError(error_msg) from e

    def prompt(self, prompt_string: str) -> LLMResponse:
        """
        Send prompt to ChatGPT and get response.
        
        Args:
            prompt_string (str): The prompt to send
            
        Returns:
            LLMResponse: Response object containing result or error
            
        Usage:
            response = chatgpt.prompt("What are the benefits of AI in healthcare?")
            if response.success:
                print(f"ChatGPT response: {response.data}")
            else:
                print(f"Error: {response.error}")
        """
        try:
            # Input validation
            if not prompt_string:
                raise ValueError("Prompt string cannot be empty")
                
            if not isinstance(prompt_string, str):
                raise TypeError("Prompt must be a string")
                
            if len(prompt_string.strip()) == 0:
                raise ValueError("Prompt cannot be only whitespace")

            logger.debug(f"Sending prompt to ChatGPT: {prompt_string}")
            
            response = self.client.completions.create(
                model=self.model,
                prompt=prompt_string,
                response_format={"type": "json_object"},
            )
            
            if not response.choices:
                raise LLMError("No response choices returned from OpenAI")
                
            content = response.choices[0].message.content
            
            if content is None:
                raise LLMError("Received None content from OpenAI")
            
            logger.debug(f"ChatGPT response received: {content}")
            return LLMResponse(success=True, data=content)
            
        except ValueError as e:
            error_msg = f"Invalid input: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                success=False,
                data=None,
                error=error_msg,
                error_type="ValidationError"
            )
            
        except openai.APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                success=False,
                data=None,
                error=error_msg,
                error_type="APIError"
            )
            
        except openai.RateLimitError as e:
            error_msg = f"OpenAI rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            return LLMResponse(
                success=False,
                data=None,
                error=error_msg,
                error_type="RateLimitError"
            )
            
        except Exception as e:
            error_msg = f"Unexpected error in ChatGPT prompt: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return LLMResponse(
                success=False,
                data=None,
                error=error_msg,
                error_type=type(e).__name__
            )


# Usage Examples and Interface Documentation
def example_usage():
    """
    Examples of how to use the enhanced LLM classes.
    """
    print("=== LLM Usage Examples ===\n")
    
    try:
        # Initialize LLM
        print("1. Initializing LLM...")
        llm = LLM("ggml-gpt4all-j-v1.3-groovy")
        print("✓ LLM initialized successfully\n")
        
        # Generate text
        print("2. Generating text...")
        prompt = "What are the key applications of AI in medical devices?"
        response = llm.generate(prompt)
        
        if response.success:
            print(f"✓ Generated response: {response.data[:100]}...")
        else:
            print(f"✗ Generation failed: {response.error}")
        print()
        
        # Keyword completion
        print("3. Processing keywords...")
        keywords = ["artificial intelligence", "medical imaging", "diagnostics", 
                   "machine learning", "patient monitoring", "robotics"]
        
        result = llm.keyword_completion(keywords)
        
        if result.success:
            print(f"✓ Relevant keywords: {result.data}")
        else:
            print(f"✗ Keyword processing failed: {result.error}")
        print()
        
    except LLMError as e:
        print(f"✗ LLM Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    try:
        # Initialize ChatGPT
        print("4. Initializing ChatGPT...")
        chatgpt = ChatGPT("gpt-3.5-turbo")
        print("✓ ChatGPT initialized successfully\n")
        
        # Send prompt
        print("5. Sending prompt to ChatGPT...")
        prompt = "List 3 benefits of AI in healthcare in JSON format"
        response = chatgpt.prompt(prompt)
        
        if response.success:
            print(f"✓ ChatGPT response: {response.data}")
        else:
            print(f"✗ ChatGPT error: {response.error}")
        print()
        
    except LLMError as e:
        print(f"✗ ChatGPT Error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


if __name__ == "__main__":
    example_usage()