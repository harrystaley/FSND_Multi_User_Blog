# ART HOMEWORK
class Art(db.model):
    """ Database class for art homework """
    title = db.StringProperty(Required=True)
    art = db.TextProperty(Required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class ArtHandler(Handler):
    """ This is the handler class fo the art homework """
    def render_art(self, title="", art="", error=""):
        # arts = db.GqlQuery("SELECT * FROM Art " +
                           # "ORDER BY created DESC ")
        self.render('asciiart.html', title=title,
                    art=art, error=error)

    def get(self):
        self.render_art()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        a = Art(title=title, art=art)
        a.put()

        self.redirect("/asciiart.html")
