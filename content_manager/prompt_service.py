class PromptService:
    def title_generator_prompt(self, description):
        return f"""
        Create a concise, engaging title (maximum 100 characters) that accurately represents the following content.
        Provide only the title text without any additional formatting, explanations, or quotation marks.

        Content: {description}

        Requirements:
        - Maximum 100 characters
        - Clear and descriptive
        - No introductory phrases
        - No quotation marks
        - Just the title text
        """

    def prompt_generator(self, title):
        return f"""
        Provide the response in EXACTLY this JSON format with NO other text:
        {{
            "Title": "string",
            "Description": "string",
            "Category": "string"
        }}
    
        Title: {title}
    
        Requirements:
        - Only output the JSON object
        - No additional commentary
        - No markdown formatting
        - No code blocks
        """
