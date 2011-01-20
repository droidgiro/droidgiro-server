# coding=UTF-8
from google.appengine.ext import db

class Pin(db.Model):
    code = db.IntegerProperty()
    channel = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
