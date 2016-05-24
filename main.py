import os
import jinja2
import webapp2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.environment(loader = jinja2.FileSystemLoader(template_dir))


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(Handler):
    def get(self):
        self.render("shopping_list.html")

        # output = form_html
        # output_hidden = ""

        # items = self.request.get_all("food")

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/testform', TestHandler),
], debug=True)
