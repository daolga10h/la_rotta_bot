def test_required_env_vars_present():
    import config
    assert config.TELEGRAM_BOT_TOKEN
    assert config.ANTHROPIC_API_KEY
    assert config.SUPABASE_URL
    assert config.SUPABASE_KEY
    assert config.MODEL_NAME == "claude-sonnet-4-6"
    assert config.CLASSIFICATION_MODEL == "claude-haiku-4-5-20251001"


def test_llm_error_messages_defined():
    import config
    required_keys = {"timeout", "timeout_final", "rate_limit", "rate_limit_final", "server_error", "generic"}
    assert required_keys.issubset(config.LLM_ERROR_MESSAGES.keys())
    for msg in config.LLM_ERROR_MESSAGES.values():
        assert len(msg) > 0
