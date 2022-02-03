import unittest
from utils import datePeriodName

class DatePeriodNameTestCase(unittest.TestCase):

    def test_days(self):
        self.assertEqual('5 дней', ''.join(datePeriodName({'d':5})))

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()