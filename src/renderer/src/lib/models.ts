export const AI_MODELS = {
    "google/gemini-2.0-flash-001": "Gemini Flash 2.0",
    "anthropic/claude-3.5-haiku": "Claude 3.5 Haiku",
    "openai/gpt-4o-mini": "GPT-4o Mini",
    "deepseek/deepseek-chat": "DeepSeek v3",
    "deepseek/deepseek-r1-distill-llama-70b": "Llama 3.3 70B (DeepSeek as Teacher)",
    "mistralai/mistral-saba": "Mistral Saba",
    "mistralai/mistral-nemo": "Mistral Nemo",
    "deepseek/deepseek-r1-distill-qwen-32b": "Qwen 32B (DeepSeek as Teacher)"
} as const

export interface ModelInfo {
    name: string
    description: string
    bestFor: string[]
}

export const AI_MODELS_INFO: Record<keyof typeof AI_MODELS, ModelInfo> = {
    "google/gemini-2.0-flash-001": {
        name: "Gemini Flash 2.0",
        description: "Fast and efficient model with good balance of speed and quality",
        bestFor: ["Quick responses", "General tasks", "Code generation"]
    },
    "anthropic/claude-3.5-haiku": {
        name: "Claude 3.5 Haiku",
        description: "Highly capable at understanding context and nuanced instructions",
        bestFor: ["Complex analysis", "Detailed explanations", "Technical writing"]
    },
    "openai/gpt-4o-mini": {
        name: "GPT-4o Mini",
        description: "Lightweight version optimized for everyday tasks",
        bestFor: ["Basic text processing", "Simple summaries", "Quick translations"]
    },
    "deepseek/deepseek-chat": {
        name: "DeepSeek v3",
        description: "Advanced model with strong reasoning capabilities",
        bestFor: ["Problem solving", "Technical discussions", "Detailed analysis"]
    },
    "deepseek/deepseek-r1-distill-llama-70b": {
        name: "Llama 3.3 70B",
        description: "Large model with broad knowledge base",
        bestFor: ["Creative writing", "Complex reasoning", "Detailed responses"]
    },
    "mistralai/mistral-saba": {
        name: "Mistral Saba",
        description: "Balanced model with good general capabilities",
        bestFor: ["General purpose", "Content generation", "Text analysis"]
    },
    "mistralai/mistral-nemo": {
        name: "Mistral Nemo",
        description: "Specialized in technical and analytical tasks",
        bestFor: ["Technical writing", "Code analysis", "Data interpretation"]
    },
    "deepseek/deepseek-r1-distill-qwen-32b": {
        name: "Qwen 32B",
        description: "Efficient model with good performance on various tasks",
        bestFor: ["General tasks", "Content processing", "Basic analysis"]
    }
} as const

export const getModelId = (key: keyof typeof AI_MODELS) => key
export const getModelName = (key: keyof typeof AI_MODELS) => AI_MODELS[key]


