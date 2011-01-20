# coding=UTF-8

from google.appengine.api import users
from google.appengine.api import channel
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext import db
import os
from datetime import datetime, time, date, timedelta
import time
import random
import md5
from django.utils import simplejson
from agiro.models import Pin

class MainPage(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), '../templates/index.html')
        self.response.out.write(template.render(path, template_values))

class InvoiceHandler(webapp.RequestHandler):
    def post(self, invoice_id):
        identifier = self.request.get('identifier')

        if not identifier:
            self.response.set_status(401)
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.out.write(simplejson.dumps("Unauthorized"))
            return

        invoice = {}
        invoice.setdefault('reference', self.request.get('reference'))
        invoice.setdefault('type', self.request.get('type'))
        invoice.setdefault('amount', self.request.get('amount'))

        response = simplejson.dumps(invoice)

        channel.send_message(str(identifier), response)

        self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
        self.response.set_status(201)
        self.response.out.write(response)

class RegisterHandler(webapp.RequestHandler):
    def get(self):
        random.seed()
        hash = random.getrandbits(128)
        channel_name = "%016x" % hash

        iterations = 0
        found = False
        while not found:
            pin_code = random.randint(1000, 9999)
            q = Pin.all()
            q.filter('code = ', pin_code)
            pin = q.get()

            if pin:
                time = datetime.utcnow() - timedelta(minutes=5)
                if pin.date <= time:
                    pin.code = pin_code
                    pin.channel = channel_name
                    pin.date = datetime.utcnow()
                    pin.put()
                    found = True
                else:
                    pin = None
            else:
                pin = Pin()
                pin.code = pin_code
                pin.channel = channel_name
                pin.put()
                found = True

            iterations += 1
            if iterations >= 10:
                found = True
                pin = None

        if not pin:
            self.response.set_status(409) # Conflict
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.out.write(simplejson.dumps("Try again."))
        else:
            token = channel.create_channel(pin.channel)
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.out.write(simplejson.dumps({
                'token': token,
                'channel': pin.channel,
                'pin': pin.code,
            }))

    def post(self):
        pin_code = self.request.get('pin')
        if not pin_code:
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.set_status(400)
            self.response.out.write(simplejson.dumps('Missing parameters.'))
            return
        try:
            pin_code = int(pin_code)
        except:
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.set_status(400)
            self.response.out.write(simplejson.dumps('Bad parameters.'))
            return

        q = Pin.all()
        q.filter('code = ', pin_code)
        pin = q.get()

        if not pin:
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.set_status(401)
            self.response.out.write(simplejson.dumps('Unauthorize, must register again.'))
        else:
            channel.send_message(pin.channel, simplejson.dumps('Connected'))
            self.response.headers.add_header("Content-Type", 'application/json; charset=utf-8')
            self.response.out.write(simplejson.dumps({
                'channel': pin.channel,
            }))

