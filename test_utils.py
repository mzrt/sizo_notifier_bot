import unittest
from utils import datePeriodName, weekDayStr

class DatePeriodNameTestCase(unittest.TestCase):

    def test_days(self):
        self.assertEqual('5 дней', ''.join(datePeriodName({'d':5})))
    def test_weekDayName(self):
        self.assertEqual('понедельник', weekDayStr('07.02.2022'))
        self.assertEqual('понедельник', weekDayStr('7.2.2022'))
        self.assertEqual('воскресенье', weekDayStr('13.2.2022'))

# Executing the tests in the above test case class
if __name__ == "__main__":
    unittest.main()