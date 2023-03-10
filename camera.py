import tornado.ioloop
import tornado.web
import os, time

import datetime, math
from PIL import Image, ImageDraw, ImageEnhance

import base64
import uuid

import config

# crea un cookie per l'utente loggato
cookie_secret = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)

# processa le immagini con un timestamp
class CameraImageProcessor():
	def __init__(self, in_filename, out_filename, width=640, height=480):
		self.size = (width, height)
		self.in_filename = in_filename
		self.out_filename = out_filename

	def process(self, prefix, postfix):
		now = datetime.datetime.now()
		original = Image.open(self.in_filename)
		original.thumbnail(self.size, Image.ANTIALIAS)
		#original = ImageEnhance.Brightness(original).enhance(self.getDaylightIntensity(now.hour)) # overwrite original
		watermark = Image.new("RGBA", original.size)
		waterdraw = ImageDraw.ImageDraw(watermark, "RGBA")
		waterdraw.text((4, 2), "%s @ %s -- %s" % (prefix, now, postfix))
		original.paste(watermark, None, watermark)
		original.save(self.out_filename, "JPEG")

	def getDaylightIntensity(self, hour):
		return 0.45 * math.sin(0.25 * hour + 4.5) + 0.5

# classe delle immagini
class ImageClass():
	def __init__(self):
		self.images = [file for file in os.listdir(config.IMAGES_DIR) if file.endswith(".jpeg")]
		self.counter = 0
	
	def getImage(self):
		res = self.images[self.counter]
		self.counter = (self.counter + 1)%len(self.images)
		return str(res)

# gestisce la richiesta della camera e il processing delle foto 
class ImageHandler(tornado.web.RequestHandler):
	
	BOUNDARY = '--boundarydonotcross'
	HEADERS = {
        'Cache-Control': 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0',
        'Connection': 'close',
        'Expires': 'Mon, 3 Jan 2000 12:34:56 GMT',
        'Pragma': 'no-cache'
    }

	def get(self):
		if self.get_secure_cookie("username"):
			for hk, hv in ImageHandler.HEADERS.items():
				self.set_header(hk, hv)

			# # TODO: Do not process if current
			global image
			img_name = image.getImage()
			img_proc_filename = config.IMAGES_DIR_PROC + img_name
			img_filename = config.IMAGES_DIR + img_name

			cip = CameraImageProcessor(img_filename, img_proc_filename)
			cip.process(config.CAMERA_NAME, config.CAMERA_DESCRIPTION)


			for hk, hv in self.image_headers(img_proc_filename).items():
				self.set_header(hk, hv)

			with open(img_proc_filename, "rb") as f:
				self.write(f.read())
		else:
			self.redirect("/")

	def image_headers(self, filename):
		return {
			'X-Timestamp': int(time.time()),
			'Content-Length': os.path.getsize(filename),
			'Content-Type': 'image/jpeg',
		}

# gestisce la pagina della presa shelly
class ShellyHandler(tornado.web.RequestHandler):
	def get(self):
		return self.render("templates/shelly.html")

# gestisce la pagina contenente la camera
class HomeHandler(tornado.web.RequestHandler):
	settings = {
		'title': config.CAMERA_NAME,
		'refresh': config.REFRESH_TIME,
	}
	
	def get(self):
		if self.get_secure_cookie("username"):
			return self.render("templates/home.html", page=HomeHandler.settings)
		else:
			self.redirect("/")



# gestisce la pagina / con il login
class RootHandler(tornado.web.RequestHandler):

	def get(self):
		if not self.get_secure_cookie("username"):
			return self.render("templates/index.html")
		else:
			self.redirect("/home")

	def post(self):
		username = self.get_argument("username")
		password = self.get_argument("password")
		if username == config.USERNAME and password == config.PASSWORD:
			self.set_secure_cookie("username", username)
			self.redirect("/home")
		else:
			self.write("Login failed")
			self.redirect("/")

# inizializza la classe delle immagini
image = ImageClass()

# modifica gli header del server
class ServerHeaderTransform(tornado.web.OutputTransform):
    def transform_first_chunk(self, status_code, headers, chunk, finishing):
        headers['Server'] = config.SERVER_HEADER_NAME
        return status_code, headers, chunk

# path dei servizi 
application = tornado.web.Application([
	(r'/camera', ImageHandler),
	(r'/home', HomeHandler),
	(r'/shelly', ShellyHandler),
	(r'/', RootHandler),
	(r'/(favicon\.ico)', tornado.web.StaticFileHandler, {'path': 'static/'}),
	(r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static/'}),
], transforms=[ServerHeaderTransform], cookie_secret=cookie_secret)

# main
if __name__ == "__main__":
	application.listen(config.PORT)
	tornado.ioloop.IOLoop.instance().start()

