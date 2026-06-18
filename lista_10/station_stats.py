import sys
import tkinter as tk
from tkinter import ttk
from sqlalchemy import create_engine, select, func, distinct
from sqlalchemy.orm import sessionmaker
from create_database import Stations, Rentals


class StationStatsApp:
    def __init__(self, root, db_name):
        self.root = root
        self.root.title("Statystyki Stacji WRM")
        self.root.geometry("950x620")
        self.root.resizable(True, True)

        db_filename = f"{db_name}.sqlite3"
        try:
            engine = create_engine(f"sqlite:///{db_filename}")
            Session = sessionmaker(bind=engine)
            self.session = Session()
        except:
            raise Exception(f"Error connecting to {db_filename}")

        self._build_ui()
        self._load_stations()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root, padding=10)
        left.grid(row=0, column=0, sticky="ns")

        ttk.Label(left, text="Wybierz stację:", font=("Arial", 11, "bold")).pack(anchor="w")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_stations)
        ttk.Entry(left, textvariable=self.search_var, width=32).pack(pady=(4, 6))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            list_frame, yscrollcommand=scrollbar.set, width=34, height=28,
            selectmode=tk.SINGLE, font=("Arial", 10)
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self._on_station_select)

        #Right panel
        right = ttk.Frame(self.root, padding=10)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        ttk.Label(right, text="Statystyki stacji", font=("Arial", 13, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        txt_frame = ttk.Frame(right)
        txt_frame.grid(row=1, column=0, sticky="nsew")
        txt_frame.columnconfigure(0, weight=1)
        txt_frame.rowconfigure(0, weight=1)

        txt_scroll = ttk.Scrollbar(txt_frame)
        txt_scroll.grid(row=0, column=1, sticky="ns")

        self.stats_text = tk.Text(
            txt_frame, state=tk.DISABLED, wrap=tk.WORD,
            font=("Consolas", 11), yscrollcommand=txt_scroll.set,
            padx=8, pady=8
        )
        self.stats_text.grid(row=0, column=0, sticky="nsew")
        txt_scroll.config(command=self.stats_text.yview)

        self._write_stats("Wybierz stację z listy, aby zobaczyć statystyki.")



    def _load_stations(self):
        self.all_stations = self.session.scalars(
            select(Stations).order_by(Stations.station_name)
        ).all()
        self._repopulate(self.all_stations)

    def _repopulate(self, stations):
        self.listbox.delete(0, tk.END)
        for s in stations:
            self.listbox.insert(tk.END, s.station_name)
        self._station_map = {s.station_name: s for s in stations}

    def _filter_stations(self, *_):
        q = self.search_var.get().lower()
        filtered = [s for s in self.all_stations if q in s.station_name.lower()]
        self._repopulate(filtered)

    def _on_station_select(self, _event):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        station = self._station_map.get(name)
        if station:
            self._show_stats(station)


    def _show_stats(self, station: Stations):
        sid = station.station_id

        # a) Średni czas przejazdu rozpoczynanego na tej stacji
        avg_start = self.session.scalar(
            select(func.avg(Rentals.duration))
            .where(Rentals.rental_station_id == sid)
        )

        # b) Średni czas przejazdu kończonego na tej stacji
        avg_end = self.session.scalar(
            select(func.avg(Rentals.duration))
            .where(Rentals.return_station_id == sid)
        )

        # c) Liczba różnych rowerów parkowanych na tej stacji
        unique_bikes = self.session.scalar(
            select(func.count(distinct(Rentals.bike_number)))
            .where(
                (Rentals.rental_station_id == sid) |
                (Rentals.return_station_id == sid)
            )
        )

        # d) Top 5 najczęstszych stacji docelowych z tej stacji
        top_dest = self.session.execute(
            select(
                Stations.station_name,
                func.count(Rentals.rental_id).label("trips")
            )
            .join(Rentals, Rentals.return_station_id == Stations.station_id)
            .where(Rentals.rental_station_id == sid)
            .group_by(Stations.station_id)
            .order_by(func.count(Rentals.rental_id).desc())
            .limit(5)
        ).all()

        lines = [
            f"Stacja: {station.station_name}",
            "=" * 55,
            "",
            "a) Średni czas przejazdu ROZPOCZĘTEGO na tej stacji:",
            f"   {avg_start:.1f} min" if avg_start is not None else "   Brak danych",
            "",
            "b) Średni czas przejazdu ZAKOŃCZONEGO na tej stacji:",
            f"   {avg_end:.1f} min" if avg_end is not None else "   Brak danych",
            "",
            "c) Liczba różnych rowerów parkowanych na tej stacji:",
            f"   {unique_bikes}",
            "",
            "d) Top 5 najczęstszych stacji docelowych z tej stacji:",
        ]

        if top_dest:
            for rank, (dest_name, count) in enumerate(top_dest, 1):
                lines.append(f"   {rank}. {dest_name}  ({count} przejazdów)")
        else:
            lines.append("   Brak danych")

        self._write_stats("\n".join(lines))

    def _on_close(self):
        self.session.close()
        self.root.destroy()

    def _write_stats(self, text: str):
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", text)
        self.stats_text.config(state=tk.DISABLED)


def main():
    if len(sys.argv) < 2:
        print("Użycie: python station_stats.py <nazwa_bazy>")
        print("Przykład: python station_stats.py rentals")
        sys.exit(1)

    db_name = sys.argv[1]
    root = tk.Tk()
    StationStatsApp(root, db_name)
    root.mainloop()


if __name__ == "__main__":
    main()