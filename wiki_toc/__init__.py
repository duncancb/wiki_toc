from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('choose_wiki_page', '/')                           # The default page where the user chooses the Wikipaedia TOC to view
    config.add_route('wiki_toc', '/wiki_toc/*wiki_location')
    config.scan()
    return config.make_wsgi_app()
