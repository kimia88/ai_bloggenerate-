import json
from difflib import get_close_matches
from content_manager.llm_service import QService
from content_manager.sql_server_database import SQLServerDatabase

# Constants
MAX_TITLE_LENGTH = 100
DEFAULT_TITLE = "Untitled Content"
JSON_FORMAT = {
    "Title": "",
    "Description": "",
    "Category": ""
}

class ContentManager:
    def __init__(self, session_hash, db_instance):
        self.q_service = QService(session_hash)
        self.db = db_instance
        self.categories = {}

    def fetch_categories(self):
        """دریافت لیست دسته‌بندی‌ها از دیتابیس"""
        self.categories = {title: cid for cid, title in self.db.get_category()}

    def prompt_generator(self, title):
        """تولید پرامپت برای تولید توضیحات برای عنوان محتوا"""
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

    def title_generator_prompt(self, description):
        """تولید پرامپت برای تولید عنوان بر اساس توضیحات"""
        return f"""
        Create a concise, engaging title (maximum {MAX_TITLE_LENGTH} characters) that accurately represents the following content.
        Provide only the title text without any additional formatting, explanations, or quotation marks.

        Content: {description}

        Requirements:
        - Maximum {MAX_TITLE_LENGTH} characters
        - Clear and descriptive
        - No introductory phrases
        - No quotation marks
        - Just the title text
        """

    def parse_response(self, response_text):
        """تجزیه و تحلیل پاسخ JSON و استخراج داده‌ها"""
        try:
            if not response_text.strip():
                print("❗ Response is empty")
                return None

            print(f"📥 Raw response: {response_text}")

            # Standardize line endings and remove leading/trailing whitespace
            response_text = response_text.replace('\r\n', '\n').strip()

            # Handle cases where the response contains "Final Output" marker
            if "Final Output" in response_text:
                response_text = response_text.split("Final Output", 1)[-1].strip()

            # Find all JSON objects in the response
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
                # Use the last complete JSON object found
                print(f"✅ Parsed JSON successfully: {json_objects[-1]}")
                return self._validate_response_data(json_objects[-1])

            print("❗ Could not extract valid JSON from response")
            return None

        except Exception as e:
            print(f"❗ Unexpected error in parse_response: {e}")
            return None

    def _validate_response_data(self, data):
        """تأیید صحت داده‌های استخراج‌شده"""
        try:
            title = data.get("Title", "").strip()
            description = data.get("Description", "").strip()
            category = data.get("Category", "").strip()

            if not all([title, description, category]):
                print(f"❗ Missing required fields - Title: '{title}', Description: '{description}', Category: '{category}'")
                return None

            return title, description, category
        except Exception as e:
            print(f"❗ Validation error: {e}")
            return None

    def find_best_category_match(self, target_category):
        """یافتن بهترین تطابق با دسته‌بندی موجود"""
        target_lower = target_category.lower().strip()
        available_categories = [cat.lower() for cat in self.categories.keys()]
        original_case_map = {cat.lower(): cat for cat in self.categories.keys()}

        print(f"🔍 Searching for category: '{target_category}'")
        print(f"Available categories: {list(self.categories.keys())}")

        # Try exact match (case insensitive)
        if target_lower in available_categories:
            print(f"✅ Found exact match (case insensitive): '{target_category}'")
            return original_case_map[target_lower]

        # Try close matches using fuzzy matching
        matches = get_close_matches(
            target_lower, 
            available_categories, 
            n=3,
            cutoff=0.4
        )

        # Also check for partial matches
        partial_matches = [
            cat for cat in available_categories 
            if target_lower in cat or cat in target_lower
        ]

        # Combine and deduplicate matches
        all_matches = matches + partial_matches
        unique_matches = list(dict.fromkeys(all_matches))

        if unique_matches:
            best_match = original_case_map[unique_matches[0]]
            print(f"⚠️ Using closest match: '{target_category}' → '{best_match}'")
            return best_match

        print(f"❗ No suitable match found for category '{target_category}'")
        return None

    def process_contents(self):
        """پردازش محتواهای موجود در دیتابیس"""
        connection_established = False
        try:
            self.db.connect()
            connection_established = True
            self.fetch_categories()

            # First handle entries with NULL titles
            null_title_contents = self.db.get_purecontent_with_null_title()
            for content_id, description in null_title_contents:
                print(f"\n⚠️ Found content with NULL title (ID: {content_id})")
                if description:
                    print("Generating title from description...")
                    prompt = self.title_generator_prompt(description)
                    self.q_service.send_request(prompt)
                    response = self.q_service.get_response()
                    title = self.parse_response(response)

                    if title:
                        title = title.strip().strip('"').strip("'")
                        if len(title) > MAX_TITLE_LENGTH:
                            title = title[:MAX_TITLE_LENGTH].strip()
                        self.db.update_pure_content(content_id, title=title)
                        print(f"✅ Generated and set title for content ID {content_id}: '{title}'")
                    else:
                        self.db.update_pure_content(content_id, title=DEFAULT_TITLE)
                        print(f"⚠️ Could not generate title, set to default for content ID {content_id}")
                else:
                    self.db.update_pure_content(content_id, title=DEFAULT_TITLE)
                    print(f"⚠️ No description available, set default title for content ID {content_id}")

            # Then handle entries with empty or invalid titles
            empty_title_contents = self.db.get_purecontent_with_empty_title()
            for content_id, description in empty_title_contents:
                print(f"\n⚠️ Found content with empty/invalid title (ID: {content_id})")
                if description:
                    print("Generating proper title from description...")
                    prompt = self.title_generator_prompt(description)
                    self.q_service.send_request(prompt)
                    response = self.q_service.get_response()
                    title = self.parse_response(response)

                    if title:
                        title = title.strip().strip('"').strip("'")
                        if len(title) > MAX_TITLE_LENGTH:
                            title = title[:MAX_TITLE_LENGTH].strip()
                        self.db.update_pure_content(content_id, title=title)
                        print(f"✅ Generated and set proper title for content ID {content_id}: '{title}'")
                    else:
                        self.db.update_pure_content(content_id, title=DEFAULT_TITLE)
                        print(f"⚠️ Could not generate title, set to default for content ID {content_id}")
                else:
                    self.db.update_pure_content(content_id, title=DEFAULT_TITLE)
                    print(f"⚠️ No description available, set default title for content ID {content_id}")

            # Process entries missing a description (with valid titles)
            contents = self.db.get_purecontent_without_description()
            for content_id, title in contents:
                print(f"\n📝 Processing description for: {title} (ID: {content_id})")
                prompt = self.prompt_generator(title)

                self.q_service.send_request(prompt)
                response = self.q_service.get_response()
                result = self.parse_response(response)

                if result and isinstance(result, tuple):
                    _, description, category_title = result

                    best_match = self.find_best_category_match(category_title)
                    if best_match:
                        category_id = self.categories[best_match]
                        self.db.update_pure_content(content_id, description=description, content_category_id=category_id)
                        print(f"✅ Updated content ID {content_id} with description and category '{best_match}'.")
                    else:
                        print(f"⚠️ No suitable category found for '{category_title}', inserting new category...")
                        # Adding a new category if no match found
                        new_category_id = self.db.insert_category(category_title)
                        if new_category_id:
                            self.categories[category_title] = new_category_id  # Update categories list
                            self.db.update_pure_content(content_id, description=description, content_category_id=new_category_id)
                            print(f"✅ Inserted new category '{category_title}' and updated content ID {content_id}.")
                        else:
                            # If category insert failed, just update description
                            self.db.update_pure_content(content_id, description=description)
                            print(f"⚠️ Failed to insert new category. Updated description only for content ID {content_id}.")
                else:
                    print(f"❌ Skipped content ID {content_id} due to invalid response.")

        except Exception as e:
            print(f"❗ Error in process_contents: {str(e)}")
            if connection_established:
                self.db.disconnect()
                print("Database connection closed due to error.")
            raise

        finally:
            if connection_established:
                self.db.disconnect()
                print("Database connection closed normally.")
