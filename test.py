import firebase_admin
from firebase_admin import credentials,db
import json
import os

class FirebaseControls:
    def __init__(self):
        cred = credentials.Certificate("./service-account/recordmatcher-firebase-adminsdk-mfcn7-d0ee2c6bad.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://recordmatcher-default-rtdb.firebaseio.com/'
        })
        self.table_ref = db.reference("/table/") 
        self.leftMenu_ref = db.reference('/leftMenu/')   
    def set_mastertable_data(self, child, data):
        return self.table_ref.child(child).set(data)
    def remove_mastertable_data(self, child, data):
        return self.table_ref.child(child).set({}) 
    def get_mastertable_data(self):
        return self.table_ref.get() 
    def set_leftMenu_data(self, data):
        return self.leftMenu_ref.set(data)
    def get_leftMenu_data(self):
        return self.leftMenu_ref.get()     
        
    
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

firebaseControls = FirebaseControls()
json_path = os.path.join(CURRENT_DIR, "data.json")
data = firebaseControls.get_mastertable_data()
print(data)
# a = {"vava":{
# 	"Book1":
# 	{
# 		"Title": "The Fellowship of the Ring",
# 		"Author": "J.R.R. Tolkien",
# 		"Genre": "Epic fantasy",
# 		"Price": 100
# 	},
# 	"Book2":
# 	{
# 		"Title": "The Two Towers",
# 		"Author": "J.R.R. Tolkien",
# 		"Genre": "Epic fantasy",
# 		"Price": 100	
# 	},
# 	"Book3":
# 	{
# 		"Title": "The Return of the King",
# 		"Author": "J.R.R. Tolkien",
# 		"Genre": "Epic fantasy",
# 		"Price": 100
# 	},
# 	"Book4":
# 	{
# 		"Title": "Brida",
# 		"Author": "Paulo Coelho",
# 		"Genre": "Fiction",
# 		"Price": 100
# 	}
# }}
# b = {"vava2":{
# 	"Book1":
# 	{
# 		"Title": "The Fellowship of the Ring",
# 		"Author": "J.R.R. Tolkien",
# 		"Genre": "Epic fantasy",
# 		"Price": 100
# 	},
# 	"Book2":
# 	{
# 		"Title": "The Two Towers",
# 		"Author": "J.R.R. Tolkien",
# 		"Genre": "Epic fantasy",
# 		"Price": 100	
# 	},
# 	"Book3":
# 	{
# 		"Title": "The Return of the King",
# 		"Author": "J.R.R. Tolkien",
# 		"Genre": "Epic fantasy",
# 		"Price": 100
# 	},
# 	"Book4":
# 	{
# 		"Title": "Brida",
# 		"Author": "Paulo Coelho",
# 		"Genre": "Fiction",
# 		"Price": 100
# 	}
# }}
# firebaseControls.pushTo_table(a)
# firebaseControls.pushTo_table(b)
# print(firebaseControls.get_mastertable_data('vava2'))