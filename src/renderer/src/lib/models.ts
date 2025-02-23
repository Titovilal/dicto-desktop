export const AI_MODELS = {
    "gemini-flash-2.0": ["google/gemini-2.0-flash-001", "Gemini Flash 2.0"],
    "claude-3.5-haiku": ["anthropic/claude-3.5-haiku", "Claude 3.5 Haiku"],
    "gpt-4o-mini": ["openai/gpt-4o-mini", "GPT-4 Mini"],
    "deepseek-v3": ["deepseek/deepseek-chat", "DeepSeek v3"],
    "llama-3.3-70b-distill-deepseek-r1": ["deepseek/deepseek-r1-distill-llama-70b", "Llama 3.3 70B (DeepSeek)"],
    "mistral-saba": ["mistralai/mistral-saba", "Mistral Saba"],
    "mistral-nemo": ["mistralai/mistral-nemo", "Mistral Nemo"],
    "qwen-32b-distill-deepseek-r1": ["deepseek/deepseek-r1-distill-qwen-32b", "Qwen 32B (DeepSeek)"]
} as const

export const getModelId = (key: keyof typeof AI_MODELS) => AI_MODELS[key][0]
export const getModelName = (key: keyof typeof AI_MODELS) => AI_MODELS[key][1]


