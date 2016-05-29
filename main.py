import os
import jinja2
import webapp2
import re

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


def valid_userid(userId):
    """ validates the user id input by passing it through regex """
    return userId and USER_RE.match(userId)


def valid_password(password1):
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


class MainPage(Handler):
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


class FizzBuzzHandler(Handler):
    """ Class to handle FizzBuzz template """

    def get(self):
        """ uses GET request to render the main page and get the value of n """
        n = self.request.get('n', 0)
        n = n and int(n)
        self.render("fizzbuzz.html", n=n)


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


class UserSignup(Handler):
    """ This is the hander class for the user sign up page """

    def get(self):
        """ uses GET request to render the main page """
        self.render("signup.html")

    def post(self):
        """ handles the POST request from the signup page """
        haveError = False
        # GET requests for user input from signup page
        userId = self.request.get('userId')
        password1 = self.request.get('password1')
        password2 = self.request.get('password2')
        email = self.request.get('email')

        # dictionary to store error messages and userId and email if not valid
        params = dict(userId=userId, email=email)

        # tests for valid userid
        if not valid_userid(userId):
            params['errorUserId'] = 'Invalid User ID'
            haveError = True

        # tests for valid password and password match
        if not valid_password(password1):
            params['errorPassword1'] = 'Invalid Password'
            haveError = True
        elif password1 != password2:
            params['errorPassword2'] = 'Passwords do not Match'
            haveError = True

        # tests for valid email
        if not valid_email(email):
            params['errorEmail'] = 'Invalid Email'
            haveError = True

        # if there is an error re-render signup page
        # else render the welcome page
        if haveError:
            self.render("signup.html", **params)
        else:
            self.redirect('/welcome?userId=' + userId)


class Welcome(Handler):
    """ This is the handler class for the welcome page """
    def get(self):
        """ handles the GET request for the welcome paage """
        userId = self.request.get('userId')
        # If userId is valid render the welcome page.
        if valid_userid(userId):
            self.render("welcome.html", userId=userId)


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/fizzbuzz', FizzBuzzHandler),
    ('/rot13', Rot13Handler),
    ('/signup', UserSignup),
    ('/wecome', Welcome)
], debug=True)
