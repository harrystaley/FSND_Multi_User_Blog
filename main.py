import os
import re
import random
import webapp2
import hashlib
import hmac
import datetime
from string import letters

# import jinja2 lib for templating
import jinja2

# import google app engine data store lib
from google.appengine.ext import db
from google.appengine.ext.db import metadata


__author__ = "Harry Staley <staleyh@gmail.com>"
__version__ = "1.0"

# FILE LEVEL VARIABLES/CONSTANTS

# sets the locaiton of the templates folder contained in the home of this file.
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
# envokes the jinja2 envronment pointing it to the location of the templates.
# with user input markup automatically escaped
JINJA_ENV = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
                               autoescape=True)
COOKIE_SECRET = 'secret'
# REGEX FOR SIGNUP FORM
# email validation regex from http://emailregex.com/ taken from hackernews
EMAIL_RE = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")


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


def post_key(post_id):
    """
    This is the key that defines a post and facilitates
    multiple groups on the same site.
    """
    return db.Key.from_path('Post', int(post_id), parent=blog_key())


def render_str(template, **params):
    """ Gets the template and passes it with paramanters. """
    tmp = JINJA_ENV.get_template(template)
    return tmp.render(params)


def like_dup(ent, login_id, post_id):
    key = post_key(post_id)
    like_exists = db.GqlQuery("SELECT * "
                              "FROM " + ent +
                              " WHERE like_user_id = '" + login_id +
                              "' AND ANCESTOR IS :1", key).get()
    return like_exists


# CLASS DEFINITIONS
class EncryptHandler(object):
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

    def valid_pass_hash(self, username, password, hashed_pass):
        """
        Checks to see if the password is valid by comparing it to a hash
        passed into the function.
        """
        salt = hashed_pass.split('|')[0]
        return hashed_pass == self.hash_pass(username, password, salt)

    def make_secure_val(self, val):
        return '%s|%s' % (val, hmac.new(COOKIE_SECRET, val).hexdigest())

    def get_secure_val(self, secure_val):
        if secure_val:
            val = secure_val.split('|')[0]
        else:
            val = None
        if secure_val == self.make_secure_val(val):
            return val


