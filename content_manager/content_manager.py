import json
from difflib import get_close_matches
from content_manager.llm_service import QService
from content_manager.sql_server_database import SQLServerDatabase

MAX_TITLE_LENGTH = 100
DEFAULT_TITLE = "Untitled Content"

class ContentManager:
    def __init__(self, session_hash, db_instance):
        self.q_service = QService(session_hash)
        self.db = db_instance
        self.categories = {}

    def fetch_categories(self):
        self.categories = {title: cid for cid, title in self.db.get_category()}

    def title_generator_prompt(self, description):
        return f"""
        Create a concise, engaging title (maximum {MAX_TITLE_LENGTH} characters) that accurately represents the following content.
        Provide only the title text without any additional formatting, explanations, or quotation marks.

        Content: {description}
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
        """

    def complete_prompt(self, title=None, description=None):
        base = """Complete the following content data. Fill in any missing fields and return ONLY a valid JSON like this:

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
            base += f"Title: {title}\n"
        if description:
            base += f"Description: {description}\n"
        return base.strip()

    def parse_response(self, response_text):
        try:
            if not response_text.strip():
                print("❗ Response is empty")
                return None

            response_text = response_text.replace('\r\n', '\n').strip()
            if "Final Output" in response_text:
                response_text = response_text.split("Final Output", 1)[-1].strip()

            json_objects = []
            start_pos = 0
            while True:
                start = response_text.find('{', start_pos)
                if start == -1:
                    break
                end = response_text.find('}', start) + 1
                if end == 0:
                    break
                json_str = response_text[start:end]
                try:
                    data = json.loads(json_str)
                    json_objects.append(data)
                except json.JSONDecodeError:
                    pass
                start_pos = end

            if json_objects:
                return self._validate_response_data(json_objects[-1])
            return None

        except Exception as e:
            print(f"❗ Error in parse_response: {e}")
            return None

    def _validate_response_data(self, data):
        try:
            title = data.get("Title", "").strip()
            description = data.get("Description", "").strip()
            category = data.get("Category", "").strip()

            if not any([title, description, category]):
                return None
            return title, description, category
        except Exception as e:
            print(f"❗ Validation error: {e}")
            return None

    def find_best_category_match(self, target_category):
        target_lower = target_category.lower().strip()
        available_categories = [cat.lower() for cat in self.categories.keys()]
        original_case_map = {cat.lower(): cat for cat in self.categories.keys()}

        if target_lower in available_categories:
            return original_case_map[target_lower]

        matches = get_close_matches(target_lower, available_categories, n=3, cutoff=0.4)
        partial_matches = [cat for cat in available_categories if target_lower in cat or cat in target_lower]
        unique_matches = list(dict.fromkeys(matches + partial_matches))

        if unique_matches:
            return original_case_map[unique_matches[0]]
        return None

    def complete_missing_fields(self, content_id, title=None, description=None):
        print(f"\n🔄 Completing missing fields for content ID {content_id}...")
        prompt = self.complete_prompt(title=title, description=description)

        self.q_service.send_request(prompt)
        response = self.q_service.get_response()
        result = self.parse_response(response)

        if result and isinstance(result, tuple):
            title_out, description_out, category_title = result

            if not title:
                title_out = title_out[:MAX_TITLE_LENGTH]

            best_match = self.find_best_category_match(category_title)
            if best_match:
                category_id = self.categories[best_match]
            else:
                category_id = self.db.insert_category(category_title)
                self.categories[category_title] = category_id

            self.db.update_pure_content(
                content_id,
                title=title_out,
                description=description_out,
                content_category_id=category_id
            )
            print(f"✅ Content ID {content_id} updated.")
        else:
            print(f"❌ Could not update content ID {content_id}.")

    def process_incomplete_contents(self):
        try:
            self.db.connect()
            self.fetch_categories()

            # مواردی که title ندارن اما description دارن
            null_title = self.db.get_purecontent_with_null_title()
            for content_id, description in null_title:
                if description:
                    self.complete_missing_fields(content_id, description=description)
                else:
                    self.db.update_pure_content(content_id, title=DEFAULT_TITLE)
                    print(f"⚠️ No description found for content ID {content_id}, set default title.")

            # مواردی که description ندارن اما title دارن
            null_desc = self.db.get_purecontent_without_description()
            for content_id, title in null_desc:
                if title:
                    self.complete_missing_fields(content_id, title=title)

            # مواردی که title خالی یا نامعتبره
            empty_title = self.db.get_purecontent_with_empty_title()
            for content_id, description in empty_title:
                if description:
                    self.complete_missing_fields(content_id, description=description)
                else:
                    self.db.update_pure_content(content_id, title=DEFAULT_TITLE)
                    print(f"⚠️ No description found for content ID {content_id}, set default title.")

        except Exception as e:
            print(f"❗ Error in process_incomplete_contents: {e}")
        finally:
            self.db.disconnect()
            print("✅ Database connection closed.")
