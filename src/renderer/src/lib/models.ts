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
        description:
            "A fast and powerful model from Google, designed to provide quick and high-quality responses, balancing speed and performance in generative tasks.",
        bestFor: [
            "Quick responses",
            "General tasks",
            "Code generation"
        ]
    },
    "anthropic/claude-3.5-haiku": {
        name: "Claude 3.5 Haiku",
        description:
            "Excels at understanding complex contexts and following nuanced instructions, making it ideal for in-depth analysis and specialized writing.",
        bestFor: [
            "Complex analysis",
            "Detailed explanations",
            "Technical writing"
        ]
    },
    "openai/gpt-4o-mini": {
        name: "GPT-4o Mini",
        description:
            "A lightweight and efficient version of GPT-4o, optimized for everyday tasks, processing text efficiently and generating summaries and translations quickly.",
        bestFor: [
            "Basic text processing",
            "Simple summaries",
            "Quick translations"
        ]
    },
    "deepseek/deepseek-chat": {
        name: "DeepSeek v3",
        description:
            "An advanced model with strong reasoning capabilities, ideal for solving complex problems, technical discussions, and in-depth analysis.",
        bestFor: [
            "Complex problem-solving",
            "Technical discussions",
            "In-depth analysis"
        ]
    },
    "deepseek/deepseek-r1-distill-llama-70b": {
        name: "Llama 3.3 70B (DeepSeek as Teacher)",
        description:
            "A large-scale model with a broad and diverse knowledge base, perfect for tasks requiring creativity and complex reasoning. Is a distillation of the Llama 3.3 70B model, trained by DeepSeek to improve performance.",
        bestFor: [
            "Creative writing",
            "Complex reasoning",
            "Detailed responses"
        ]
    },
    "mistralai/mistral-saba": {
        name: "Mistral Saba",
        description:
            "A balanced and versatile model, ideal for a wide range of general tasks, with strong performance in content generation and text analysis.",
        bestFor: [
            "General-purpose use",
            "Content generation",
            "Text analysis"
        ]
    },
    "mistralai/mistral-nemo": {
        name: "Mistral Nemo",
        description:
            "Specialized in technical and analytical tasks, providing superior performance in technical writing, code analysis, and data interpretation.",
        bestFor: [
            "Technical writing",
            "Code analysis",
            "Data interpretation"
        ]
    },
    "deepseek/deepseek-r1-distill-qwen-32b": {
        name: "Qwen 32B (DeepSeek as Teacher)",
        description:
            "An efficient model that delivers solid performance across various tasks, making it ideal for content processing and basic analysis. Is a distillation of the Qwen 32B model, trained by DeepSeek to improve performance.",
        bestFor: [
            "General tasks",
            "Content processing",
            "Basic analysis"
        ]
    }
} as const;


export const getModelId = (key: keyof typeof AI_MODELS) => key
export const getModelName = (key: keyof typeof AI_MODELS) => AI_MODELS[key]


