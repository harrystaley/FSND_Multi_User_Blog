import os
import jinja2
import webapp2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))


class Handler(webapp2.RequestHandler):
    """
    Handler class for all functions in this app for rendering any templates.
    """
    def write(self, *a, **kw):
        """
        Prints out the response to al functions.
        """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """
        Gets the template string and renders it with paramanters.
        """
        tmp = jinja_env.get_template(template)
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


app = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)
