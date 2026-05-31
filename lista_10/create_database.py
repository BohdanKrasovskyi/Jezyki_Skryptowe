import sys

from sqlalchemy import create_engine, Integer, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Stations(Base):
    __tablename__ = 'stations'

    station_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    rentals_started: Mapped[list["Rentals"]] = relationship(
        "Rentals", foreign_keys="Rentals.rental_station_id", back_populates="rental_station"
    )

    rentals_ended: Mapped[list["Rentals"]] = relationship(
        "Rentals", foreign_keys="Rentals.return_station_id", back_populates="return_station"
    )

class Rentals(Base):
    __tablename__ = 'rentals'

    rental_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bike_number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[str] = mapped_column(Text, nullable=False)
    end_time: Mapped[str] = mapped_column(Text, nullable=False)
    rental_station_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stations.station_id", ondelete="SET NULL"), nullable=True
    )
    return_station_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("stations.station_id", ondelete="SET NULL"), nullable=True
    )
    duration: Mapped[int] = mapped_column(Integer, nullable=False)

    rental_station: Mapped["Stations"] = relationship(
        "Stations", foreign_keys=[rental_station_id], back_populates="rentals_started"
    )
    return_station: Mapped["Stations"] = relationship(
        "Stations", foreign_keys=[return_station_id], back_populates="rentals_ended"
    )


def main():
    if len(sys.argv) < 2:
        print("Błąd: Nie podano nazwy bazy danych!")
        print("Użycie: python create_database.py <nazwa_bazy>")
        sys.exit(1)

    db_name = sys.argv[1]
    db_filename = f"{db_name}.sqlite3"

    engine = create_engine(f"sqlite:///{db_filename}", echo=True)

    Base.metadata.create_all(engine)

    print(f"\nBaza {db_name} utworzona pomyślnie")

if __name__ == "__main__":
    main()

