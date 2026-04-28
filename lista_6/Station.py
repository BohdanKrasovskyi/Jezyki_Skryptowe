import datetime

class Station:
    def __init__(self, code : str, name_of_station : str,
                 address : str, type_of_station : str, date_of_start : datetime.date,
                 date_of_end : datetime.date) -> None:
        self.code = code
        self.name_of_station = name_of_station
        self.address = address
        self.type_of_station = type_of_station
        self.date_of_start = date_of_start
        self.date_of_end = date_of_end

    def __str__(self) -> str:
        return f'Kod stacji: {self.code} , Nazwa:  {self.name_of_station}, Adress :  {self.address}, Typ stacji : {self.type_of_station}, Data rozpoczencia : {self.date_of_start}, Data zakonczenia : {self.date_of_end}'

    def __repr__(self) -> str:
        return f'Station({str(self)})'

    def __eq__(self, other) -> bool:
        if isinstance(other, Station):
            return self.code == other.code
        else:
            return False

