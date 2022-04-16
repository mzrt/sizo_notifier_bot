import unittest
import io
from lxml import html
from utils.date import datePeriodName
from utils.getUrlList import getParselUrls

class DatePeriodNameTestCase(unittest.TestCase):

    def test_days(self):
        self.assertEqual('5 дней', ''.join(datePeriodName({'d':5})))

    def test_parseldays(self):
        with io.open('./test_data/html/parsel01.html', 'r', encoding="utf-8") as fp:
            # считываем сразу весь файл
            data = fp.read()
        if(len(data)>0):
            tree = html.fromstring(data)
            urls = getParselUrls(tree)
        self.assertEqual('/base/novosibirsk/s2kuibishev?sub=order&date=2022-04-06&t=15&ss=3505', urls[0])
        self.assertEqual(19, len(urls))
        self.assertEqual('/base/novosibirsk/s2kuibishev?sub=order&date=2022-04-27&t=15&ss=3505', urls[18])

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()