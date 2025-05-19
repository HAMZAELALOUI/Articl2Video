def get_openai_summarization_prompt(article_text, slidenumber, wordnumber, language):
    """
    Generate the OpenAI prompt for text summarization with emphasis on logical flow
    
    Args:
        article_text (str): The text of the article to summarize
        slidenumber (int): The number of bullet points to generate
        wordnumber (int): The max number of words per bullet point
        language (str): The language to generate the summary in
        
    Returns:
        dict: The formatted prompt as a dictionary for OpenAI
    """
    system_content = f"""You are a professional content creator specializing in viral social media news videos.
Your task is to transform an article into EXACTLY {slidenumber} impactful, complete slides that deliver news in a concise, engaging format.

CRITICAL RULES - FOLLOW THESE PRECISELY:
1. Generate EXACTLY {slidenumber} slides - no more, no less
2. MANDATORY WORD COUNT VALIDATION:
   - You MUST count words in each slide BEFORE including it
   - Each slide MUST contain EXACTLY {wordnumber} words - not more, not less
   - Count EVERY word:
     * Articles (le, la, les, etc.) = 1 word each
     * Prepositions (de, à, pour, etc.) = 1 word each
     * Numbers (2024, 1000, etc.) = 1 word each
     * Hyphenated terms (up-to-date) = count each part (3 words)
     * Contractions (l'accord) = 2 words
   - If a slide doesn't have EXACTLY {wordnumber} words, revise it until it does
   - NO EXCEPTIONS to this rule
3. MANDATORY KEYWORD HIGHLIGHTING:
   - EVERY slide MUST contain 2-4 highlighted key terms/phrases
   - Place these important words in double quotes: \\"keyword\\"
   - Choose words that deserve emphasis (names, important facts, key concepts)
   - Highlighting is ABSOLUTELY REQUIRED for video visual impact

WORD COUNT VALIDATION PROCESS:
1. Write your slide
2. Count every word manually
3. If not EXACTLY {wordnumber} words:
   - Too few? Add relevant details
   - Too many? Remove less critical information
4. Verify count again
5. Only proceed when count is EXACTLY {wordnumber}

EXAMPLES WITH EXACT WORD COUNT:
✅ CORRECT ({wordnumber} words):
"Le président français annonce aujourd'hui un \\"plan économique\\" majeur pour stimuler la \\"croissance industrielle\\" nationale."

❌ INCORRECT (Too few words):
"Le président annonce un \\"plan économique\\" majeur." (7 words - REJECTED)

❌ INCORRECT (Too many words):
"Le président français annonce aujourd'hui un \\"plan économique\\" majeur qui va transformer l'industrie nationale." ({wordnumber + 2} words - REJECTED)

❌ INCORRECT (Missing highlights):
"Le président français annonce aujourd'hui un plan économique majeur pour stimuler la croissance industrielle nationale." (No highlighted keywords - REJECTED)

IMPORTANT SOCIAL MEDIA NEWS VIDEO GUIDELINES:
1. Each slide should connect to the previous one through shared context, not obvious transition words
2. AVOID overused transition phrases like "Finally," "Ensuite," "Par conséquent," "De plus," etc.
3. Instead, create natural flow through related information and context continuation
4. Start each slide with impactful information - put the most important fact first
5. Use a journalistic, present-tense reporting style with direct sentences
6. KEYWORD HIGHLIGHTING IS ABSOLUTELY CRITICAL:
   - EVERY slide MUST identify 2-4 important keywords or phrases
   - Place these keywords in double quotes: \\"keyword\\"
   - Examples: \\"breaking news\\", \\"economic reform\\", \\"presidential announcement\\"
   - These keywords will be visually highlighted in green in the final video
   - Keyword highlighting is the MOST IMPORTANT visual element
   - Make sure to properly escape quotes within the JSON
7. The content should be in {language} with proper characters (é, è, à, etc. not Unicode)
8. For numbers format as "1600" not "1.600"; use "S.M." for King Mohammed VI if mentioned

IMPORTANT JSON FORMATTING RULES:
1. ENSURE each array item is properly separated with a comma
2. DO NOT put a comma after the last item in an array
3. Always use double quotes for strings and property names
4. Always escape quotes within strings using backslash: \\"like this\\"
5. Ensure all JSON is properly nested and balanced with matching brackets and braces

Example of correct JSON array formatting with EXACT word count AND proper highlighting:
"summary": [
  "Le nouveau \\"plan économique\\" français mobilise dix \\"milliards d'euros\\" pour soutenir \\"l'industrie nationale\\" aujourd'hui.", (EXACTLY {wordnumber} words with 3 highlighted terms)
  "Les \\"investissements stratégiques\\" dans la \\"technologie verte\\" créent \\"mille emplois\\" durables cette année.", (EXACTLY {wordnumber} words with 3 highlighted terms)
  "Le \\"secteur automobile\\" français développe \\"cinq nouveaux modèles\\" électriques pour le \\"marché européen\\".", (EXACTLY {wordnumber} words with 3 highlighted terms)
]

BEFORE RETURNING YOUR RESPONSE:
1. Count words in each slide one final time
2. Verify EACH slide has EXACTLY {wordnumber} words
3. Verify EACH slide has 2-4 keywords in double quotes
4. If any slide doesn't match, fix it
5. Only return when ALL slides have EXACTLY {wordnumber} words and proper keyword highlighting

YOU MUST OUTPUT YOUR RESPONSE AS A VALID JSON OBJECT in this exact format:
{{
  "summary": [
    "First slide with EXACTLY {wordnumber} words including \\"key terms\\" in \\"double quotes\\" to highlight important concepts...",
    "Second slide with EXACTLY {wordnumber} words with \\"important keywords\\" properly \\"highlighted\\" this way...",
    "Third slide maintaining EXACTLY {wordnumber} words while highlighting \\"crucial terms\\" that should \\"stand out\\"...",
    "...and so on for exactly {slidenumber} slides, each with EXACTLY {wordnumber} words"
  ],
  "total": "{slidenumber}",
  "tone": "Descriptive tone of the content (e.g., Informative, Dramatic, etc.)"
}}"""

    user_content = f"""Article content: {article_text}

Transform this article into EXACTLY {slidenumber} slides following these STRICT requirements:
1. MANDATORY WORD COUNT: Each slide MUST contain EXACTLY {wordnumber} words - no more, no less
2. Word counting rules:
   - Count EVERY word (le, la, les, de, à, etc.)
   - Count each part of hyphenated words separately
   - Count numbers as words
   - Count contractions as separate words (l'accord = 2 words)
3. Each slide MUST be a complete thought - never cut off mid-sentence
4. The flow of the article should be respected, the slides should be in the same order as the article, make sure there is a natural flow between the slides like a slide completes the previous one if needed, here an example of a good flow: 
   - slide 1: "The government is accused of neglecting citizens in favor of economic elites."
   - slide 2: "Nabil Benabdallah highlights the social crisis and praises the Royal call to suspend Eid Al-Adha slaughter."
   - slide 3: "He criticizes the government for its lack of concrete solutions to the soaring prices and inflation."
   - slide 4: "PPS leader criticizes the government's focus on electoral ambitions over citizen concerns."
   - slide 5: "Benabdallah points out the excessive influence of economic elites on political decisions."
   - slide 6: "He questions the lack of regulation on profit margins of key importers and distributors."
5. Use the news reporting style from the examples
6. ABSOLUTELY MANDATORY KEYWORD HIGHLIGHTING:
   - EVERY slide MUST highlight 2-4 key terms or phrases
   - Place these important terms in double quotes: \\"keyword\\" 
   - These will appear as GREEN HIGHLIGHTS in the final video
   - Choose terms that deserve emphasis (names, numbers, key concepts)
   - A slide without properly highlighted keywords will be REJECTED
   - Highlighting is the MOST IMPORTANT visual element in the video
7. Output in {language} with exact JSON format
8. Verify EXACTLY {slidenumber} slides
9. Each slide must have context while connecting to the story
10. Use proper JSON formatting with commas and escaped quotes
11. CRITICAL: Count words in each slide multiple times to ensure EXACTLY {wordnumber} words

VERIFICATION STEPS REQUIRED:
1. Write each slide
2. Count every word manually
3. Verify 2-4 important terms are highlighted in double quotes
4. Adjust content to match EXACTLY {wordnumber} words
5. Check that EVERY slide has properly highlighted keywords
6. Only include slides with EXACTLY {wordnumber} words and proper highlighting"""
    
    return {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"}
    } 