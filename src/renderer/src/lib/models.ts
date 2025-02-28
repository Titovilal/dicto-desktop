export const AI_MODELS = {
    // Google
    "google/gemini-2.0-flash-001": "Gemini Flash 2.0",
    // Deepseek
    "deepseek/deepseek-chat": "DeepSeek R1",
    // OpenAI
    "openai/o3-mini": "o3 Mini",
    "openai/o3-mini-high": "o3 Mini High",
    "openai/gpt-4o-mini": "GPT-4o Mini",
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
            "Superior, fast and efficient model with exceptional capabilities across all tasks. The default choice for most use cases, combining speed with high-quality outputs.",
        bestFor: [
            "Very quick responses",
            "Time-sensitive tasks",
            "General-purpose use",
            "Code generation",
            "Complex reasoning"
        ]
    },

    "deepseek/deepseek-chat": {
        name: "DeepSeek V3",
        description:
            "Capable model with good performance but not as strong as Gemini Flash 2.0 across most tasks. Features a warmer communication style and performs adequately for many purposes. Takes slightly longer to respond than Gemini Flash.",
        bestFor: [
            "Conversational interactions",
            "Basic problem-solving",
            "Situations preferring a warmer tone",
            "Secondary option when results from Gemini aren't satisfactory"
        ]
    },
    "openai/o3-mini": {
        name: "o3 Mini",
        description:
            "Model with strong chain-of-thought reasoning that produces higher quality responses but with longer response times. Particularly strong with mathematical problems. Consider using when Gemini Flash or DeepSeek V3 haven't succeeded.",
        bestFor: [
            "Mathematical calculations and proofs",
            "Difficult reasoning tasks",
            "High-quality responses",
            "Situations where response time isn't critical"
        ]
    },
    "openai/o3-mini-high": {
        name: "o3 Mini High",
        description:
            "Premium version of o3 Mini with even more thorough chain-of-thought reasoning, resulting in significantly longer response times but superior response quality. Excellent for complex mathematics and programming tasks, but should only be used when other models haven't delivered satisfactory results.",
        bestFor: [
            "Advanced mathematics",
            "Advanced programming tasks",
            "Complex logical problems",
            "Highest quality outputs",
            "Situations where wait time isn't an issue"
        ]
    },
    "openai/gpt-4o-mini": {
        name: "GPT-4o Mini",
        description:
            "Similar to Gemini Flash, but with slightly less reasoning capabilities.",
        bestFor: [
            "Basic text processing",
            "Simple summaries",
            "Quick translations"
        ]
    },


} as const;


export const getModelId = (key: keyof typeof AI_MODELS) => key
export const getModelName = (key: keyof typeof AI_MODELS) => AI_MODELS[key]