# LIBRARY IMPORTS
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

# FILE LEVEL VARIABLES/CONSTANTS

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


# FILE LEVEL FUNCTIONS

def valid_user_id(user_id):
    """ validates the user id input by passing it through regex """
    return user_id and USER_RE.match(user_id)


def valid_password(password):
    """ validates the password input by passing it through regex """
    return password and PASS_RE.match(password)


def valid_email(email):
    """ validates the email input by passing it through regex """
    return not email or EMAIL_RE.match(email)


def render_post(response, DbPost):
    """ handler for rendering posts """
    response.out.write('<b>' + DbPost.db_subject + '</b><br>')
    response.out.write(DbPost.db_content)


def blog_key(name='default'):
    """
    This is the key that defines a single blog and facilitiate multiple
    blogs on the same site.
    """
    return db.Key.from_path('blogs', name)


# CLASS DEFINITIONS

class TemplateHandler(webapp2.RequestHandler):
    """
     TemplateHandler class for all functions in this app for rendering
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


class Post(TemplateHandler, db.Model):
    """
    Instantiates the class for a kind (table) in the GAE datastor
    consisting of properties (fields).

    """
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        """
        Renders the blog post replacing cariage returns in the text with
        html so that it displays correctly in the borowser.
        """
        self._render_text = self.content.replace('\n', '<br>')
        return self.render("post.html", db_post=self)


class MainPage(TemplateHandler):
    """ This is the handler class for the main page for the blog. """

    def get(self):
        """
        queries the database for the 10 most recent
        blog posts and orders them descending
        """
        posts = db.GqlQuery("SELECT * FROM Post "
                            "ORDER BY created DESC LIMIT 10")
        self.render("front.html", posts=posts)


class NewPostHandler(TemplateHandler):
    """ This is the handler class for the new blog post page """
    def get(self):
        """
        uses GET request to render the new post
        """
        self.render("newpost.html")

    def post(self):
        """
        handles the POST request
        from the new post page
        """
        input_subject = self.request.get('subject')
        input_content = self.request.get('content')
        # if subject and content exist store them in the database and redirect
        if input_subject and input_content:
            post = Post(parent=blog_key(),
                        subject=input_subject,
                        content=input_content)
            post.put()
            self.redirect('/%s' % str(post.key().id()))
        else:
            input_error = "Please submit both the title and the post content. "
            self.render("newpost.html", subject=input_subject,
                        content=input_content,
                        error=input_error)


class PermaPost(TemplateHandler):
    """ Class to handle successfull blog posts """
    def get(self, post_id):
        """
        function gets the primary key for the current
        blog and renders a permalink if it exists.
        """
        dbkey = db.Key.from_path('DbPost', int(post_id), parent=blog_key())
        perma_post = db.get(dbkey)

        if not perma_post:
            self.error(404)
            return
        else:
            self.render("permalink.html", db_post=perma_post)


class UserSignupHandler(TemplateHandler):
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


class WelcomeHandler(TemplateHandler):
    """ This is the handler class for the welcome page """
    def get(self):
        """ handles the GET request for the welcome paage """
        user_name = self.request.get('user_id')
        # If user_id is valid render the welcome page.
        if valid_user_id(user_name):
            self.render("welcome.html", user_id=user_name)


# GAE APPLICATION VARIABLE
# This variable sets the atributes of the individual HTML
# files that will be served using google app engine.
WSGI_APP = webapp2.WSGIApplication([
    ('/?', MainPage),
    ('/([0-9]+)', PermaPost),
    ('/newpost', NewPostHandler),
    ('/signup', UserSignupHandler),
    ('/welcome', WelcomeHandler)
], debug=True)
