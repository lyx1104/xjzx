from app import create_app
from config import DevelopConfig
from models import db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = create_app(DevelopConfig)

if __name__ == '__main__':
    manager = Manager(app)
    migrate = Migrate(app, db)
    manager.add_command('db', MigrateCommand)
    manager.run()
