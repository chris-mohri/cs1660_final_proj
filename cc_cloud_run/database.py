from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, LargeBinary, DateTime
import sqlalchemy
import datetime
from google.cloud.sql.connector import Connector, IPTypes

Base = declarative_base()

class QRCode(Base):
    __tablename__ = 'qrcodes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    qrcode = Column(LargeBinary, nullable=False)
    date = Column(DateTime, default=datetime.datetime.utcnow)


def get_engine():
    connector = Connector()
    INSTANCE_CONNECTION_NAME = "cs1660-cjm235:us-central1:qr-codes"

    def getconn():
        return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user="postgres",
        password="cjm235",
        db="qr-codes",
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