class AuthHandler(EncryptHandler):
    """ Handles user authentication """
    def user_exists(self, username):
        """ validates that the user exists in the database """
        username_exists = db.GqlQuery("SELECT * "
                                      "FROM User "
                                      "WHERE username = :usernm",
                                      usernm=username).get()
        return username_exists

    def user_auth(self, username, password):
        """
        If the username exists it suthenticates the password of the user
        """
        user = db.GqlQuery("SELECT * "
                           "FROM User "
                           "WHERE username = :usernm",
                           usernm=username).get()
        if user:
            return self.valid_pass_hash(user.username,
                                        password,
                                        user.pass_hash)


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
        Calls render_tmp and write to display the jinja template.
        """
        # Loads the nav for each page from a tuple in the order of link, title.
        if self.read_secure_cookie('usercookie'):
            # Gets the user id from the cookie
            user_id = self.read_secure_cookie('usercookie')
            # gets the key for the kind (table)
            key = db.Key.from_path('User',
                                   int(user_id),
                                   parent=user_key())
            # gets the user data based upon what is passed
            # from user_id into key
            user = db.get(key)
            login_status = "<span>Logged in as: %s  </span>" % (user.username)
            nav = [('/', 'Home'),
                   ('/newpost', 'Create New Post'),
                   ('/logout', 'Log Out')]
        else:
            login_status = ''
            user_id = ''
            nav = [('/', 'Home'),
                   ('/signup', 'Sign Up'),
                   ('/login', 'Log In')]
        self.write(self.render_tmp(template, login_id=user_id,
                                   nav=nav, login_status=login_status, **kw))

    def set_secure_cookie(self, name, val, exp):
        """
        Method takes in a name, value, and expiration it creates a cookie.

        The name parameter takes in any value and converts it to a string.

        The val parameter takes in any value and converts it to a string.

        The exp parameter takes in integer representing the number of
        seconds before expiration.

        A null or non integer value in the expiration parameter sets a
        session cookie.
        """
        # sets cookie that expires  after a specified time unless refreshed
        # a blank value sets a session cookie
        cookie_val = self.make_secure_val(str(val))
        if exp and isinstance(exp, (int, long, float)):
            now = datetime.datetime.utcnow()
            expires = datetime.timedelta(seconds=exp)
            exp_date = (now + expires).strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            exp_date = ''
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; expires=%s; Path=/' % (name, cookie_val, exp_date))

    def read_secure_cookie(self, cookie_name):
        """
        Method takes in the name of a cookie and returns its' value.
        Remember that the value of a cookie will be in plain text format.
        """
        if self.request.cookies.get(cookie_name):
            cookie_val = self.request.cookies.get(cookie_name)
            val = self.get_secure_val(cookie_val)
            return val
        else:
            return


class Post(db.Model):
    """
    Instantiates a class to store post (entity or row) data for posts
    (kiind or table) in the datastor consisting of individual atributes
    of the post (properties or fields).
    """
    author_id = db.StringProperty(required=True)
    author_name = db.StringProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def post_likes(self, post_id):
        # gets the metadata about the datastor
        kinds = metadata.get_kinds()
        # checks to see if any likes exist and if so displays them
        if u'PostLike' in kinds:
            likes = db.GqlQuery("SELECT * "
                                "FROM PostLike "
                                "WHERE ANCESTOR IS :1",
                                post_key(post_id)).count()
        else:
            likes = 0
        return likes

    def render_post(self, login_id, post_id):
        """
        Renders the blog post replacing cariage returns in the text with
        html so that it displays correctly in the borowser.
        """
        likes = self.post_likes(post_id)
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", login_id=login_id,
                          likes=likes, post=self)

    def post_like_dup(self, login_id, post_id):
        exists = like_dup('PostLike', login_id, post_id)
        return exists


class PostLike(db.Model):
    """
    Handles the likes for each of the posts
    """
    like_user_id = db.StringProperty(required=True)


class Comment(db.Model):
    """
     Instantiates a class to store comments (entity or row) data for comments
    (kiind or table) in the datastor consisting of individual atributes
    of the post (properties or fields).
    """
    author_id = db.StringProperty(required=True)
    author_name = db.StringProperty(required=True)
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)

    def render_comment(self, login_id):
        """
        Renders the blog post replacing cariage returns in the text with
        html so that it displays correctly in the borowser.
        """
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("comment.html", login_id=login_id,
                          comment=self)


class User(db.Model):
    """
    Instantiates a class to store user (entity or row) data for users
    (kiind or table) in the datastor consisting of individual atributes
    of the user (properties or fields).
    """
    username = db.StringProperty(required=True)
    pass_hash = db.StringProperty(required=True)
    email = db.StringProperty()


class MainPage(TemplateHandler, AuthHandler):
    """ This is the handler class for the main page for the blog. """
    def get(self):
        """
        queries the database for the 10 most recent
        blog posts and orders them descending
        """
        posts = db.GqlQuery("SELECT * "
                            "FROM Post "
                            "ORDER BY created DESC LIMIT 10")
        self.render("front.html", posts=posts)

    def post(self):
        """ handles the post for from the main page """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            edit_post_id = self.request.get('edit_post_id')
            comment_post_id = self.request.get('comment_post_id')
            like_post_id = self.request.get('like_post_id')
            if comment_post_id:
                post_id = comment_post_id
                self.redirect('/newcomment?post_id=' + post_id)
            if edit_post_id:
                post_id = edit_post_id
                self.redirect('/editpost?post_id=' + post_id)
            if like_post_id:
                post_id = like_post_id
                user_id = self.read_secure_cookie('usercookie')
                if not like_dup('PostLike', user_id, post_id):
                    like = PostLike(like_user_id=user_id,
                                    parent=post_key(post_id))
                    like.put()
                    self.redirect('/')
        else:
            self.redirect('/signup')


class NewPostHandler(TemplateHandler, AuthHandler):
    """ This is the handler class for the new blog post page """
    def get(self):
        """
        uses GET request to render newpost.html by calling render from the
        TemplateHandler class
        """
        if self.read_secure_cookie('usercookie'):
            self.render("newpost.html")
        else:
            self.redirect('/signup')

    def post(self):
        """
        handles the POST request from newpost.html
        """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            subject_input = self.request.get('subject')
            content_input = self.request.get('content')
            if self.read_secure_cookie('usercookie'):
                # Gets the user id from the cookie if the cookie is set
                user_id = self.read_secure_cookie('usercookie')
                key = db.Key.from_path('User', int(user_id), parent=user_key())
                user = db.get(key)
            # if subject, content, and user_id exist create an entity (row) in
            # the GAE datastor (database) and redirect to a permanent link to
            # the post
            if subject_input and content_input and user_id:
                post = Post(parent=blog_key(),
                            author_id=user_id,
                            author_name=user.username,
                            subject=subject_input,
                            content=content_input)
                post.put()
                # redirects to a single blog post passing the post id
                # from the function as a string to a pagewhere the post_id
                # is the url
                post_id = str(post.key().id())
                self.redirect('/post-%s' % post_id)
            else:
                input_error = "Please submit both the title and content."
                self.render("newpost.html", subject=subject_input,
                            content=content_input,
                            error=input_error)
        else:
            self.redirect('/signup')


class NewCommentHandler(TemplateHandler, AuthHandler):
    """ This is the handler class for the new blog post page """
    def get(self):
        """
        uses GET request to render newpost.html by calling render from the
        TemplateHandler class
        """
        if self.read_secure_cookie('usercookie'):
            post_id = self.request.get('post_id')
            self.render("newcomment.html", post_id=post_id)
        else:
            self.redirect('/signup')

    def post(self):
        """
        handles the POST request from newpost.html
        """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            post_id = self.request.get('post_id')
            subject_input = self.request.get('subject')
            content_input = self.request.get('content')
            if self.read_secure_cookie('usercookie'):
                # Gets the user id from the cookie if the cookie is set
                user_id = self.read_secure_cookie('usercookie')
                key = db.Key.from_path('User', int(user_id), parent=user_key())
                user = db.get(key)
            # if subject, content, and user_id exist create an entity (row) in
            # the GAE datastor (database) and redirect to a permanent link to
            # the post
            if subject_input and content_input and user_id:
                comment = Comment(parent=post_key(post_id),
                                  author_id=user_id,
                                  author_name=user.username,
                                  subject=subject_input,
                                  content=content_input)
                comment.put()
                # redirects to a single blog post passing the post id
                # from the function as a string to a pagewhere the post_id
                # is the url
                comment_id = str(comment.key().id())
                self.redirect('/comment-%s?post_id=%s' % (comment_id, post_id))
            else:
                input_error = "Please submit both the title and content."
                self.render("newcomment.html", subject=subject_input,
                            content=content_input,
                            error=input_error,
                            post_id=post_id)
        else:
            self.redirect('/signup')


class PostLinkHandler(TemplateHandler, AuthHandler):
    """ Class to handle successfull blog posts that returns a permalink """
    def get(self, login_id):
        """
        uses GET request to get the post_id from the new post
        and renders permalink.html if the blog post exists by
        passing the template into render from the TemplateHandler class.
        """
        url_str = self.request.path
        post_id = url_str.rsplit('post-', 1)[1]
        key = post_key(post_id)
        post = db.get(key)

        kinds = metadata.get_kinds()
        # checks to see if any comments exist and if so displays them
        if u'Comment' in kinds:
            comments = db.GqlQuery("SELECT * "
                                   "FROM Comment "
                                   "WHERE ANCESTOR IS :1", key)
        else:
            comments = ''
        self.render("postlink.html", post=post,
                    comments=comments)

    def post(self, login_id):
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            edit_post_id = self.request.get('edit_post_id')
            edit_comment_id = self.request.get('edit_comment_id')
            comment_post_id = self.request.get('comment_post_id')
            like_post_id = self.request.get('like_post_id')
            if comment_post_id:
                post_id = comment_post_id
                self.redirect('/newcomment?post_id=' + post_id)
            if edit_post_id:
                post_id = edit_post_id
                self.redirect('/editpost?post_id=' + post_id)
            if edit_comment_id:
                url_str = self.request.path
                post_id = url_str.rsplit('post-', 1)[1]
                comment_id = edit_comment_id
                self.redirect('/editcomment?post_id=%s&comment_id=%s' %
                              (post_id, comment_id))
            if like_post_id:
                post_id = like_post_id
                user_id = self.read_secure_cookie('usercookie')
                if not like_dup('PostLike', user_id, post_id):
                    like = PostLike(like_user_id=user_id,
                                    parent=post_key(post_id))
                    like.put()
                    self.redirect('/post-%s' % post_id)
        else:
            self.redirect('/signup')


class CommentLinkHandler(TemplateHandler, AuthHandler):
    """ Class to handle successfull blog posts that returns a permalink """
    def get(self, login_id):
        """
        uses GET request to get the post_id from the new post
        and renders permalink.html if the blog post exists by
        passing the template into render from the TemplateHandler class.
        """
        post_id = self.request.get('post_id')
        url_str = self.request.path
        comment_id = url_str.rsplit('comment-', 1)[1]
        comment_key = db.Key.from_path('Comment', int(comment_id),
                                       parent=post_key(post_id))
        comment = db.get(comment_key)
        # gets the metadata about the datastor
        # checks to see if any comments exist
        self.render("commentlink.html", comment=comment)

    def post(self, login_id):
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            comment_id = self.request.get('edit_comment_id')
            post_id = self.request.get('post_id')
            if self.read_secure_cookie('usercookie'):
                if comment_id and post_id:
                    self.redirect('/editcomment?comment_id=%s&post_id=%s' %
                                  (comment_id, post_id))
        else:
            self.redirect('/signup')


class UserSignUpHandler(TemplateHandler, EncryptHandler):
    """ This is the hander class for the user sign up page """
    # user signup form validation constaccccnts using a string literal regex to
    # validate user input
    def valid_username(self, username):
        """ validates the user id input by passing it through regex """
        return username and USER_RE.match(username)

    def user_exists(self, username):
        """ validates that the user exists in the database """
        username_exists = db.GqlQuery("SELECT * "
                                      "FROM User "
                                      "WHERE username = :usernm",
                                      usernm=username).get()
        return username_exists

    def valid_password(self, password):
        """ validates the password input by passing it through regex """
        return password and PASS_RE.match(password)

    def valid_email(self, email):
        """ validates the email input by passing it through regex """
        return not email or EMAIL_RE.match(email)

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

        # if the username already exists or it is an error
        if self.user_exists(username):
            params['error_username_exists'] = 'User Exists'
            have_error = True
        elif not self.valid_username(username):
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
            hashed_pass = self.hash_pass(username, password)
            user = User(parent=user_key(),
                        username=username,
                        pass_hash=hashed_pass,
                        email=email)
            user.put()
            user_id = str(user.key().id())
            self.set_secure_cookie('usercookie', user_id, None)
            self.redirect('/welcome')


class UserLoginHandler(TemplateHandler, AuthHandler):
    """ This is the hander class for the user sign up page """
    def get(self):
        """
        uses GET request to render signup.html by passing signup.html into
        render from the TemplateHandler class.
        """
        self.render("login.html")

    def post(self):
        """ handles the POST request from signup.html """
        auth_error = True
        username = self.request.get('username')
        password = self.request.get('password')

        # dictionary to store error messages, username and email if not valid
        params = dict(username=username)

        # if the username already exists or it is an error
        if self.user_exists(username):
            auth_error = False
            # tests for valid password and password match
            if self.user_auth(username, password):
                auth_error = False
            else:
                auth_error = True
                params['error_password'] = 'Invalid Password'
        else:
            auth_error = True
            params['error_username'] = 'User Does Not Exist'

        # if there is an error re-render signup page
        # else render the welcome page
        if auth_error:
            self.render("login.html", **params)
        else:
            user = db.GqlQuery("SELECT * "
                               "FROM User "
                               "WHERE username = :usernm",
                               usernm=username).get()
            user_id = str(user.key().id())
            self.set_secure_cookie('usercookie', user_id, None)
            self.redirect('/welcome')


class UserLogoutHandler(TemplateHandler, EncryptHandler):
    """ logs user out of the application """
    def get(self):
        """
        Uses GET request to redirect to signup as well as destroying
        the cookie.
        """
        # sets the expiration time of the cookie to -1 to destroy it
        self.set_secure_cookie('usercookie', '', -1)
        self.redirect('/signup')


class WelcomeHandler(TemplateHandler):
    """ This is the handler class for the welcome page """
    def get(self):
        """ handles the GET request for welcome.html """
        # if the usercookie exists render the welcome page
        # otherwise redirect to the signup page.
        if self.read_secure_cookie('usercookie'):
            # Gets the user id from the cookie
            user_id = self.read_secure_cookie('usercookie')
            # gets the key for the kind (table)
            key = db.Key.from_path('User',
                                   int(user_id),
                                   parent=user_key())
            # gets the user data based upon what is passed
            # from user_id into key
            user = db.get(key)
            # renders the welcome page passing in the user name
            self.render("welcome.html",
                        username=user.username)
        else:
            self.redirect('/signup')


class EditPost(TemplateHandler, AuthHandler):
    """ Handles the editing of blog posts """
    def get(self):
        """ uses get request to get newpost.html """
        post_id = self.request.get('post_id')
        key = db.Key.from_path('Post',
                               int(post_id),
                               parent=blog_key())
        # gets the post data based upon what
        # is passed from post_id into key
        post = db.get(key)
        if self.read_secure_cookie('usercookie'):
            user_id = self.read_secure_cookie('usercookie')
            # If the current logged in user is not the post author
            # it redirects them back to the previous page
            if user_id == post.author_id:
                self.render("editpost.html",
                            subject=post.subject,
                            content=post.content,
                            post_id=post_id)
            else:
                referrer = self.request.headers.get('referer')
                if referrer:
                    return self.redirect(referrer)
                return self.redirect_to('/')
        else:
            self.redirect('/signup')

    def post(self):
        """
        handles the POST request from newpost.html
        """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            post_id = self.request.get('post_id')
            subject_input = self.request.get('subject')
            content_input = self.request.get('content')
            post_key = db.Key.from_path('Post',
                                        int(post_id),
                                        parent=blog_key())
            # gets the post data based upon what
            # is passed from post_id into key
            # if subject and content exist create an entity (row) in
            # the GAE datastor (database) and redirect to a permanent
            # link to the post
            if subject_input and content_input:
                post = db.get(post_key)
                post.subject = subject_input
                post.content = content_input
                post.put()
                # redirects to a single blog post passing the post id
                # from the function as a string to a pagewhere the post_id
                # is the url
                post_id = str(post.key().id())
                self.redirect('/post-%s' % post_id)
            else:
                input_error = "Please submit both the title and content."
                self.render("editpost.html", subject=subject_input,
                            content=content_input,
                            error=input_error, post_id=post_id)
        else:
            self.redirect('/signup')


class EditComment(TemplateHandler, AuthHandler):
    """ Handles the editing of blog posts """
    def get(self):
        """ uses get request to get newpost.html """
        comment_id = self.request.get('comment_id')
        post_id = self.request.get('post_id')
        key = db.Key.from_path('Comment',
                               int(comment_id),
                               parent=post_key(post_id))
        # gets the post data based upon what
        # is passed from post_id into key
        comment = db.get(key)
        if self.read_secure_cookie('usercookie'):
            user_id = self.read_secure_cookie('usercookie')
            # If the current logged in user is not the post author
            # it redirects them back to the previous page
            if user_id == comment.author_id:
                self.render("editcomment.html",
                            subject=comment.subject,
                            content=comment.content,
                            post_id=post_id,
                            comment_id=comment_id)
            else:
                referrer = self.request.headers.get('referer')
                if referrer:
                    return self.redirect(referrer)
                return self.redirect_to('/')
        else:
            self.redirect('/signup')

    def post(self):
        """
        handles the POST request from newpost.html
        """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            post_id = self.request.get('post_id')
            comment_id = self.request.get('comment_id')
            subject_input = self.request.get('subject')
            content_input = self.request.get('content')
            comment_key = db.Key.from_path('Comment',
                                           int(comment_id),
                                           parent=post_key(post_id))
            # gets the post data based upon what
            # is passed from post_id into key
            # if subject and content exist create an entity (row) in the GAE
            # datastor (database) and redirect to a permanent link to the post
            if subject_input and content_input:
                comment = db.get(comment_key)
                comment.subject = subject_input
                comment.content = content_input
                comment.put()
                # redirects to a single blog post passing the post id
                # from the function as a string to a pagewhere the post_id
                # is the url
                self.redirect('/comment-%s?post_id=%s' % (comment_id, post_id))
            else:
                input_error = "Please submit both the title and the content."
                self.render("editcomment.html", subject=subject_input,
                            content=content_input, error=input_error,
                            comment_id=comment_id, post_id=post_id)
        else:
            self.redirect('/signup')


class DeletePost(TemplateHandler, AuthHandler):
    """ This handles the deletion of blog posts """
    def post(self):
        """ Submits data to the server to delete the post """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            post_id = self.request.get('post_id')
            key = db.Key.from_path('Post',
                                   int(post_id),
                                   parent=blog_key())
            # gets the post data based upon what
            # is passed from post_id into key
            db.delete(key)
            self.render('/postdeleted.html')
        else:
            self.redirect('/signup')


class DeleteComment(TemplateHandler, AuthHandler):
    """ This handles the deletion of blog posts """
    def post(self):
        """ Submits data to the server to delete the post """
        auth_error = True
        if self.read_secure_cookie('usercookie'):
            auth_error = False
        else:
            auth_error = True
        username = self.read_secure_cookie('usercookie')
        if not self.user_exists(username):
            auth_error = False
        else:
            auth_error = True

        if not auth_error:
            comment_id = self.request.get('comment_id')
            post_id = self.request.get('post_id')
            key = db.Key.from_path('Comment',
                                   int(comment_id),
                                   parent=post_key(post_id))
            # gets the post data based upon what
            # is passed from post_id into key
            db.delete(key)
            self.render('/commentdeleted.html')
        else:
            self.redirect('/signup')


# GAE APPLICATION VARIABLE
# This variable sets the atributes of the individual HTML
# files that will be served using google app engine.
# '/([0-9]+)' recieves post_id from NewPostHandler class passing it
# into PermaPost class via the url using regular expression
WSGI_APP = webapp2.WSGIApplication([('/?', MainPage),
                                    ('/post-([0-9]+)',
                                     PostLinkHandler),
                                    ('/comment-([0-9]+)',
                                     CommentLinkHandler),
                                    ('/newpost', NewPostHandler),
                                    ('/newcomment', NewCommentHandler),
                                    ('/signup', UserSignUpHandler),
                                    ('/editpost', EditPost),
                                    ('/editcomment', EditComment),
                                    ('/login', UserLoginHandler),
                                    ('/logout', UserLogoutHandler),
                                    ('/deletepost', DeletePost),
                                    ('/deletecomment', DeleteComment),
                                    ('/welcome', WelcomeHandler)
                                    ], debug=True)
