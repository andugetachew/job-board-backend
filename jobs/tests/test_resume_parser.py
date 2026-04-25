from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from jobs.resume_parser import parse_resume


class ResumeParserTest(TestCase):

    def test_extracts_email(self):
        file = SimpleUploadedFile("resume.txt", b"Email: john@example.com")
        result = parse_resume(file)
        self.assertEqual(result["email"], "john@example.com")

    def test_extracts_phone(self):
        file = SimpleUploadedFile("resume.txt", b"Phone: 555-123-4567")
        result = parse_resume(file)
        self.assertEqual(result["phone"], "555-123-4567")

    def test_extracts_skills(self):
        file = SimpleUploadedFile("resume.txt", b"Skills: Python, Django, React")
        result = parse_resume(file)
        self.assertIn("python", result["skills"])
        self.assertIn("django", result["skills"])

    def test_handles_missing_info(self):
        file = SimpleUploadedFile("resume.txt", b"No email or phone here")
        result = parse_resume(file)
        self.assertIsNone(result["email"])
        self.assertEqual(result["skills"], [])
