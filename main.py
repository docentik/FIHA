#!/usr/bin/env python
### Author: Stanislav PetrÌk fiha-on

import logging
from cgi import escape
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.db import Key
from django.utils import simplejson as json

# vytv·ra v google db tieto 3 poloûky, komunikuje cez tag a value s App Inventor :

class StoredData(db.Model):
  tag = db.StringProperty()
  value = db.TextProperty()
  date = db.DateTimeProperty(required=True, auto_now=True)

# TitulnÈ knoflÌky -premenn· Uvod :

Uvod = '''
<table border=0>
 <td><button onclick= location.reload()>Refresh</button></td>
 <td><image src="/images/giv.png" width="40" hspace="10"></td>
 <td><button onClick=location.href='http://fiha-st.appspot.com'>Straty a N·lezy</button></td>
 <td><button onClick=location.href='http://fiha-elo.appspot.com'>ELO</button></td>
</table>'''
 
class MainPage(webapp.RequestHandler):

  def get(self):
    write_page_header(self);
    self.response.out.write(Uvod)
    write_available_operations(self)
    show_stored_data(self)
    self.response.out.write('</body></html>')

########################################
### Implementovanie oper·ciÌ
### Kaûd· oper·cia je navrhnut·, aby odpovedala JSON poûiadavke
### alebo Web form, z·visÌ Ëi fmt input POST je json al. html
### Kaûd· oper·cia je class. Class zah‡Úa metÛdu, ktor· aktu·lne manipuluje s DB,
### nasleduj˙c oper·cia post al. get

class StoreAValue(webapp.RequestHandler):

  def store_a_value(self, tag, value):
    # There's a potential readers/writers error here :(
    entry = db.GqlQuery("SELECT * FROM StoredData where tag = :1", tag).get()
    if entry:
      entry.value = value
    else: entry = StoredData(tag = tag, value = value)
    entry.put()
    ## Posiela sp‰ù potvrdenie do google db. TinyWebDB component ignoruje potvrdenie
    ## (iba, ûe to bolo prijatÈ), ale ostatnÈ komponenty to mÙûu pouûiù
    result = ["STORED", tag, value]
    WritePhoneOrWeb(self, lambda : json.dump(result, self.response.out))

### lambda funkcia bez returnu

  def post(self):
    tag = self.request.get('tag')
    value = self.request.get('value')
    self.store_a_value(tag, value)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/storeavalue" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Tag<input type="text" name="tag" /></p>
       <p>Value<input type="text" name="value" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Store a value">
    </form></body></html>\n''')

class GetValue(webapp.RequestHandler):

  def get_value(self, tag):
    entry = db.GqlQuery("SELECT * FROM StoredData where tag = :1", tag).get()
    if entry:
      value = entry.value
    else: value = ""
    ## Tag vr·ten˝ v˝sledok s  "VALUE".  pre TinyWebDB
    ## Component to nepouûÌva, ale ostatnÈ programy mÙûu.
    ## Kontroluje, Ëi to je html, ak ·no, potom vyËisti tag a hodnoty premenn˝ch
    if self.request.get('fmt') == "html":
      value = escape(value)
      tag = escape(tag)
    WritePhoneOrWeb(self, lambda : json.dump(["VALUE", tag, value], self.response.out))

  def post(self):
    tag = self.request.get('tag')
    self.get_value(tag)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/getvalue" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Tag<input type="text" name="tag" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get value">
    </form></body></html>\n''')


### The DeleteEntry is called from the Web only, by pressing one of the
### buttons on the main page.  So there's no get method, only a post.

class DeleteEntry(webapp.RequestHandler):

  def post(self):
    logging.debug('/deleteentry?%s\n|%s|' %
    (self.request.query_string, self.request.body))
    entry_key_string = self.request.get('entry_key_string')
    key = db.Key(entry_key_string)
    tag = self.request.get('tag')
    db.run_in_transaction(dbSafeDelete,key)
    self.redirect('/')


####################################
#### Proced˙ry zobrazenÈ na hlavnej str·nke

