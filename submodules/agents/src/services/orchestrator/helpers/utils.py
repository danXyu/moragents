def parse_llm_structured_output(value, model_cls, logger, context):
    """
    Helper to ensure LLM output is parsed as a Pydantic model.
    If value is a string, attempts to parse as JSON into model_cls.
    Logs and raises on error.
    """
    if isinstance(value, model_cls):
        return value
    if isinstance(value, str):
        logger.warning(f"LLM returned string for {context}, attempting to parse: {value}")
        try:
            return model_cls.model_validate_json(value)
        except Exception as e:
            logger.error(f"Failed to parse {context}: {e}")
            raise ValueError(f"LLM did not return valid {context}: {value}")
    logger.error(f"LLM returned unexpected type for {context}: {type(value)}")
    raise ValueError(f"LLM did not return valid {context}: {value}")
