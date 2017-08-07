## Install dependencies ##

Start a terminal session as root.

    apt-get update
    apt install build-essential ssh git apache2 python3 postgresql postgresql-contrib libapache2-mod-wsgi-py3 python3-pip

    pip3 install --upgrade pip
    pip3 install flask sqlalchemy psycopg2

## Start Apache ##

    service start apache2

## Start postgres ##
Find out the version of your postgres cluster by running

    pg_lsclusters

then,

    pg_ctlcluster <version> main start


## Create postgres database ##

Replace `<username>` and `<password>` with desired ones.

    createdb sparts
    su - postgres
    psql sparts
    create user <username> with password '<password>';
    grant all privileges on database "sparts" to <username>;
    \q


## Clone sparts project ##

    mkdir -p /var/www/sparts
    git clone https://github.com/Wind-River/sparts-catalog-1 /var/www/sparts

## Remove the default apache test page ##

    rm /etc/apache2/sites-enabled/000-default.conf

## Create Apache server config ##

Copying the contents below to `/etc/apach2/sites-available/sparts.conf`:

    <VirtualHost *>
    <IfModule !wsgi_module>
    LoadMOdule wsgi_module wsgi.so
    </IfModule>

    WSGIScriptAlias / /var/www/sparts/sparts.wsgi

    <Directory /var/www/sparts>
        <Files sparts.wsgi>
            Require all granted
        </Files>

        Order allow,deny
        Allow from all
    </Directory>

    </VirtualHost>

Then make this config enabled by creating a soft link

    cd /etc/apache2/sites-enabled
    ln -s ../sites-available/sparts.conf


## create upload and artifact-files folders ##
Create two directories for upload data and artifacts data and make `www-data` their owner.

    mkdir -p /path/to/upload
    mkdir -p /path/to/artifacts-folder
    chown www-data:www-data /path/to/upload
    chown www-data:www-data /path/to/artifacts-folder

## Create Flask configuration file ##

Create a file `config.py` in `/var/www/sparts` and place the following in it:

    DEBUG = False
    UPLOAD_FOLDER = "/your/path/to/upload/folder"
    ARTIFACT_FOLDER = "/your/path/to/artifacts/folder"
    SAMPLE_DATA_FOLDER = "/var/www/sparts/sample-data"
    DATABASE_URI = "postgresql://<username>:<password>@localhost:5432/sparts"
    BLOCKCHAIN_API = "http://147.11.176.31:3075/api/sparts"
    DEFAULT_API_TIMEOUT = 20
    BYPASS_API_CALSS = False

`BLOCKCHAIN_API` is the hard-coded address of the conductor service.
`DEFAULT_API_TIMEOUT` is the number of seconds to wait for a response in an API call
`BYPASS_API_CALSS` is a flag to bypass making API calls for debugging purposes

## Restart apache server ##

    service apache2 restart

## Populate the database with sample data (optional) ##

Visit this url with any browser `http://localhost/api/sparts/reset`. It should return the following

    {
      "status": "success"
    }