### Ukazuje API
def write_available_operations(self):
  self.response.out.write('''
  ''')

### Vytv·ra hlaviËku

def write_page_header(self):
  self.response.headers['Content-Type'] = 'text/html'
  self.response.out.write('''
     <html>
     <head>
     <style type="text/css">
        body {background-color:black;font-size:20px;margin-left: 5% ; margin-right: 5%; margin-top: 0.1in;
             font-family: verdana, arial,"trebuchet ms", helvetica, sans-serif;}
        button {font-size:30px; background-color:silver;}
        h4 {color:gray;}
        table {font-family: Arial; border: 3px solid dimgray; padding: 4px; border-spacing: 5px;}
        th {font-size:40px; border: 3px solid darkgray; padding: 10px; cellspacing:20px;}
        td {font-size:25px; color: silver; border: 1px solid darkgray;text-align:center; padding: 10px;}
        ul {list-style: disc;}
        a {color:gray;}
     </style>
     <title>Tiny WebDB</title>
     </head>
     <body>''')
### self.response.out.write('<h2>App Inventor for Android: zakaznicky Tiny WebDB servis</h2>')

### Ukazuje Tagy a hodnoty v tabulke
def show_stored_data(self):
#  self.response.out.write('''
 #        <p> <table>''')
  entries = StoredData.all().order("-tag")
  for e in entries:
     entry_key_string = str(e.key())
     if (e.tag) == 'loc':
      tmp = e.value
   #    tmp = '"https:\/\/www.instantstreetview.com\/Habursk· 92\/49 831 04 Bratislava Slovensko"'
   #   self.response.out.write('<p><table><td>')
  #    self.response.out.write('<button onClick=location.href=')
  #    self.response.out.write(tmp)
    #  self.response.out.write('>Kde ?')
#</button></td>')
   #   self.response.out.write('</table>')
      self.response.out.write('<h4>  <a href=')
      self.response.out.write(tmp)
      self.response.out.write('>miesto</a>')
     if (e.tag) == 'on' :
      self.response.out.write('<p><table>')
      self.response.out.write(e.value)
      self.response.out.write('</table>')
      self.response.out.write('<br>')
      self.response.out.write('<h4>')
      self.response.out.write(e.date.ctime())

#### Proced˙ry pre Output :

#### PÌöe odpoveÔ na mobil alebo Web v z·vislosti od skrytÈho fmt
#### Handler (manaûÈr) je appengine request handler.  writer je
#### (napr. proced˙ra bez argumentov) to Ëo pÌöe.

def WritePhoneOrWeb(handler, writer):
  if handler.request.get('fmt') == "html":
    WritePhoneOrWebToWeb(handler, writer)
  else:
    handler.response.headers['Content-Type'] = 'application/jsonrequest'
    writer()

#### V˝sledok, ak sa pÌöe na Web

def WritePhoneOrWebToWeb(handler, writer):
  handler.response.headers['Content-Type'] = 'text/html'
  handler.response.out.write('<html><body>')
  handler.response.out.write('''
  <em>Server toto poöle componentu:</em>
  <p />''')
  writer()
  WriteWebFooter(handler, writer)


#### PÌöe na Web (bez kontroly fmt)

def WriteToWeb(handler, writer):
  handler.response.headers['Content-Type'] = 'text/html'
  handler.response.out.write('<html><body>')
  writer()
  WriteWebFooter(handler, writer)

def WriteWebFooter(handler, writer):
  handler.response.out.write('''
  <p><a href="/">
  <i>N·vrat na hlavn˙ str·nku</i>
  </a>''')
  handler.response.out.write('</body></html>')

### Proced˙ra br·niaca zruöeniu neexistuj˙ceho objektu

def dbSafeDelete(key):
  if db.get(key) :  db.delete(key)


### Priradenie classes ku URL's

application =     \
   webapp.WSGIApplication([('/', MainPage),
                           ('/storeavalue', StoreAValue),
                           ('/deleteentry', DeleteEntry),
                           ('/getvalue', GetValue)
                           ],
                          debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

### Copyright 2015
