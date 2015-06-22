from pyramid.view import view_config
from pyramid import httpexceptions as exc
import urlparse
import urllib2
from bs4 import BeautifulSoup
import logging

# For this example app, there is no database so many of the paremters below are hardcoded throughout the app
# even though it would be more useful to derive them from database configuration
default_template_parameters = dict(
    title = "Table of Contents Scraper",
    errors = None
)

wikipedia_scheme = "https://"
wikipedia_domain = "wikipedia.org"

class UrlManager(object):
    """ A simple helper class which provides functions for interogating and modifying urls
    """

    def __init__(self, url, fallback_scheme=None, fallback_netloc=None):
        # First check whether this url starts with 'http'. If it doesn't and there is a fallback scheme, attempt prepend this to the url
        # Note that url may remain unchanged even if it does meet this first condition
        if not url.startswith("http") and fallback_scheme:
            # If url[0] is '/', attempt to treat url as a relative url
            if url[0] == '/':
                # Since this is meant to be a relative url, require a fallback_netloc or do nothing
                if fallback_netloc:
                    url = fallback_scheme + fallback_netloc + url
            else:
                # This is to be treated as a full url so just prepend the scheme
                url = fallback_scheme + url
        self._urlobj = urlparse.urlparse(url)

    def matches_domain(self, domain):
        """ Returns true if this instance's url points to the given domain.
        """
        return self._urlobj.netloc and self._urlobj.netloc.endswith(domain)

    def url_is_relative(self):
        """ Returns true if the url for this instance does not identify a website and web protocol
        """
        return not self._urlobj.netloc

    def to_list(self):
        return list(self._urlobj)

    def absolute_url(self, reference_url_object):
        """ Given a reference url object, provide any of the following values, if they are missing: scheme, netloc, relative path, query string
            reference_url_object should be an instance of urlparse.ParseResult or an equivalent object
            This way href="#introduction" becomes href="<full path># introduction"
        """
        # Convert the url object for this instance to a list
        result = list(self._urlobj)

        # Now provide any missing url components using the reference url object
        if not self._urlobj.scheme:
            result[0] = reference_url_object.scheme
        if not self._urlobj.netloc:
            result[1] = reference_url_object.netloc
        if not self._urlobj.path:
            result[2] = reference_url_object.path
        if not self._urlobj.query:
            result[4] = reference_url_object.query

        # Return the result list converted to a url
        return urlparse.urlunparse(result)

def get_wiki_page_redirect(request, errors):
    """ This page accepts a form post containing the value 'target_wiki_page' and redirects to a site page matching the relative url of the wikipedia page
        eg: 'https://en.wikipedia.org/wiki/Stuff' becomes '<site url>/wiki_toc/en.wikipedia.org/wiki/Stuff'
            The browser is redirected to the resulting site url, which matches the site route 'wiki_toc'

        Remapping the relative URL in this way avoids using a session to keep track of the currently viewable table of contents.
    """
    if not request.POST:
        # There is no post so there will be no need to redirect to a TOC view page
        return None

    target_wiki_page = request.POST.get('target_wiki_page', None)
    if not target_wiki_page:
        # There is a problem with the form post so return an internal server error
        return exc.HTTPInternalServerError("Cannot locate the wikipedia page for unspecified location.")

    # There is a post specifying a target page
    try:
        # Create an instance of UrlManager with fallback options for creating a full url from a partial one
        # Eg: if '/wiki/Satchel' is provided convert it into 'https://wikipedia.org/wiki/Satchel'
        #     if 'wiki/Satchel' is provided, assume that 'wiki' is the netloc
        url_manager = UrlManager(target_wiki_page, fallback_scheme=wikipedia_scheme, fallback_netloc=wikipedia_domain)

        if url_manager.matches_domain(wikipedia_domain):
            # Convert url_manager to a list and set its scheme to ''
            url_parts = url_manager.to_list()
            url_parts[0] = ""
            # With the scheme removed, calculate a relative url path to the resource
            wiki_location = urlparse.urlunparse(url_parts).strip("/")
            return exc.HTTPFound(request.route_url("wiki_toc", wiki_location=wiki_location))
        else:
            logging.error("User supplied url, '%s', is not a valid wikipedia url.", target_wiki_page)
            errors.append("'%s' is not a valid wikipedia url. Please try again." % target_wiki_page)
    except BaseException, e:
        # An unexpected error has occurred. Remain on the current page and display the error.
        logging.error("Error while determining redirect url: %s", e)
        errors.append("Cannot locate the wikipedia page for '%s'" % target_wiki_page)
        return None

@view_config(route_name='choose_wiki_page', renderer='templates/choose_wiki_page.pt')
def choose_wiki_page(request):
    """ This view displays a form for requesting the table of contents for a wikipedia page.
    """
    errors = []
    # If there is a post, attempt to redirect to the appropriate "Table of Contents" view    
    redirect = get_wiki_page_redirect(request, errors)
    if redirect:
        raise redirect
    
    # Either there was no post or there were errors attempting to redirect
    
    template_parameters = default_template_parameters.copy()
    template_parameters["post_url"] = request.route_url('choose_wiki_page')
    template_parameters["errors"] = errors
    return template_parameters

@view_config(route_name='wiki_toc', renderer='templates/view_wiki_toc.pt')
def wiki_toc(request):
    errors = []
    template_parameters = default_template_parameters.copy()
    
    if request.matchdict["wiki_location"]:
        # Get the relative path to the wikipedia resouce; it is always defined by the trailing components of the 'wiki_toc' route
        wiki_location = "/".join(request.matchdict["wiki_location"])
        template_parameters["title"] = wiki_location
        
        # Fetch the page  - not that the default timeout for urllib2 is being used
        try:
            # Prepend the default wikipedia scheme to the url location (which should be 'https://')
            url = wikipedia_scheme + wiki_location
            reference_url_object = urlparse.urlparse(url)
            page = urllib2.urlopen(url)
            html = page.read()
            soup = BeautifulSoup(html, 'lxml')
            
            # Get the div containing the table of contents
            toc = soup.find_all('div', id="toc", limit=1)
            
            # Check that there is a table of contents
            if toc:
                toc = toc[0]
                # Fix any relative hrefs so that they link to the original site
                for a in toc.find_all('a'):
                    url_manager = UrlManager(a["href"])
                    if url_manager.url_is_relative():
                        a["href"] = url_manager.absolute_url(reference_url_object)
                    a["target"] = "_NEW"
            else:
                template_parameters["toc"] = None
                errors.append("No table of contents is available.")

            template_parameters["toc"] = toc
        except BaseException, e:
            logging.error("Failed to process the contents of '%s' due to error: %s", url, str(e))
            errors.append("Could not get the table of contents for '%s'" % wiki_location)
            template_parameters["toc"] = None
    else:
        template_parameters["title"] = "No wikipedia page provided" 
        template_parameters["toc"] = None
        errors.append("No wikipedia location has been provided.")

    template_parameters["errors"] = errors
    return template_parameters
