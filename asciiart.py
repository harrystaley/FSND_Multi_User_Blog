# ART HOMEWORK
class DArt(db.Model):
    """ Database class for art homework """
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class ArtHandler(TemplateHandler):
    """ This is the handler class fo the art homework """
    def get(self, title="", art="", error=""):
        arts = db.GqlQuery("SELECT * FROM DArt " +
                           "ORDER BY created DESC ")
        self.render('asciiart.html', title=title,
                    art=art, error=error, arts=arts)

    # def get(self):
    #     self.render_art()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        a = DArt(title=title, art=art)
        a.put()

        self.redirect("/asciiart")
