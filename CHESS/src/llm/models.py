from typing import Any, Dict, List

from langchain_core.exceptions import OutputParserException
from langchain.output_parsers import OutputFixingParser

from llm.engine_configs import ENGINE_CONFIGS
from runner.logger import Logger
from threading_utils import ordered_concurrent_function_calls

def get_llm_chain(engine_name: str, temperature: float = 0, reasoning_effort: str = None, base_uri: str = None) -> Any:
    """
    Returns the appropriate LLM chain based on the provided engine name and temperature.

    Args:
        engine (str): The name of the engine.
        temperature (float): The temperature for the LLM.
        reasoning_effort (str, optional): The reasoning effort for the LLM. Defaults to None.
        base_uri (str, optional): The base URI for the engine. Defaults to None.
        model_kwargs (Dict[str, Any], optional): Additional keyword arguments for the model. Defaults to None.

    Returns:
        Any: The LLM chain instance.

    Raises:
        ValueError: If the engine is not supported.
    """
    if engine_name not in ENGINE_CONFIGS:
        raise ValueError(f"Engine {engine_name} not supported")
    
    config = ENGINE_CONFIGS[engine_name]
    constructor = config["constructor"]
    # params = config["params"]
    params = config["params"].copy()
    if temperature:
        params["temperature"] = temperature
    if reasoning_effort:
        params["reasoning_effort"] = reasoning_effort
        print(f"------ trying to add reasoning_effort={reasoning_effort} to model_kwargs for {engine_name}")
        # if "model_kwargs" not in params:
        #     params["model_kwargs"] = {}
        # params["model_kwargs"]["reasoning_effort"] = reasoning_effort
    
    # print(f"== Engine: {engine_name} params: {params}")
    # # merge model_kwargs from explicit arg 
    # mk = model_kwargs if model_kwargs is not None else config["params"].get("model_kwargs")
    # if mk:
    #     params.setdefault("model_kwargs", {})
    #     if isinstance(params["model_kwargs"], dict):
    #         params["model_kwargs"].update(mk)
    #     else:
    #         params["model_kwargs"] = mk
    # if "gpt-5" in engine_name:
    #         # Pass it in model_kwargs so LangChain 0.2.17 doesn't reject it
    #         print("Adding reasoning_effort=low to model_kwargs for", engine_name)
    #         if "model_kwargs" not in params:
    #             params["model_kwargs"] = {}
    #         params["model_kwargs"]["reasoning_effort"] = "minimal"
    
    
    # Adjust base_uri if provided
    if base_uri and "openai_api_base" in params:
        params["openai_api_base"] = f"{base_uri}/v1"
    
    model = constructor(**params)
    if "preprocess" in config:
        llm_chain = config["preprocess"] | model
    else:
        # print("model params:", params)
        llm_chain = model
    return llm_chain

# def call_llm_chain(prompt: Any, engine: Any, parser: Any, request_kwargs: Dict[str, Any], step: int, max_attempts: int = 12, backoff_base: int = 2, jitter_max: int = 60) -> Any:
#     """
#     Calls the LLM chain with exponential backoff and jitter on failure.

#     Args:
#         prompt (Any): The prompt to be passed to the chain.
#         engine (Any): The engine to be used in the chain.
#         parser (Any): The parser to parse the output.
#         request_kwargs (Dict[str, Any]): The request arguments.
#         step (int): The current step in the process.
#         max_attempts (int, optional): The maximum number of attempts. Defaults to 12.
#         backoff_base (int, optional): The base for exponential backoff. Defaults to 2.
#         jitter_max (int, optional): The maximum jitter in seconds. Defaults to 60.

#     Returns:
#         Any: The output from the chain.

