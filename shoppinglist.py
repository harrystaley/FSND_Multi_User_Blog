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


class ShoppintListHandler(Handler):
    """
    Takes input from Handler and renders the markup
    defined.
    """

    def get(self):
        """
        Passes markup from defined file and passes it to the renderer.
        """
        items = self.request.get_all("food")
        # pases the value in item variable into the jinja2 template
        self.render("shopping_list.html", items=items)


WSGI_APP = webapp2.WSGIApplication([
    ('/shoppinglist', ShoppintListHandler)
], debug=True)
