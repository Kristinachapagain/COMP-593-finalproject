import sys
from datetime import datetime, date
import requests
import os
import inspect
import urllib.request
from PIL import Image
import sqlite3
import hashlib
import ctypes

class APOD:
    

    def __init__(self):
        if len(sys.argv) < 2:
            date = datetime.today().strftime('%Y-%m-%d')
        else:
            date = sys.argv[1].replace("'", "")
        date_validated = self.validate_date(date)
        if date_validated == True:
            self.set_date(date)
            self.download_and_set_image()
        else:
            if self.isFuture(date):
                print("Script execution aborted")
            else:
                print("Error: Invalid date format;", date_validated)
                print("Script execution aborted")
    id = None
    image_dir = None
    db = None
    date = None
    media_type = None
    url = None
    image_url = None
    image_name = None
    image_title = None
    explanation = None
    file_path = None
    hash_code = None
    key = None
    params = dict()
    
    def download_and_set_image(self):
        self.set_params(self.date)
        self.set_key("LEfOyYM1IbPXp6rVre2XNekoru46CIKrSWDtATSm")
        self.set_url("https://api.nasa.gov/planetary/apod?api_key="+self.key)
        current_path = os.path.dirname(os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename))
        self.set_image_dir(os.path.join(current_path, "images"))
        self.set_db(os.path.join(current_path, "images/image_cache.db"))
        self.set_connection()
        print("APOD date:", self.date)
        image_info = self.get_image_info_from_date()
        if 'code' in image_info:
            print(image_info["msg"])
        else:
            if image_info["media_type"] != 'image':
                self.set_image_url(image_info["thumbnail_url"])
            else:
                self.set_image_url(image_info["url"])
            self.set_explanation(image_info["explanation"])
            print("Getting " + self.date + " APOD information from NASA...success")
            self.add_image_to_cache(image_info)
            self.add_image_to_db(image_info)
            self.set_desktop_bg()
    
    def set_id(self, _id):
        self.id = _id
    def set_date(self, _date):
        self.date = _date
    def set_image_dir(self, _image_dir):
        print("Image cache directory: " + _image_dir)
        if not os.path.exists(_image_dir):
            os.mkdir(_image_dir)
            print("Image cache directory created.")
        else:
            print("Image cache directory already exists.")
        self.image_dir = _image_dir
    def set_db(self, _db):
        print("Image cache DB: " + _db)
        self.db = _db
        if not os.path.exists(_db):
            sqlite3.connect(_db)
            print("Image cache DB created.")
        else:
            print("Image cache DB already exists.")
    def set_connection(self):
        self.connection = sqlite3.connect(self.db)
    def set_media_type(self, _type):
        self.media_type = _type
    def set_url(self, _url):
        self.url = _url
    def set_image_url(self, _image_url):
        self.image_url = _image_url
    def set_image_name(self, _image_name):
        self.image_name = _image_name
    def set_image_title(self, _image_title):
        self.image_title = _image_title
    def set_explanation(self, _explanation):
        self.explanation = _explanation
    def set_file_path(self, _file_path):
        self.file_path = _file_path
    def get_file_path(self):
        return self.file_path
    def set_hash_code(self, _hash_code):
        self.hash_code = _hash_code
    def get_hash_code(self):
        return self.hash_code;
    def set_key(self, _key):
        self.key = _key
    def set_params(self, _date):
        self.params = {"date": _date, "thumbs": "True"}
    def get_params(self):
        return self.params
    def get_connection(self):
        return self.connection
    def get_url(self):
        return self.url
    
    def validate_date(self, date):
        today = datetime.now()
        specific_date = datetime(1995, 6, 16)
        try:
            datetime.fromisoformat(date)
        except ValueError as e:
            return str(e)
        date = datetime.strptime(date, "%Y-%m-%d")
        try:
            if date < today and date > specific_date:
                return True
            else:
                print("Error:  APOD date cannot be in the future")
                return False
        except ValueError as e:
            return False

    def isFuture(self, date):
        today = datetime.now()
        specific_date = datetime(1995, 6, 16)
        try:
            if datetime.strptime(date, "%Y-%m-%d") > today:
                return True
            else:
                return False
        except Exception as e:
            return False
        
    def create_db(self, _db):
        try:
            connection = sqlite3.connect(_db)
            self.set_connection(connection)
        except sqlite3.Error as error:
            print(str(error))
            
    def get_image_info_from_date(self):
        image_info = requests.get(url = self.get_url(), params = self.get_params()).json()
        return image_info

    def add_image_to_cache(self, image_info):
        image_name = ""
        for i in image_info["title"].strip():
            if i == " ":
                image_name = image_name + "_"
            elif i == "_":
                image_name = image_name + i
            elif i.isalnum():
                image_name = image_name + i
        image_ext = self.image_url.split(".")
        self.set_image_name(image_name + "." + image_ext[len(image_ext) - 1])
        self.set_image_title(image_info["title"])
        print("APOD title: " + self.image_title)
        print("APOD URL: " + self.image_url)
        print("Downloading image from " + self.image_url + "...success")
        self.set_file_path(os.path.join(self.image_dir, self.image_name))
        
        #Save the Image to the image cache directory
        if not os.path.exists(self.get_file_path()):
            raw_image = requests.get(self.image_url).content
            image = open(os.path.join(self.get_file_path()), "wb")
            image.write(raw_image)
            image.close()
        self.set_hash_code(self.create_hash_from_image())
        print("APOD SHA-256: " + self.hash_code)
            
    def add_image_to_db(self, image_info):
        query = "CREATE TABLE if not exists images (id integer NOT NULL PRIMARY KEY, title varchar(255) NOT NULL, explanation text NOT NULL, file_path varchar(255) NOT NULL, sha256  UNSIGNED BIG INT NOT NULL)"
        connection = self.get_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        
        #Insert query
        if not self.check_if_image_exists():
            print("APOD image is not already in cache.")
            #query = "insert into images (title, explanation, file_path, sha256) values ('"+self.image_title+"', \""+self.explanation+"\", '"+self.get_file_path()+"', '"+self.get_hash_code()+"')"
            query = "insert into images (title, explanation, file_path, sha256) values (?, ?, ?, ?)"
            cursor.execute(query, (self.image_title, self.explanation, self.get_file_path(), self.get_hash_code()))
            print("APOD file path: " + self.get_file_path())
            print("Saving image file as " + self.get_file_path() + "...success")
            self.set_id(cursor.lastrowid)
        else:
            print("APOD image is already in cache.")
        connection.commit()

    def create_hash_from_image(self):
        sha256 = hashlib.sha256()
        with open(self.get_file_path(), "rb") as hash_code:
            for byte_block in iter(lambda: hash_code.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()

    def check_if_image_exists(self):
        query = "select id from images where sha256 = '" + self.get_hash_code() + "'"
        connection = self.get_connection()
        cursor = connection.cursor()
        result = cursor.execute(query).fetchall()
        if result == []:
            print("Adding APOD to image cache DB...success")
            return False
        else:
            self.set_id(result[0][0])
            return True
    
    def get_image_info_from_id(self):
        pass
    
    def set_desktop_bg(self):
        if sys.platform == "win32":
            ctypes.windll.user32.SystemParametersInfoW(20, 0, self.file_path, 3)
        else:
            image_lib.set_desktop_background_image(self.file_path)
        print("Setting desktop to " + self.file_path + "...success")



apod = APOD()
#apod.download_and_set_image()
