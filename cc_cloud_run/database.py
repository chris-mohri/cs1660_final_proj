from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, LargeBinary, DateTime
import sqlalchemy
import datetime
from google.cloud.sql.connector import Connector, IPTypes

Base = declarative_base()

# Define the QRCode model
# Documentation to connect cloud run https://cloud.google.com/sql/docs/postgres/connect-run#python
class QRCode(Base):
    __tablename__ = 'qrcodes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    qrcode = Column(LargeBinary, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)


def get_engine():
    connector = Connector()
    INSTANCE_CONNECTION_NAME = "strawhattendance:us-central1:screenshot-db"
    # Replace with your actual project ID, region, and instance name
    USER="postgres"
    PASSWORD=")hY=D|?^S|aqmLPp"
    DB="qr-codes"


    def getconn():
        return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=USER,
        password=PASSWORD,
        db=DB,
        ip_type= IPTypes.PUBLIC,
    )
    

    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        pool_size=5,
        max_overflow=2,
        pool_timeout=30,
        pool_recycle=1800,
    )

    return engine
