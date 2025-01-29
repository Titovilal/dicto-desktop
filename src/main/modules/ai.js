import Anthropic from '@anthropic-ai/sdk'

export async function processWithAI(text, prompt) {
  try {
    const anthropic = new Anthropic({
      apiKey:
        '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'
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

    const response = await anthropic.messages.create({
      model: 'claude-3-5-haiku-latest',
      max_tokens: 4000,
      system: systemPrompt,
      messages: [{ role: 'user', content: text }],
      temperature: 0.3
    })

    // Extract only the content between <output> tags
    const content = response.content[0].text
    const outputMatch = content.match(/<output>([\s\S]*)<\/output>/)
    return outputMatch ? outputMatch[1].trim() : content.trim()
  } catch (error) {
    console.error('AI Processing Error:', error)
    throw error
  }
}
