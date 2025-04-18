import json
import re

class ResponseParser:
    def parse(self, response_text):
        if not response_text:
            print("❗ Empty response text")
            return None
        
        try:
            # حذف تگ‌های اضافی یا خلاصه‌ها
            cleaned = re.sub(r"<summary>.*?</summary>", "", response_text)
            # جستجوی JSON داخل متن
            matches = re.findall(r"{.*?}", cleaned, re.DOTALL)

            for match in matches[::-1]:  # آخرین JSON رو بررسی می‌کنیم
                try:
                    data = json.loads(match)
                    return self._validate(data)
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            print(f"⚠️ Error parsing response: {e}")
            return None

        print("❗ No valid JSON found in response")
        return None

    def _validate(self, data):
        required_keys = ["Title", "Description", "Category"]
        for key in required_keys:
            if key not in data or not data[key].strip():
                print(f"❗ Missing or empty field: {key}")
                return None
        return data["Title"].strip(), data["Description"].strip(), data["Category"].strip()
