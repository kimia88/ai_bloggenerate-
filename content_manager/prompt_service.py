class PromptService:
    def complete_content_prompt(self, title=None, description=None):
        prompt = """Complete the following content data. Fill in any missing fields and return ONLY a valid JSON like this:

{
    "Title": "string",
    "Description": "string",
    "Category": "string"
}

Requirements:
- If a field already exists, keep it unchanged.
- Fill in the missing fields based on the available ones.
- Do NOT include any explanation, markdown, or formatting.
- Return ONLY the JSON object.

"""
        if title:
            prompt += f"Title: {title}\n"
        if description:
            prompt += f"Description: {description}\n"

        return prompt.strip()
