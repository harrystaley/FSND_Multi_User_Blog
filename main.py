import os
import jinja2
import webapp2

# sets the locaiton of the templates folder contained in the home of this file.
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
# envokes the jinja2 envronment pointing it to the location of the templates.
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))


class Handler(webapp2.RequestHandler):
    """
    Handler class for all functions in this app for rendering any templates.
    """
    def write(self, *a, **kw):
        """
        displays the respective function, parameters, ect.
        """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """
        Gets the template string and passes it with paramanters.
        """
        tmp = JINJA_ENV.get_template(template)
        return tmp.render(params)

    def render(self, template, **kw):
        """
        Calls render_str and displays the template
        """
        self.write(self.render_str(template, **kw))


class MainPage(Handler):
    """
    Takes input from Handler and renders the markup defined.
    """
    def get(self):
        """
        Passes markup from defined file and passes it to the renderer.
        """
        self.render("shopping_list.html")

# Called in app.yaml as an atribute of this
# file so that template can be rendered
app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