#     Raises:
#         Exception: If all attempts fail.
#     """
#     logger = Logger()
#     for attempt in range(max_attempts):
#         try:
#             # chain = prompt | engine | parser
#             chain = prompt | engine
#             prompt_text = prompt.invoke(request_kwargs).messages[0].content
#             output = chain.invoke(request_kwargs)
#             if isinstance(output, str):
#                 if output.strip() == "":
#                     engine = get_llm_chain("gemini-1.5-flash")
#                     raise OutputParserException("Empty output")
#             else:
#                 if output.content.strip() == "":    
#                     engine = get_llm_chain("gemini-1.5-flash")
#                     raise OutputParserException("Empty output")
#             output = parser.invoke(output)
#             logger.log_conversation(
#                 [
#                     {
#                         "text": prompt_text,
#                         "from": "Human",
#                         "step": step
#                     },
#                     {
#                         "text": output,
#                         "from": "AI",
#                         "step": step
#                     }
#                 ]
#             )
#             return output
#         except OutputParserException as e:
#             logger.log(f"OutputParserException: {e}", "warning")
#             new_parser = OutputFixingParser.from_llm(parser=parser, llm=engine)
#             chain = prompt | engine | new_parser
#             if attempt == max_attempts - 1:
#                 logger.log(f"call_chain: {e}", "error")
#                 raise e
#         except Exception as e:
#             # if attempt < max_attempts - 1:
#             #     logger.log(f"Failed to invoke the chain {attempt + 1} times.\n{type(e)}\n{e}", "warning")
#             #     sleep_time = (backoff_base ** attempt) + random.uniform(0, jitter_max)
#             #     time.sleep(sleep_time)
#             # else:
#             logger.log(f"Failed to invoke the chain {attempt + 1} times.\n{type(e)} <{e}>\n", "error")
#             raise e

def call_llm_chain(prompt: Any, engine: Any, parser: Any, request_kwargs: Dict[str, Any], step: int, max_attempts: int = 12, backoff_base: int = 2, jitter_max: int = 60) -> Any:
    """
    Calls the LLM chain with exponential backoff and jitter on failure.
    Includes TOKEN USAGE logging.
    """
    logger = Logger()
    for attempt in range(max_attempts):
        try:
            # 1. Prepare Chain
            chain = prompt | engine
            prompt_text = prompt.invoke(request_kwargs).messages[0].content
            
            # 2. Invoke Engine (Capture raw response object)
            response = chain.invoke(request_kwargs)
            
            # 3. Check for Empty Output (Standard Check)
            content_to_check = response if isinstance(response, str) else response.content
            if not content_to_check or content_to_check.strip() == "":
                engine = get_llm_chain("gemini-1.5-flash")
                raise OutputParserException("Empty output")

            # =================================================================
            # NEW: SAFE COST LOGGING BLOCK
            # This block is isolated. If it fails, the agent DOES NOT crash.
            # =================================================================
            try:
                # Attempt to grab standard usage metadata (LangChain standard)
                usage = getattr(response, "usage_metadata", None)
                
                # Fallback: Attempt to grab raw OpenAI metadata
                if not usage:
                    usage = getattr(response, "response_metadata", {}).get("token_usage")

                if usage:
                    # extract counts safely
                    p_tok = usage.get("input_tokens", 0) or usage.get("prompt_tokens", 0)
                    c_tok = usage.get("output_tokens", 0) or usage.get("completion_tokens", 0)
                    t_tok = usage.get("total_tokens", 0)

                    r_tok = usage.get("reasoning_tokens", 0)
                    if not r_tok and "completion_tokens_details" in usage:
                        r_tok = usage["completion_tokens_details"].get("reasoning_tokens", 0)
                    if not r_tok and "specific_metadata" in usage:
                        r_tok = usage["specific_metadata"].get("reasoning_tokens", 0)
                    
                    cost_msg = f"[Step {step}] TOKEN USAGE: Input={p_tok} | Output={c_tok} (Reasoning={r_tok}) | Total={t_tok}"
                    
                    # THIS WRITES TO THE FILE results/.../logs/qid_dbid.log
                    logger.log_conversation([
                        {
                            "text": cost_msg,
                            "from": "System (Cost)",
                            "step": step
                        }
                    ])
                    
                    # Optional: Still print to console if you want to see progress
                    # print(f"[Step {step}] {cost_msg}")
            except Exception as log_err:
                # Silently fail logging so we don't stop the agent
                logger.log(f"Warning: Could not log token usage: {log_err}", "warning")
            # =================================================================

            # 4. Parse Output (Standard Logic)
            # We pass 'response' because parsers handles AIMessage objects
            parsed_output = parser.invoke(response)
            
            # 5. Log Conversation
            logger.log_conversation(
                [
                    {
                        "text": prompt_text,
                        "from": "Human",
                        "step": step
                    },
                    {
                        "text": parsed_output, 
                        "from": "AI",
                        "step": step
                    }
                ]
            )
            return parsed_output

        except OutputParserException as e:
            logger.log(f"OutputParserException: {e}", "warning")
            new_parser = OutputFixingParser.from_llm(parser=parser, llm=engine)
            
            # Re-construct chain for the retry attempt
            chain = prompt | engine | new_parser
            
            if attempt == max_attempts - 1:
                logger.log(f"call_chain: {e}", "error")
                raise e
        except Exception as e:
            # Your existing retry logic
            logger.log(f"Failed to invoke the chain {attempt + 1} times.\n{type(e)} <{e}>\n", "error")
            raise e

