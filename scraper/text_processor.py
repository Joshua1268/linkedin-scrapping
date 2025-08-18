import re
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta


class TextProcessor:
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f700-\U0001f77f"
        "\U0001f780-\U0001f7ff"
        "\U0001f800-\U0001f8ff"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\U00002700-\U000027bf"
        "\U00002600-\U000026ff"
        "]+",
        flags=re.UNICODE,
    )

    def clean(self, text):
        if not text:
            return ""
        text = self.EMOJI_PATTERN.sub("", text)
        return text.strip()

    def extract_email(self, text):
        match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        return match.group(0) if match else None

    def parse_relative_date(self, date_str):
        now = datetime.now()
        try:
            date_str = date_str.strip()
            if any(x in date_str for x in ["h", "m", "now", "l'instant"]):
                return now.strftime("%Y-%m-%d")
            elif "j" in date_str or "d" in date_str:
                val = int(re.search(r"(\d+)", date_str).group(1))
                return (now - timedelta(days=val)).strftime("%Y-%m-%d")
            elif "sem" in date_str or "w" in date_str:
                val = int(re.search(r"(\d+)", date_str).group(1))
                return (now - timedelta(weeks=val)).strftime("%Y-%m-%d")
            elif "mois" in date_str or "mo" in date_str:
                val = int(re.search(r"(\d+)", date_str).group(1))
                return (now - relativedelta(months=val)).strftime("%Y-%m-%d")
            elif "an" in date_str or "y" in date_str:
                val = int(re.search(r"(\d+)", date_str).group(1))
                return (now - relativedelta(years=val)).strftime("%Y-%m-%d")
        except Exception:
            pass
        return now.strftime("%Y-%m-%d")
