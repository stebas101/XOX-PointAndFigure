from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aasdfr3434' # Generate new key using secrets

from xox_pnf import routes