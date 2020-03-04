# Video Call Metrics Collector
Daily.co Video Call Metrics Collector

The Video Call Metrics Collector is a highly simplified metrics viewer for [Daily.co](http://daily.co/) video calls. It's a Python Flask application that allows users to start video calls and view dashboards of their video call network statistics. This is all made possible with the use of Daily.co's [front-end and REST API](https://docs.daily.co/reference).

## Requirements
The following modules are required to successfully run the application:
* [Python 3.7 or higher](https://www.python.org/downloads/)
* [Flask](https://palletsprojects.com/p/flask/)
* [Matplotlib](https://matplotlib.org/)
* [pyOpenSSL](https://www.pyopenssl.org/en/stable/)

## How to Run the Code
### Running on Local Machine
1. Obtain an API KEY from [Daily.co](https://www.daily.co/). You will need an API KEY in order to create new video calls.
2. Create a file called **config.ini** in the application root directory. This file will contain several configuration properties required by the application. Enter the following in the file:
```
[DEFAULT]
SERVER_HOST = <SERVER HOST ADDRESS>
SERVER_PORT = <SERVER PORT>
SERVER_NAME = <SERVER NAME>
DEBUG_MODE = 1
PROD_MODE = 0
DAILY_API_KEY = <YOUR-API-KEY>
```
3. Execute the application
```
python run.py
```
Once the flask process starts, open your browser and navigate to the application. https://[serverhost]:[serverport]/. One important point worth mentioning: **The application must be accessed using HTTPS, not HTTP**. Your browser will block the use of your camera and microphone on an HTTP connection, leaving you no option to enable them. An HTTPS connection will allow the use these devices. 
### Deploying on Remote Server using Apache
1. Steps 1 and 2 of instructions for Running on Local Machine.
2. Install apache2 webserver and mod_wsgi
```
sudo apt-get update
sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi
```
3. Create a python virtual environment for the application.
```
virtualenv venv 
```
4. Link the site-root defined in apache's configuration (/var/www/html by default) to the application directory.
```
sudo ln -sT ~/VideoCallMetricsCollector /var/www/html/VideoCallMetricsCollector
```
5. In the application root directory, create a file named **VideoCallMetricsCollector.wsgi**. Enter the following in that file:
```
activate_this = '<PATH_TO_VIRTUAL_ENVIRONMENT>'
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))
import sys
sys.path.insert(0, '/var/www/html/VideoCallMetricsCollector')
from run import app as application
```
6. Use openssl to generate a self signed SSL certificate for the application. The command will create a cert.pem and key.pem file.
```
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```
7. Enable the mod_ssl module
```
sudo a2enmod ssl
```
8. Enter the following information in the apache configuation file located at /etc/apache2/sites-enabled/000-default.conf.
```
<VirtualHost *:443>
        ServerAdmin webmaster@localhost
        DocumentRoot /var/www/html

        SSLEngine on
        SSLCertificateFile [PATH_TO_SSL_CERTIFICATE_PEM_FILE]
        SSLCertificateKeyFile [PATH_TO_SSL_KEY_FILE]

        WSGIDaemonProcess SecureVideoCallMetricsCollector
        WSGIScriptAlias / /var/www/html/VideoCallMetricsCollector/VideoCallMetricsCollector.wsgi

        <Directory /var/www/html/VideoCallMetricsCollector>
            WSGIProcessGroup SecureVideoCallMetricsCollector
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>

        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```
9. Restart the web server
```
sudo service apache2 restart
```
10. Create a new folder in the application root called video_logs. This will be where the application stores call metrics collected during web meetings. Give apache permission to write to this directory.
```
chmod 0777 ~/VideoCallMetricsCollector/video_logs
```
11. Navigate to the application in the browser
## Using the Video Call Metrics Collector
1. You can start a new video call by clicking on the first link you see on the home page. The app will redirect you to another page with the video call embedded in it. The link to the meeting is provided on top of the page that you can share with other people so they can join the meeting.
2. Once you're done with the meeting, navigate back to the home page. An additional link will appear that will take you to a dashboard for the meeting.
3. **IMPORTANT: This application is not designed to handle more than one user starting meetings and viewing call metrics at the same time**. Please keep that in mind while using the application. 