def async_llm_chain_call(
    prompt: Any, 
    engine: Any, 
    parser: Any, 
    request_list: List[Dict[str, Any]], 
    step: int, 
    sampling_count: int = 1
) -> List[List[Any]]:
    """
    Asynchronously calls the LLM chain using multiple threads.

    Args:
        prompt (Any): The prompt to be passed to the chain.
        engine (Any): The engine to be used in the chain.
        parser (Any): The parser to parse the output.
        request_list (List[Dict[str, Any]]): The list of request arguments.
        step (int): The current step in the process.
        sampling_count (int): The number of samples to be taken.

    Returns:
        List[List[Any]]: A list of lists containing the results for each request.
    """

    call_list = []
    engine_id = 0
    for request_id, request_kwargs in enumerate(request_list):
        for _ in range(sampling_count):
            call_list.append({
                'function': call_llm_chain,
                'kwargs': {
                    'prompt': prompt,
                    'engine': engine[engine_id % len(engine)] if isinstance(engine,list) else engine,
                    'parser': parser,
                    'request_kwargs': request_kwargs,
                    'step': step
                }
            })
            engine_id += 1

    # Execute the functions concurrently
    results = ordered_concurrent_function_calls(call_list)

    # Group results by sampling_count
    grouped_results = [
        results[i * sampling_count: (i + 1) * sampling_count]
        for i in range(len(request_list))
    ]

    return grouped_results

def call_engine(message: str, engine: Any, max_attempts: int = 12, backoff_base: int = 2, jitter_max: int = 60) -> Any:
    """
    Calls the LLM chain with exponential backoff and jitter on failure.

    Args:
        message (str): The message to be passed to the chain.
        engine (Any): The engine to be used in the chain.
        max_attempts (int, optional): The maximum number of attempts. Defaults to 12.
        backoff_base (int, optional): The base for exponential backoff. Defaults to 2.
        jitter_max (int, optional): The maximum jitter in seconds. Defaults to 60.

    Returns:
        Any: The output from the chain.

    Raises:
        Exception: If all attempts fail.
    """
    logger = Logger()
    for attempt in range(max_attempts):
        try:
            output = engine.invoke(message)
            return output.content
        except Exception as e:
            # if attempt < max_attempts - 1:
            #     logger.log(f"Failed to invoke the chain {attempt + 1} times.\n{type(e)}\n{e}", "warning")
            #     sleep_time = (backoff_base ** attempt) + random.uniform(0, jitter_max)
            #     time.sleep(sleep_time)
            # else:
            logger.log(f"Failed to invoke the chain {attempt + 1} times.\n{type(e)} <{e}>\n", "error")
            raise e