import unittest

from pyramid import testing


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def choose_wiki_page(self):
        from .views import choose_wiki_page
        request = testing.DummyRequest()
        info = choose_wiki_page(request)
        #self.assertEqual(info['project'], 'wiki_toc')
