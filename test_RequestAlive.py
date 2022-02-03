import unittest, time, json, os
from requestAlive import getLastTimeout

class TimeoutTestCase(unittest.TestCase):

    def test_getLastTimeout(self):
        timeoutVal = 5
        testFilename = "testtimeout.json"
        with open(testFilename, 'w') as output_file:
            json.dump([], output_file, ensure_ascii=False, indent=4)
        time.sleep(timeoutVal)
        result = getLastTimeout(testFilename)
        self.assertEqual(5, round(time.time()-result))
        os.remove(testFilename)

    def test_nofile(self):
        testFilename = "nofile.json"
        result = getLastTimeout(testFilename)
        self.assertEqual(0, result)

# Executing the tests in the above test case class
if __name__ == "__main__":
  unittest.main()