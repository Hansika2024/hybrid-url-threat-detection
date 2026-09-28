import unittest


class TestHealth(unittest.TestCase):

    def test_health_response(self):
        response = {
            "status": "healthy"
        }

        self.assertEqual(response["status"], "healthy")


if __name__ == "__main__":
    unittest.main()