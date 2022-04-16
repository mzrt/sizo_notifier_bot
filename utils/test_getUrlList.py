import unittest
import io
from lxml import html
from getUrlList import getParselUrls, getRegions

class UrlListTestCase(unittest.TestCase):

    def read_file(self, path):
        with io.open(path, 'r', encoding="utf-8") as fp:
            # считываем сразу весь файл
            return fp.read()


    def test_parseldays(self):
        data = self.read_file('./test_data/html/parsel01.html')
        if(len(data)>0):
            tree = html.fromstring(data)
            urls = getParselUrls(tree)
        self.assertEqual('/base/novosibirsk/s2kuibishev?sub=order&date=2022-04-06&t=15&ss=3505', urls[0])
        self.assertEqual(19, len(urls))
        self.assertEqual('/base/novosibirsk/s2kuibishev?sub=order&date=2022-04-27&t=15&ss=3505', urls[18])

    def test_regions(self):
        data = self.read_file('./test_data/html/regions.html')
        if(len(data)>0):
            tree = html.fromstring(data)
            regions = getRegions(tree)
        self.assertEqual('/base/novosibirsk/s2kuibishev?sub=order&date=2022-04-06&t=15&ss=3505', regions[0])
        self.assertEqual(19, len(regions))

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()