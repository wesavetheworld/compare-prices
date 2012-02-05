import webapp2
#from webapp2_extras import jinja2
import jinja2
import os
import random
from itertools import *
from operator import itemgetter
import pprint
from BeautifulSoup import BeautifulSoup
import re


jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
from google.appengine.api import users
from models import *

class init(webapp2.RequestHandler):
    def get_page_content(self,url):
        from google.appengine.api import urlfetch
        result = urlfetch.fetch(url=url)
        if result.status_code == 200:
            return result.content

    def get(self):
        for m in [Page,Site, Product]:
            print '*'*8, m
            for i in m.query():
                i.key.delete()
        self.response.out.write('ok, nuked')
        t = Site(
            name = 'greenfingers.com',
            price_class= 'greenfingers',
            url = 'http://www.greenfingers.com'
        )
        t.put()
        for name, url in [
            ('LS6157D Fire pit',
             'http://www.greenfingers.com/superstore/product.asp?dept_id=2211&pf_id=LS6157D'
            ),
            ('DD4251 Grilletto',
             'http://www.greenfingers.com/superstore/product.asp?dept_id=200398&pf_id=DD4215D'
                ),
            ('Steel Oil Drum',
             'http://www.greenfingers.com/superstore/product.asp?dept_id=200398&pf_id=LS4303D'
                ),
            (' Moroccan Fire Basket',
             'http://www.greenfingers.com/superstore/product.asp?dept_id=2211&pf_id=CA1078D'
                ),
        ]:
            p = Product(name = name,our_price = 20+ random.random(),sku = name)
            p.put()
            page = Page(url =url,
                        product = p.key,
                        site = t.key,
                        current_price = 99.9)
            page.put()


class update(webapp2.RequestHandler):

    def store_archive(self,page):
        a = Archive_Price(
            product = page.product,
            date=page.date,
            price =page.current_price
        )
        a.put()

    def get(self):
        allpages = Page.query().fetch()
        for page in allpages:
            site = Site.query(Site.key == page.site).get()
            g = eval(site.price_class)()
            page.current_price = g.get_price(url = page.url)
            self.store_archive(page)
            page.put()
        self.response.out.write('pages scraped and updated')

class MainPage(webapp2.RequestHandler):
    def grouper(self,data):
        data.sort()
        r = []
        for product_key, outer_grouper in groupby(data, lambda o:o.product):
            p = Product.query(Product.key== product_key).get()
            for site_name, inner_grouper in groupby(list(outer_grouper), lambda o:o.url):
                for page in inner_grouper:
                    page.product_data = p
                    s = Site.query(Site.key == page.site).get()
                    page.site_name = s.name
                    r.append(page)
        r = sorted(r, key=lambda p: p.product_data.name)
        return r

    def get(self):
        allproducts = Product.query().fetch()
        allpages = Page.query().order(Page.product).fetch()
        product_list = self.grouper(data=allpages)
        template_values = {
            'products':allproducts,
            'pages': product_list,
            }

        template = jinja_environment.get_template('templates/main.html')
        self.response.out.write(template.render(template_values))


app = webapp2.WSGIApplication([
        ('/init', init),
        ('/get', update),
        ('/', MainPage),
    ],debug=True)