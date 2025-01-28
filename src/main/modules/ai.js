import OpenAI from 'openai'
export async function processWithAI(text, prompt) {
  try {
    const openai = new OpenAI({
      baseURL: 'https://api.deepseek.com',
      apiKey: 'sk-da6f9635b42248118ecdbe813d7461d4'
    })

    const systemPrompt = `Your task is to rewrite the provided text following these strict rules:

FORMATTING RULES:
1. Keep EXACTLY the same language as the original text
2. Preserve the speaker's general tone and style
3. Maintain technical terms, proper names, and specific references
4. Keep the original paragraph structure

PROCESSING INSTRUCTIONS:
${prompt}

CRITICAL CONSTRAINTS:
- ONLY return the processed text
- DO NOT add comments, explanations, or notes
- DO NOT use phrases like "Here's the text..." or "I have rewritten..."
- DO NOT include prefixes, suffixes, or format markers
- DO NOT make assumptions beyond the given instructions

OUTPUT FORMAT:
<output>
[Processed text following instructions]
</output>

If the original text is empty or invalid, return an empty string "".`

    const completion = await openai.chat.completions.create({
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: text }
      ],
      model: 'deepseek-chat',
      temperature: 0.3, // Reduced for better consistency
      max_tokens: 2000,
      presence_penalty: -0.5, // Discourages deviations from original content
      frequency_penalty: 0.3 // Prevents excessive repetition
    })

    // Extract only the content between <output> tags
    const response = completion.choices[0].message.content
    const outputMatch = response.match(/<output>([\s\S]*)<\/output>/)
    return outputMatch ? outputMatch[1].trim() : response.trim()
  } catch (error) {
    console.error('AI Processing Error:', error)
    throw error
  }
}
