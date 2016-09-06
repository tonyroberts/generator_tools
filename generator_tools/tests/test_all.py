import unittest
import test_support
import os

class AllTest(unittest.TestCase):
    def setUp(self):
        import os
        import test_all
        setup_path = (os.sep).join(test_all.__file__.split(os.sep)[:-1])
        files = os.listdir(setup_path)
        self.test_modules = []
        for f in files:
            base, ext = os.path.splitext(f)
            if base.startswith("test_"):
                if base not in ('test_all', 'test_support') and ext == '.py':
                    self.test_modules.append(base)


    def check(self, module):
        exec "import %s; %s.test_main()"%(module, module)

    def test_all(self):
        for module in self.test_modules:
            self.check(module)


def test_main():
    test_support.run_unittest(AllTest)

if __name__ == "__main__":
    test_main()
