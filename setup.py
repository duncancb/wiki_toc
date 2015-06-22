import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'pyramid',
    'pyramid_chameleon',
    'pyramid_debugtoolbar',
    'waitress',
    'lxml',
    'beautifulsoup4',
    'WebTest'
    ]

setup(name='wiki_toc',
      version='0.0',
      description='wiki_toc',
      long_description="An example web site that scrapes the TOC from Wikipaedia",
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="wiki_toc",
      entry_points="""\
      [paste.app_factory]
      main = wiki_toc:main
      """,
      )
