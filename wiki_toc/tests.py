import unittest

from pyramid import testing

def get_dummy_soup(url):
    """ This function will be used to bypass the call to urllib2 in views.get_soup and return some predefined html
    """
    if not url or not url.endswith("en.wikipedia.org/wiki/Satchel"):
        if url and url.endswith("test_url_error"):
            from urllib2 import URLError
            raise URLError(str(url))
        else:
            raise Exception(str(url))
            
    from bs4 import BeautifulSoup
    html = """<div id="toc" class="toc">
<div id="toctitle">
<h2>Contents</h2>
</div>
<ul>
<li class="toclevel-1 tocsection-1"><a href="#History"><span class="tocnumber">1</span> <span class="toctext">History</span></a></li>
<li class="toclevel-1 tocsection-2"><a href="#School_bag"><span class="tocnumber">2</span> <span class="toctext">School bag</span></a></li>
<li class="toclevel-1 tocsection-3"><a href="#In_fashion"><span class="tocnumber">3</span> <span class="toctext">In fashion</span></a></li>
<li class="toclevel-1 tocsection-4"><a href="#In_popular_culture"><span class="tocnumber">4</span> <span class="toctext">In popular culture</span></a></li>
<li class="toclevel-1 tocsection-5"><a href="#See_also"><span class="tocnumber">5</span> <span class="toctext">See also</span></a></li>
<li class="toclevel-1 tocsection-6"><a href="#References"><span class="tocnumber">6</span> <span class="toctext">References</span></a></li>
</ul>
</div>"""
    return BeautifulSoup(html, 'lxml')

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()
        self.config.add_route('choose_wiki_page', '/')                           # The default page where the user chooses the Wikipaedia TOC to view
        self.config.add_route('wiki_toc', '/wiki_toc/*wiki_location')

    def tearDown(self):
        testing.tearDown()

    def test_choose_wiki_page(self):
        from .views import choose_wiki_page
        from pyramid.httpexceptions import HTTPFound
        request = testing.DummyRequest()
        
        # Test the form view
        info = choose_wiki_page(request)
        self.assertEqual(info['title'], 'Table of Contents Scraper')
        self.assertEqual(info['errors'], [])
        self.assertEqual(info['post_url'], request.route_url('choose_wiki_page'))
        
        # Test the form processing
        request.POST["target_wiki_page"] = "https://en.wikipedia.org/wiki/Satchel"
        self.assertRaises(HTTPFound, choose_wiki_page, request)

    def test_wiki_toc(self):
        from . import views
        # Make sure to bypass urllib2
        views.get_soup=get_dummy_soup
        request = testing.DummyRequest()
        
        # Test with a blank wiki_location
        request.matchdict["wiki_location"] = ''
        info = views.wiki_toc(request)
        self.assertEqual(info['title'], 'No wikipedia page provided')
        self.assertEqual(info['toc'], '')
        self.assertEqual(info['errors'], ['No wikipedia location has been provided.'])
        
        # Test with a valid wikipedia path
        request.matchdict["wiki_location"] = ('en.wikipedia.org', 'wiki', 'Satchel')
        info = views.wiki_toc(request)
        self.assertEqual(info['title'], 'en.wikipedia.org/wiki/Satchel')
        self.assertEqual(str(info['toc']), """<div class="toc" id="toc">
<div id="toctitle">
<h2>Contents</h2>
</div>
<ul>
<li class="toclevel-1 tocsection-1"><a href="https://en.wikipedia.org/wiki/Satchel#History" target="_NEW"><span class="tocnumber">1</span> <span class="toctext">History</span></a></li>
<li class="toclevel-1 tocsection-2"><a href="https://en.wikipedia.org/wiki/Satchel#School_bag" target="_NEW"><span class="tocnumber">2</span> <span class="toctext">School bag</span></a></li>
<li class="toclevel-1 tocsection-3"><a href="https://en.wikipedia.org/wiki/Satchel#In_fashion" target="_NEW"><span class="tocnumber">3</span> <span class="toctext">In fashion</span></a></li>
<li class="toclevel-1 tocsection-4"><a href="https://en.wikipedia.org/wiki/Satchel#In_popular_culture" target="_NEW"><span class="tocnumber">4</span> <span class="toctext">In popular culture</span></a></li>
<li class="toclevel-1 tocsection-5"><a href="https://en.wikipedia.org/wiki/Satchel#See_also" target="_NEW"><span class="tocnumber">5</span> <span class="toctext">See also</span></a></li>
<li class="toclevel-1 tocsection-6"><a href="https://en.wikipedia.org/wiki/Satchel#References" target="_NEW"><span class="tocnumber">6</span> <span class="toctext">References</span></a></li>
</ul>
</div>""")
        self.assertEqual(info['errors'], [])
        
        # Test urllib2 errors are caught and handled correctly
        request.matchdict["wiki_location"] = ('test_url_error',)
        info = views.wiki_toc(request)
        self.assertEqual(info['title'], 'test_url_error')
        self.assertEqual(str(info['toc']), "")
        self.assertEqual(info['errors'], ["The url 'test_url_error' does not appear to be valid"])

        request.matchdict["wiki_location"] = ('test_any_error',)
        info = views.wiki_toc(request)
        self.assertEqual(info['title'], 'test_any_error')
        self.assertEqual(str(info['toc']), "")
        self.assertEqual(info['errors'], ["Could not get the table of contents for 'test_any_error'"])
        
