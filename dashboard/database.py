import os
from flask_sqlalchemy import SQLAlchemy
from config import logger

# Initialize SQLAlchemy with no settings
db = SQLAlchemy()

class MacroHealth(db.Model):
    __tablename__ = 'macro_health'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    vix = db.Column(db.Float)
    dxy = db.Column(db.Float)
    treasury_10y = db.Column(db.Float)
    regime = db.Column(db.String(50))

class InstitutionalKPIs(db.Model):
    __tablename__ = 'institutional_kpis'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    
class BillingRecord(db.Model):
    __tablename__ = 'billing_records'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='PENDING')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

def init_database(app):
    """
    Initializes the local SQLite database for billing and macro snapshots.
    NOTE: Core prediction_ledger and observation_memory remain in Aiven PostgreSQL.
    """
    # Ensure billing directory exists
    billing_dir = os.path.join(os.getcwd(), 'billing')
    os.makedirs(billing_dir, exist_ok=True)
    
    # Configure SQLite Database URI
    db_path = os.path.join(billing_dir, 'billing.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
            logger.info(f"Successfully initialized local SQLite DB at {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite DB: {e}")
