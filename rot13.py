import os
# import jinja2 lib
import jinja2
# import regex lib
import webapp2

__author__ = "Harry Staley <staleyh@gmail.com>"
__version__ = "1.0"


# sets the locaiton of the templates folder contained in the home of this file.
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
# envokes the jinja2 envronment pointing it to the location of the templates.
# with user input markup automatically escaped
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))


class Handler(webapp2.RequestHandler):
    """
    Handler class for all functions in this app for rendering
    any templates.
    """

    def write(self, *a, **kw):
        """ displays the respective function, parameters, ect. """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """ Gets the template and passes it with paramanters. """
        tmp = JINJA_ENV.get_template(template)
        return tmp.render(params)

    def render(self, template, **kw):
        """ Calls render_str and displays the template. """
        self.write(self.render_str(template, **kw))


class Rot13Handler(Handler):
    """ Class to handle the Rot13 template """

    def get(self):
        """ uses GET request to render the rot13 page """

        self.render("rot13.html")

    def post(self):
        """ This function handles the post request from the web page """

        # GET request for user input from ROT13 page
        text = self.request.get("text")
        # encodes cyphertext using rot13 ceasar cypher
        cyphertext = text.encode('rot13')
        # re-renders the page passing in cyphertext
        self.render("rot13.html", text=cyphertext)


WSGI_APP = webapp2.WSGIApplication([
    ('/rot13', Rot13Handler)
], debug=True)
