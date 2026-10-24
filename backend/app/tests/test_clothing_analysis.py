import json
import unittest
from unittest.mock import Mock, patch

from app.image_processing.clothing_analysis import (
    ClothingAnalysisError,
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


if __name__ == "__main__":
    unittest.main()
