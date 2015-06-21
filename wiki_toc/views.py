from pyramid.view import view_config
from pyramid import httpexceptions as exc
import urlparse
import urllib2
import logging

# For this example app, there is no database so many of the paremters below are hardcoded throughout the app
# even though it would be more useful to derive them from database configuration
default_template_parameters = dict(
    title = "Table of Contents Scraper",
    errors = None
)

wikipedia_scheme = "https://"
wikipedia_domain = "wikipedia.org"


def get_wiki_page_redirect(request, errors):
    """ This page accepts a form post containing the value 'target_wiki_page' and redirects to a site page matching the relative url of the wikipaedia page
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
        return exc.HTTPInternalServerError("Cannot locate the wikipaedia page for unspecified location.")

    # There is a post specifying a target page
    try:
        if target_wiki_page.startswith("http"):
            urlobj = urlparse.urlparse(target_wiki_page)
        else:
            urlobj = urlparse.urlparse(wikipedia_scheme+target_wiki_page.strip("/"))
        
        if urlobj.netloc.endswith(wikipedia_domain):
            # Convert urlobj to a list and set its scheme and netloc components to ''
            urlobj = list(urlobj)
            urlobj[0] = ""
            # With the scheme removed, calculate a relative url path to the resource
            wiki_location = urlparse.urlunparse(urlobj).strip("/")
            return exc.HTTPFound(request.route_url("wiki_toc", wiki_location=wiki_location))
        else:
            logging.error("User supplied url, '%s', is not a valid Wikipaedia url.", target_wiki_page)
            errors.append("'%s' is not a valid Wikipaedia url. Please try again." % target_wiki_page)
    except BaseException, e:
        # An unexpected error has occurred. Remain on the current page and display the error.
        logging.error("Error while determining redirect url: %s", e)
        errors.append("Cannot locate the wikipaedia page for '%s'" % target_wiki_page)
        return None

@view_config(route_name='choose_wiki_page', renderer='templates/choose_wiki_page.pt')
def choose_wiki_page(request):
    """ This view displays a form for requesting the table of contents for a wikipaedia page.
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
        wiki_location = "/".join(request.matchdict["wiki_location"])
        template_parameters["title"] = "Table of Contents: %s" % wiki_location
        
        # Fetch the page  - not that the default timeout for urllib2 is being used
        try:
            page = urllib2.urlopen(wikipedia_scheme + wiki_location)
            html = page.read()
            template_parameters["toc"] = html.decode("utf-8")
        except BaseException, e:
            logging.warning("Failed to read the contents of '%s'", wikipedia_scheme + wiki_location)
            errors.append("Could not get the table of contents for '%s'" % wiki_location)
    else:
        template_parameters["title"] = "No Wikipaedia page provided" 
        template_parameters["toc"] = None
        errors.append("No Wikipaedia location has been provided.")

    template_parameters["errors"] = errors
    return template_parameters
