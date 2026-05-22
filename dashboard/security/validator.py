import re
import os
import html
from functools import wraps
from flask import request, abort


class InputValidator:
    MAX_TEXT_LENGTH = 10000
    MAX_TICKER_LENGTH = 20
    MAX_FILENAME_LENGTH = 255
    MAX_UPLOAD_SIZE_MB = 10

    TICKER_PATTERN = re.compile(r'^[A-Z0-9]{1,20}$')
    REFERENCE_PATTERN = re.compile(r'^SR-\d{4}-[A-Z]{2,6}-\d{3}$')
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]+$')

    SQL_INJECTION_PATTERNS = [
        r"('|(--)|;|(\b(SELECT|INSERT|UPDATE|"
        r"DELETE|DROP|CREATE|ALTER|EXEC|UNION|"
        r"FETCH|DECLARE|CAST)\b))",
    ]

    XSS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    ALLOWED_UPLOAD_EXTENSIONS = {'.pdf', '.csv', '.xlsx', '.json', '.txt'}

    @classmethod
    def sanitize_text(cls, text, max_length=None):
        if not isinstance(text, str):
            return ''
        max_len = max_length or cls.MAX_TEXT_LENGTH
        text = text[:max_len]
        text = html.escape(text)
        return text.strip()

    @classmethod
    def validate_ticker(cls, ticker):
        if not ticker:
            abort(400, "Ticker is required")
        ticker = ticker.upper().strip()[:20]
        if not cls.TICKER_PATTERN.match(ticker):
            abort(400, "Invalid ticker format")
        return ticker

    @classmethod
    def validate_float(cls, value, min_val=0, max_val=10000, name='value'):
        try:
            f = float(value)
            if not (min_val <= f <= max_val):
                abort(400, f"{name} must be between {min_val} and {max_val}")
            return f
        except (TypeError, ValueError):
            abort(400, f"Invalid {name}: must be a number")

    @classmethod
    def check_sql_injection(cls, text):
        text_upper = text.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_xss(cls, text):
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def validate_request_body(cls, data, required, optional=None):
        if not isinstance(data, dict):
            abort(400, "Invalid request body")
        for field in required:
            if field not in data:
                abort(400, f"Missing required field: {field}")
        clean = {}
        allowed = required + (optional or [])
        for key in allowed:
            if key in data:
                val = data[key]
                if isinstance(val, str):
                    if cls.check_sql_injection(val):
                        abort(400, "Invalid input detected")
                    if cls.check_xss(val):
                        abort(400, "Invalid input detected")
                    clean[key] = cls.sanitize_text(val)
                elif isinstance(val, (int, float)):
                    clean[key] = val
                else:
                    clean[key] = val
        return clean

    @classmethod
    def validate_file_upload(cls, file):
        if not file:
            abort(400, "No file provided")
        filename = file.filename
        if not filename:
            abort(400, "No filename")
        ext = os.path.splitext(filename)[1].lower()
        if ext not in cls.ALLOWED_UPLOAD_EXTENSIONS and ext != '':
            abort(400, f"File type {ext} not allowed. Allowed: {cls.ALLOWED_UPLOAD_EXTENSIONS}")
        safe_name = os.path.basename(filename)
        if len(safe_name) > cls.MAX_FILENAME_LENGTH:
            abort(400, "Filename too long")
        return True


def validate_ticker(ticker):
    return InputValidator.validate_ticker(ticker)


def sanitize_text(text, max_length=None):
    return InputValidator.sanitize_text(text, max_length)
