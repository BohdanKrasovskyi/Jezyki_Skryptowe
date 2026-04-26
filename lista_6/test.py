import datetime
import pandas
import Station
import TimeSeries

# station1 = Station.Station("DsBiakla", "Bialka", "ul.Chopina 35", "tlo", date_of_start=datetime.date(2020, 1, 1), date_of_end=datetime.date(2020, 5, 2))
# station2 = Station.Station("DsBiakla", "Bialka", "ul.Chopina 35", "tlo", date_of_start=datetime.date(2020, 1, 1), date_of_end=datetime.date(2020, 5, 2))
# station3 = Station.Station("DsCzar", "Bialka", "ul.Chopina 35", "tlo", date_of_start=datetime.date(2020, 1, 1), date_of_end=datetime.date(2020, 5, 2))
# print(str(station1))
# print(station1.__repr__())
# print(station1 == station2)
# print(station1 == station3)
# print(station1 == 1)

list_of_dates = list(pandas.date_range(datetime.date(2020, 1, 1), datetime.date(2020, 1, 5)))
measurement = [x/10 for x in range(0, len(list_of_dates))]
time_series = TimeSeries.TimeSeries(name_of_indicator="PM10", code_of_station="DsBialka", averaging_time=5, list_of_dates=list_of_dates, measurement=measurement, unit_of_measurement="PM")
print(time_series.range)
print(time_series.median)