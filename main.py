# -*- coding: utf-8 -*-
import os

# import regex lib
import re
import random
import webapp2
import hashlib
import hmac
from string import letters

# import jinja2 lib
import jinja2

# import google app engine data store lib
from google.appengine.ext import db

__author__ = "Harry Staley <staleyh@gmail.com>"
__version__ = "1.0"


# TODO: once I get the file working with the example variable style I should
# change the post variable and classnames so that they do not share
# the same name with the post from the RequestHandler class imported
# from webapp2. Info on webapp2 framework can be found at:
# https://cloud.google.com/appengine/docs/python/gettingstartedpython27/usingwebapp#hello-webapp2


# FILE LEVEL VARIABLES/CONSTANTS

# sets the locaiton of the templates folder contained in the home of this file.
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
# envokes the jinja2 envronment pointing it to the location of the templates.
# with user input markup automatically escaped
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
                               autoescape=True)
COOKIE_SECRET = ''.join(random.choice(letters) for x in xrange(10))


# FILE LEVEL FUNCTIONS
def blog_key(name='default'):
    """
    This is the key that defines a single blog and facilitiate multiple
    blogs on the same site.
    """
    return db.Key.from_path('blogs', name)


def user_key(group='default'):
    """
    This is the key that defines a user group and facilitates
    multiple groups on the same site.
    """
    return db.Key.from_path('users', group)


def render_str(template, **params):
    """ Gets the template and passes it with paramanters. """
    tmp = JINJA_ENV.get_template(template)
    return tmp.render(params)


# CLASS DEFINITIONS
class EncryptHandler():
    """ handles basic encryption functions """

    def make_salt(self, salt_length=5):
        """
        Creates a salt for salting passwords and other hashed values """
        return ''.join(random.choice(letters)
                       for x in xrange(salt_length))

    def hash_pass(self, username, password, salt=None):
        """
        if a password salt does not exist create one, otherwise hash the
        user data .
        """
        if not salt:
            salt = self.make_salt()
        hashed_pass = hashlib.sha256(username + password + salt).hexdigest()
        return '%s|%s' % (salt, hashed_pass)

    def valid_pass_hash(self, name, password, hashed_pass):
        """
        Checks to see if the password is valid by comparing it to a hash
        passed into the function.
        """
        salt = hashed_pass.split('|')[0]
        return hashed_pass == self.hash_pass(name, password, salt)

    def make_secure_val(self, val):
        return '%s|%s' % (val, hmac.new(self.COOKIE_SECRET, val).hexdigest())

    def check_secure_val(self, secure_val):
        val = secure_val.split('|')[0]
        if secure_val == self.make_secure_val(val):
            return val


class TemplateHandler(webapp2.RequestHandler, EncryptHandler):
    """
     TemplateHandler class for all functions in this app for rendering
    any templates.
    """
    def write(self, *a, **kw):
        """ displays the respective function, parameters, ect. """
        self.response.out.write(*a, **kw)

    def render_tmp(self, template, **params):
        """
        Gets the template and passes it with paramanters to a
        file level function called render_str.
        """
        return render_str(template, **params)

    def render(self, template, **kw):
        """
        Calls render_tmp and write to display the template.
        """
        self.write(self.render_tmp(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = self.make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def get_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and self.check_secure_val(cookie_val)


class Post(db.Model):
    """
    Instantiates the class for a kind (table) in the GAE datastor
    consisting of properties (fields).

    """
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def render_post(self):
        """
        Renders the blog post replacing cariage returns in the text with
        html so that it displays correctly in the borowser.
        """
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", post=self)


class User(db.Model):
    username = db.StringProperty(required=True)
    pass_hash = db.StringProperty(required=True)
    email = db.StringProperty()


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
        uses GET request to render newpost.html by calling render from the
        TemplateHandler class
        """
        self.render("newpost.html")

    def post(self):
        """
        handles the POST request from newpost.html
        """
        subject_input = self.request.get('subject')
        content_input = self.request.get('content')
        # if subject and content exist create an entity (row) in the GAE
        # datastor (database) and redirect to a permanent link to the post
        if subject_input and content_input:
            post = Post(parent=blog_key(),
                        subject=subject_input,
                        content=content_input)
            post.put()
            # redirects to a single blog post passing the post id
            # from the function as a string to a pagewhere the post_id
            # is the url
            post_id = str(post.key().id())
            self.redirect('/%s' % post_id)
        else:
            input_error = "Please submit both the title and the post content. "
            self.render("newpost.html", subject=subject_input,
                        content=content_input,
                        error=input_error)


class PermaLinkHandler(TemplateHandler):
    """ Class to handle successfull blog posts that returns a permalink """
    def get(self, post_id):
        """
        uses GET request to get the post_id from the new post
        and renders permalink.html if the blog post exists by
        passing the template into render from the TemplateHandler class.
        """
        db_key = db.Key.from_path('Post', int(post_id), parent=blog_key())
        perma_post = db.get(db_key)

        if not perma_post:
            self.error(404)
            return
        else:
            self.render("permalink.html", post=perma_post)


class UserSignupHandler(TemplateHandler, EncryptHandler):
    """ This is the hander class for the user sign up page """
    # user signup form validation constants using regex to validate user input
    PASS_RE = re.compile("^.{3,20}$")
    EMAIL_RE = re.compile("^[\S]+@[\S]+.[\S]+$")
    USER_RE = re.compile("^[a-zA-Z0-9_-]{3,20}$")

    def valid_username(self, username):
        """ validates the user id input by passing it through regex """
        return username and self.USER_RE.match(username)

    def valid_password(self, password):
        """ validates the password input by passing it through regex """
        return password and self.PASS_RE.match(password)

    def valid_email(self, email):
        """ validates the email input by passing it through regex """
        return not email or self.EMAIL_RE.match(email)

    def get(self):
        """
        uses GET request to render signup.html by passing signup.html into
        render from the TemplateHandler class.
        """
        self.render("signup.html")

    def post(self):
        """ handles the POST request from signup.html """
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        # dictionary to store error messages, username and email if not valid
        params = dict(username=username, email=email)

        # tests for valid username
        if not self.valid_username(username):
            params['error_username'] = 'Invalid User ID'
            have_error = True

        # tests for valid password and password match
        if not self.valid_password(password):
            params['error_password'] = 'Invalid Password'
            have_error = True
        elif password != verify:
            params['error_verify'] = 'Passwords do not Match'
            have_error = True

        # tests for valid email
        if not self.valid_email(email):
            params['error_email'] = 'Invalid Email'
            have_error = True

        # if there is an error re-render signup page
        # else render the welcome page
        if have_error:
            self.render("signup.html", **params)
        else:
            self.set_user_cookie(username)
            self.redirect('welcome.html')


class WelcomeHandler(TemplateHandler):
    """ This is the handler class for the welcome page """
    def get(self):
        """ handles the GET request for welcome.html """
        user_name = self.request.cookies.get('username')
        # If username is valid render the welcome page by calling
        # render from TemplateHandler class.
        if self.valid_username(user_name):
            self.render("welcome.html/username=", username=user_name)


# GAE APPLICATION VARIABLE
# This variable sets the atributes of the individual HTML
# files that will be served using google app engine.
WSGI_APP = webapp2.WSGIApplication([
    ('/?', MainPage),
    # '/([0-9]+)' recieves post_id from NewPostHandler class passing it
    # into PermaPost class via the url using regular expression
    ('/([0-9]+)', PermaLinkHandler),
    ('/newpost', NewPostHandler),
    ('/signup', UserSignupHandler),
    ('/welcome', WelcomeHandler)
], debug=True)
