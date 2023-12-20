import unittest
from poracle_server import check_padding

class TestOracle(unittest.TestCase):

    def test_check_padding(self):
        
        test1 = b"\x00" * 16
        test2 = b"\x10" * 16
        test3 = b"\xf0" + b"\x0f" * 15
        test4 = b"\x01" * 16
        test5 = b"\x04" * 14 + b"\x03" * 2

        result = not check_padding(test1) and check_padding(test2) and check_padding(test3) and check_padding(test4) and not check_padding(test5)

        self.assertEqual(result, True)


if __name__ == "__main__":
    unittest.main()