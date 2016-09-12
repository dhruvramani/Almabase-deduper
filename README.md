#Almabase-deduper
A Web-Application which uses Dedupe Library to cluster duplicate data. 

##Installation
```
$ git clone https://github.com/dhruvramani/Almabase-deduper
$ cd almabase
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```
If on Mac, see how to install Dedupe for mac on their offical docs

##Running
```
$ python manage.py runserver
```

##Features/Working
Uploads your CSV file and saves it in the database. Then lets you select the Column name which the user thinks plays a key role in guessing which data is duplicate or not. Then you train the app, in which you tell it first, wether the given pair is uncertain or not.

After training, it downloads a file, which contains column indicating the Cluster Id.

##Challenges faced
We are using the Dedupe library to do cluster the duplicate data, however the library by default does the training based on User Input through the command-line. So, to train it using a Web App, we had to get code from the original library, and had to somewhat re-impliment the function which handeled the command-line input. We used Ajax, to train but had to do a force reload of the page using Javascript because of some error. Also, had to put a `settimeout()` for the reload because the server was taking time to process the uncertain pairs.


