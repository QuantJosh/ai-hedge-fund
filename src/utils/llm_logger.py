"""
LLM Logging Decorators
Automatically logs all LLM model interactions and agent operations.
"""

import functools
import time
from typing import Any, Callable, Optional
from src.utils.logger import get_logger


def log_llm_call(agent_name: Optional[str] = None, ticker: Optional[str] = None):
    """Decorator to automatically log LLM calls with enhanced tracking"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            
            # Extract context information
            actual_agent_name = agent_name or "Unknown_Agent"
            actual_ticker = ticker
            
            # Extract parameters from call_llm function call
            # call_llm(prompt=..., pydantic_model=..., agent_name=..., state=...)
            
            # Get prompt (first positional arg or 'prompt' keyword)
            prompt = None
            if len(args) > 0:
                prompt = args[0]
            elif 'prompt' in kwargs:
                prompt = kwargs['prompt']
            
            # Get agent_name (keyword argument)
            if 'agent_name' in kwargs and kwargs['agent_name']:
                actual_agent_name = kwargs['agent_name']
            
            # Get state (keyword argument)
            state = kwargs.get('state')
            if state and hasattr(state, 'get'):
                # Extract ticker from state
                data = state.get('data', {})
                tickers = data.get('tickers', [])
                if tickers and not actual_ticker:
                    actual_ticker = tickers[0] if len(tickers) == 1 else f"{len(tickers)} tickers"
                
                # Extract model information from state
                metadata = state.get('metadata', {})
                model_provider = metadata.get('model_provider', 'Unknown')
                model_name = metadata.get('model_name', 'Unknown')
            else:
                model_provider = "Unknown"
                model_name = "Unknown"
            
            # Extract prompt text
            prompt_text = ""
            if prompt:
                # Convert different prompt formats to string
                if hasattr(prompt, 'messages'):  # ChatPromptTemplate or similar
                    if hasattr(prompt.messages, '__iter__'):
                        prompt_parts = []
                        for msg in prompt.messages:
                            if hasattr(msg, 'content'):
                                prompt_parts.append(f"{getattr(msg, 'role', 'unknown')}: {msg.content}")
                            else:
                                prompt_parts.append(str(msg))
                        prompt_text = "\n".join(prompt_parts)
                    else:
                        prompt_text = str(prompt.messages)
                elif isinstance(prompt, list):
                    # List of messages
                    prompt_parts = []
                    for msg in prompt:
                        if isinstance(msg, dict):
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', str(msg))
                            prompt_parts.append(f"{role}: {content}")
                        elif hasattr(msg, 'content'):
                            role = getattr(msg, 'role', getattr(msg, '__class__', {}).get('__name__', 'unknown'))
                            prompt_parts.append(f"{role}: {msg.content}")
                        else:
                            prompt_parts.append(str(msg))
                    prompt_text = "\n".join(prompt_parts)
                else:
                    prompt_text = str(prompt)
            
            # Also check kwargs for additional model info
            model_provider = kwargs.get('model_provider', kwargs.get('provider', model_provider))
            model_name = kwargs.get('model_name', kwargs.get('model', model_name))
            
            # Log request
            start_time = time.time()
            logger.log_model_request(
                agent_name=actual_agent_name,
                model_provider=model_provider,
                model_name=model_name,
                prompt=prompt_text,
                ticker=actual_ticker
            )
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Extract response text - try to get both raw and structured
                response_text = ""
                
                # Try to get the original JSON response if it's a Pydantic model
                if hasattr(result, 'model_dump'):
                    # This is a Pydantic model, convert to JSON
                    import json
                    try:
                        response_text = json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
                    except Exception:
                        response_text = str(result)
                elif hasattr(result, 'content'):
                    # This might be a raw LLM response
                    response_text = result.content
                elif isinstance(result, dict):
                    # This is a dictionary, convert to JSON
                    import json
                    try:
                        response_text = json.dumps(result, indent=2, ensure_ascii=False)
                    except Exception:
                        response_text = str(result)
                else:
                    response_text = str(result)
                
                # Log response
                logger.log_model_response(
                    agent_name=actual_agent_name,
                    model_provider=model_provider,
                    model_name=model_name,
                    response=response_text,
                    ticker=actual_ticker,
                    duration_ms=duration_ms
                )
                
                return result
                
            except Exception as e:
                # Log error
                logger.log_error(
                    agent_name=actual_agent_name,
                    error_message=f"LLM call failed: {str(e)}",
                    ticker=actual_ticker,
                    exception=e
                )
                raise
        
        return wrapper
    return decorator


def log_agent_execution(agent_name: str):
    """Decorator to log agent execution start and end with enhanced context"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            
            # Extract ticker and context from state
            ticker = None
            context_data = {}
            
            if len(args) > 0 and hasattr(args[0], 'get'):
                state = args[0]
                data = state.get('data', {})
                tickers = data.get('tickers', [])
                
                if tickers:
                    ticker = tickers[0] if len(tickers) == 1 else f"{len(tickers)} tickers"
                
                # Extract additional context
                context_data = {
                    "tickers_count": len(tickers),
                    "has_market_data": bool(data.get('market_data')),
                    "has_news_data": bool(data.get('news_data')),
                    "has_financial_data": bool(data.get('financial_data'))
                }
            
            # Log agent start
            logger.log_agent_start(agent_name, ticker, context_data)
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Extract result summary
                result_summary = None
                if isinstance(result, dict):
                    if 'messages' in result:
                        messages = result.get('messages', [])
                        if messages:
                            last_message = messages[-1]
                            if hasattr(last_message, 'content'):
                                content = last_message.content
                                result_summary = {
                                    "decision_preview": content[:200] + "..." if len(content) > 200 else content,
                                    "message_count": len(messages)
                                }
                    
                    # Look for decision data
                    if 'data' in result:
                        result_data = result['data']
                        if 'analysis_results' in result_data:
                            analysis = result_data['analysis_results']
                            if isinstance(analysis, dict):
                                result_summary = result_summary or {}
                                result_summary.update({
                                    "analysis_type": analysis.get('type', 'unknown'),
                                    "confidence": analysis.get('confidence'),
                                    "signal": analysis.get('signal')
                                })
                
                logger.log_agent_end(agent_name, ticker, result_summary)
                
                return result
                
            except Exception as e:
                # Log error with context
                logger.log_error(
                    agent_name=agent_name,
                    error_message=f"Agent execution failed: {str(e)}",
                    ticker=ticker,
                    exception=e
                )
                raise
        
        return wrapper
    return decorator


