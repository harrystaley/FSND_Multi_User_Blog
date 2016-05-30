import os
# import jinja2 lib
import jinja2
# import regex lib
import re
import webapp2

# import google app engine data store lib
from google.appengine.ext import db

__author__ = "Harry Staley <staleyh@gmail.com>"
__version__ = "1.0"


# sets the locaiton of the templates folder contained in the home of this file.
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
# envokes the jinja2 envronment pointing it to the location of the templates.
# with user input markup automatically escaped
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
                               autoescape=True)
# user signup form validation constants using regex
USER_RE = re.compile("^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+.[\S]+$")


def valid_user_id(user_id):
    """ validates the user id input by passing it through regex """
    return user_id and USER_RE.match(user_id)


def valid_password(password):
    """ validates the password input by passing it through regex """
    return password and PASS_RE.match(password)


def valid_email(email):
    """ validates the email input by passing it through regex """
    return not email or EMAIL_RE.match(email)


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
        """
        Calls render_str and displays the template.
        """
        self.write(self.render_str(template, **kw))




class FizzBuzzHandler(Handler):
    """ Class to handle FizzBuzz template """

    def get(self):
        """ uses GET request to render the main page and get the value of n """
        count = self.request.get('n', 0)
        count = count and int(count)
        self.render("fizzbuzz.html", n=count)


class DbPostHandler(db.Model):
    """ This is the handler class for the new blog post datastore """
    db_post_title = db.StringProperty(required=True)
    db_post_content = db.TextProperty(required=True)
    db_post_created = db.DateTimeProperty(auto_now_add=True)


class NewPostHandler(Handler):
    """ This is the new handler class for the new blog post page """
    def render_new_post(self, post_title="", post_content="", post_error=""):
        self.render("newpost.html", post_title=post_title,
                    post_content=post_content,
                    post_error=post_error)

    def get(self):
        """
        uses GET request to render the new
        post page from render_new_post
        """
        self.render_new_post()

    def post(self):
        """
        handles the POST request
        from the new post page
        """
        post_title = self.request.get('post_title')
        post_content = self.request.get('post_content')

        if post_title and post_content:
            cursor = DbPostHandler(db_post_title=post_title,
                                   db_post_content=post_content)
            cursor.put()
            self.redirect("/")
        else:
            post_error = "Please submit both the title and the post content. "


class UserSignupHandler(Handler):
    """ This is the hander class for the user sign up page """

    def get(self):
        """ uses GET request to render the main page """
        self.render("signup.html")

    def post(self):
        """ handles the POST request from the signup page """
        have_error = False
        # GET requests for user input from signup page
        user_id = self.request.get('user_id')
        password_1 = self.request.get('password_1')
        password_2 = self.request.get('password_2')
        email = self.request.get('email')

        # dictionary to store error messages and user_id and email if not valid
        params = dict(user_id=user_id, email=email)

        # tests for valid user_id
        if not valid_user_id(user_id):
            params['error_user_id'] = 'Invalid User ID'
            have_error = True

        # tests for valid password and password match
        if not valid_password(password_1):
            params['error_password_1'] = 'Invalid Password'
            have_error = True
        elif password_1 != password_2:
            params['error_password_2'] = 'Passwords do not Match'
            have_error = True

        # tests for valid email
        if not valid_email(email):
            params['error_email'] = 'Invalid Email'
            have_error = True

        # if there is an error re-render signup page
        # else render the welcome page
        if have_error:
            self.render("signup.html", **params)
        else:
            self.redirect('/welcome?user_id=' + user_id)


class WelcomeHandler(Handler):
    """ This is the handler class for the welcome page """
    def get(self):
        """ handles the GET request for the welcome paage """
        user_name = self.request.get('user_id')
        # If user_id is valid render the welcome page.
        if valid_user_id(user_name):
            self.render("welcome.html", user_id=user_name)


WSGI_APP = webapp2.WSGIApplication([
    ('/', ShoppintListHandler),
    ('/fizzbuzz', FizzBuzzHandler),
    ('/newpost', NewPostHandler),
    ('/signup', UserSignupHandler),
    ('/welcome', WelcomeHandler)
], debug=True)
