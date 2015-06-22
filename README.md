wiki_toc sample application
===========================

This is a sample web application which retrieves the Table of Contents from Wikipedia pages. 

Install
-------

Make sure that python pip is installed

From the base folder of the app run:

python setup.py install

Running the app
---------------

From the base folder of the app run:

pserve production.ini

The app should start running on http://0.0.0.0:6543/

It will initially:

* Present an input field and submit button for entering a Wikipedia url
* Flag invalid domains and entries and request new input. Invalid Wikipedia resources are initially accepted.
* Redirect to a Table of Contents page when valid urls are provided

Urls can be in either of the following formats:

* Full urls eg: https://en.wikipedia.org/wiki/Satchel
* Relative urls starting with a '/' eg: /wiki/Satchel (it will be assumed that this is a resource at wikipedia.org)

On the Table of Contents page:

* Available Tables of Contents are displayed with links corrected to point to the original site
* If the resource is not a valid wikipedia resource an error message is displayed
* If there is no table of contents for a page an error message will be displayed
* There is a restart button which returns to the home page

Testing
-------

Tests have been included and can be run by executing:

python setup.py test