def log_data_operation(data_type: str, agent_name: str = "Data_Fetcher"):
    """Decorator to log data fetching operations with detailed metrics"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            
            # Extract ticker from arguments
            ticker = kwargs.get('ticker') or kwargs.get('symbol')
            if not ticker and args:
                # Try to find ticker in first argument
                if isinstance(args[0], str):
                    ticker = args[0]
                elif hasattr(args[0], 'get'):
                    ticker = args[0].get('ticker') or args[0].get('symbol')
            
            ticker = str(ticker) if ticker else 'Unknown'
            
            try:
                # Execute the function
                start_time = time.time()
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Analyze result
                success = result is not None
                count = 0
                
                if isinstance(result, (list, tuple)):
                    count = len(result)
                elif isinstance(result, dict):
                    # For dict results, try to find data count
                    if 'data' in result:
                        data = result['data']
                        if isinstance(data, (list, tuple)):
                            count = len(data)
                        else:
                            count = 1
                    else:
                        count = len(result) if result else 0
                elif result:
                    count = 1
                
                # Log successful data fetch
                logger.log_data_fetch(
                    agent_name=agent_name,
                    data_type=data_type,
                    ticker=ticker,
                    success=success,
                    count=count
                )
                
                # Also log as system event with timing
                if success and duration_ms > 1000:  # Log slow operations
                    logger.log_system(
                        f"Slow data operation: {data_type} for {ticker} took {duration_ms/1000:.1f}s",
                        {"data_type": data_type, "ticker": ticker, "duration_ms": duration_ms, "count": count}
                    )
                
                return result
                
            except Exception as e:
                # Log failed data fetch
                logger.log_data_fetch(
                    agent_name=agent_name,
                    data_type=data_type,
                    ticker=ticker,
                    success=False,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


def log_decision(agent_name: str):
    """Decorator specifically for logging trading decisions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = get_logger()
            
            try:
                result = func(*args, **kwargs)
                
                # Extract decision information from result
                if isinstance(result, dict):
                    # Look for decision data in various possible locations
                    decision_data = None
                    ticker = "Unknown"
                    
                    if 'data' in result:
                        data = result['data']
                        if 'analysis_results' in data:
                            decision_data = data['analysis_results']
                        if 'tickers' in data and data['tickers']:
                            ticker = data['tickers'][0]
                    
                    # Also check messages for decision content
                    if 'messages' in result and result['messages']:
                        last_message = result['messages'][-1]
                        if hasattr(last_message, 'content'):
                            content = last_message.content
                            # Try to extract decision from content
                            if any(word in content.lower() for word in ['buy', 'sell', 'hold', 'strong buy', 'strong sell']):
                                # This looks like a decision
                                logger.log_decision(
                                    agent_name=agent_name,
                                    ticker=ticker,
                                    signal="extracted_from_content",
                                    confidence=0.0,  # Unknown confidence
                                    reasoning=content[:500]
                                )
                    
                    # Log structured decision if available
                    if decision_data and isinstance(decision_data, dict):
                        signal = decision_data.get('signal', decision_data.get('recommendation', 'unknown'))
                        confidence = decision_data.get('confidence', decision_data.get('score', 0.0))
                        reasoning = decision_data.get('reasoning', decision_data.get('analysis', ''))
                        
                        logger.log_decision(
                            agent_name=agent_name,
                            ticker=ticker,
                            signal=str(signal),
                            confidence=float(confidence) if confidence else 0.0,
                            reasoning=str(reasoning)
                        )
                
                return result
                
            except Exception as e:
                logger.log_error(
                    agent_name=agent_name,
                    error_message=f"Decision logging failed: {str(e)}",
                    exception=e
                )
                # Don't re-raise, as this is just logging
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Convenience function for quick setup
def setup_logging(console_format: str = "human", console_level: str = "INFO", log_dir: str = "logs"):
    """Quick setup for logging with recommended settings"""
    from src.utils.logger import init_logger
    
    return init_logger(
        log_dir=log_dir,
        console_format=console_format,
        console_level=console_level,
        enable_console=True,
        enable_file=True,
        enable_json=True
    )