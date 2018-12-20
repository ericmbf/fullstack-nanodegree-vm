from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem
import cgi


engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind=engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

class webServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path.endswith("/restaurants"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                restaurants = session.query(Restaurant).all()
                output = ""
                output += "<html><body>"
                output += "<h1><a href='restaurant/new'> \
                            Make a New Restaurant</a></h1>"
                for restaurant in restaurants:
                    output += "<h2>{}</h2>".format(restaurant.name)
                    output += "<h3><a href='restaurant/{}/edit'>Edit</a></h3>".format(restaurant.id)
                    output += "<h3><a href='restaurant/{}/delete'>Delete</a></h3>".format(restaurant.id)

                output += "</body></html>"
                self.wfile.write(output)
                # print output
                return

            if self.path.endswith("/restaurant/new"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>"
                output += "<h1>Make a New Restaurant</h1>"
                output += '''<form method='POST' enctype='multipart/form-data'\
                                action='/restaurant/new'> \
                                <input name="restaurant" type="text" >\
                                <input type="submit" value="Create"> \
                            </form>'''
                output += "</body></html>"
                self.wfile.write(output)
                # print output
                return

            if self.path.endswith("/edit"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                url = self.path
                id = url.split('/')[-2]

                restaurant = session.query(Restaurant).filter_by(id = id).one()
                print restaurant
                output = ""
                output += "<html><body>"
                output += "<h1>{}</h1>".format(restaurant.name)
                output += '''<form method='POST' enctype='multipart/form-data'\
                                action='/restaurant/{}/edit'> \
                                <input name="restaurant" type="text" >\
                                <input type="submit" value="Edit"> \
                            </form>'''.format(restaurant.id)
                output += "</body></html>"
                self.wfile.write(output)
                # print output
                return
            
            if self.path.endswith("/delete"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                url = self.path
                id = url.split('/')[-2]

                restaurant = session.query(Restaurant).filter_by(id = id).one()
                print restaurant
                output = ""
                output += "<html><body>"
                output += "<h1>Are you sure you want to delete {}?</h1>".format(restaurant.name)
                output += '''<form method='POST' enctype='multipart/form-data'\
                                action='/restaurant/{}/delete'> \
                                <input type="submit" value="Delete"> \
                            </form>'''.format(restaurant.id)
                output += "</body></html>"
                self.wfile.write(output)
                # print output
                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            if self.path.endswith("/restaurant/new"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location','http://localhost:8080/restaurants')
                self.end_headers()
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    restaurantName = fields.get('restaurant')
                
                # Add new restaurant
                myRestaurant = Restaurant(name = restaurantName[0])
                session.add(myRestaurant)
                session.commit()
                return

            if self.path.endswith("/edit"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location','http://localhost:8080/restaurants')
                self.end_headers()
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    restaurantName = fields.get('restaurant')
                
                url = self.path
                id = url.split('/')[-2]

                # Edit restaurant
                restaurant = session.query(Restaurant).filter_by(id = id).one()
                restaurant.name = restaurantName[0]
                session.add(restaurant)
                session.commit()
                return

            if self.path.endswith("/delete"):
                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location','http://localhost:8080/restaurants')
                self.end_headers()
                ctype, pdict = cgi.parse_header(
                    self.headers.getheader('content-type'))
                
                url = self.path
                id = url.split('/')[-2]

                # Edit restaurant
                restaurant = session.query(Restaurant).filter_by(id = id).one()
                session.delete(restaurant)
                session.commit()
                return
        except:
            pass

def main():
    try:
        port = 8080
        server = HTTPServer(('', port), webServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()