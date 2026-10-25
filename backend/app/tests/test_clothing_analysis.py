import json
import unittest
from unittest.mock import Mock, patch

from app.image_processing.clothing_analysis import (
    ClothingAnalysisError,
    analyze_outfit,
    analyze_clothing,
)


class ClothingAnalysisTests(unittest.TestCase):
    def _mock_response(self, result: dict) -> Mock:
        response = Mock()
        response.read.return_value = json.dumps(
            {"response": json.dumps(result)}
        ).encode("utf-8")
        context = Mock()
        context.__enter__ = Mock(return_value=response)
        context.__exit__ = Mock(return_value=None)
        return context

    @patch("app.image_processing.clothing_analysis.urlopen")
    def test_returns_validated_garment_attributes(self, urlopen: Mock) -> None:
        urlopen.return_value = self._mock_response(
            {
                "name": "Blue denim jacket",
                "category": "outerwear",
                "style": "casual",
                "gender": "unisex",
                "season": "autumn",
                "color": "navy",
            }
        )

        result = analyze_clothing(b"image bytes")

        self.assertEqual(result["name"], "Blue denim jacket")
        self.assertEqual(result["category"], "outerwear")
        self.assertEqual(result["color"], "navy")
        request = urlopen.call_args.args[0]
        request_data = json.loads(request.data)
        self.assertEqual(request_data["model"], "qwen2.5vl:3b")
        self.assertTrue(request_data["images"])

    @patch("app.image_processing.clothing_analysis.urlopen")
    def test_rejects_unsupported_categories(self, urlopen: Mock) -> None:
        urlopen.return_value = self._mock_response(
            {
                "name": "Garment",
                "category": "dress",
                "style": "casual",
                "gender": "unisex",
                "season": "all",
                "color": "blue",
            }
        )

        with self.assertRaisesRegex(ClothingAnalysisError, "unsupported category"):
            analyze_clothing(b"image bytes")

    @patch("app.image_processing.clothing_analysis.urlopen")
    def test_analyzes_a_complete_outfit(self, urlopen: Mock) -> None:
        urlopen.return_value = self._mock_response(
            {
                "summary": "A relaxed, coordinated everyday look.",
                "items": ["White shirt", "Blue jeans", "White sneakers"],
                "color_palette": "Neutral white with blue denim.",
                "strengths": ["The shoes complement the shirt."],
                "suggestions": ["Add a light jacket for cooler weather."],
            }
        )

        result = analyze_outfit(b"image bytes")

        self.assertEqual(result["summary"], "A relaxed, coordinated everyday look.")
        self.assertEqual(len(result["items"]), 3)
        request_data = json.loads(urlopen.call_args.args[0].data)
        self.assertIn("complete outfit", request_data["prompt"])

    @patch("app.image_processing.clothing_analysis.urlopen")
    def test_rejects_incomplete_outfit_analysis(self, urlopen: Mock) -> None:
        urlopen.return_value = self._mock_response(
            {
                "summary": "A coordinated look.",
                "items": ["A shirt"],
                "color_palette": "Neutral.",
                "strengths": [],
                "suggestions": ["Try a jacket."],
            }
        )

        with self.assertRaisesRegex(ClothingAnalysisError, "valid strengths"):
            analyze_outfit(b"image bytes")


if __name__ == "__main__":
    unittest.main()
