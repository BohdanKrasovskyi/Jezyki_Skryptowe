from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class Station(Base):
    __tablename__ = 'stations'

    station_id = Column(Integer, primary_key=True, autoincrement=True)
    station_name = Column(String(50), nullable=False)

    def __repr__(self):
        return f"<Station(station_id={self.id}, station_name='{self.name}')>"

try:
    engine = create_engine('sqlite:///lista10.db', echo=True)

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    new_station = Station(station_id=1, station_name="Amsterdam M1")
    session.add(new_station)
    session.commit()

    print("Table created and sample data inserted successfully.")

except SQLAlchemyError as e:
    print(f"Database error: {e}")
