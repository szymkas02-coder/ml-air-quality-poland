import pandas as pd
import numpy as np
import xarray as xr
import glob
import os
import re

def read_data(name = "PM10_24g"):
    #name = "*" + name + ".xlsx"
    root_folder = "./"
    #plik_lista = glob.glob(os.path.join(root_folder, "*", name))
    pattern = os.path.join(root_folder, "[0-9][0-9][0-9][0-9]", f"[0-9][0-9][0-9][0-9]_{name}.xlsx")
    plik_lista = glob.glob(pattern)
    # Opcjonalnie: filtracja przez regex, dla pewności
    #file_list = [f for f in file_list if re.search(r"/\d{4}/\d{4}_" + re.escape(name) + r"\.xlsx$", f)]

    df_list = []

    for sciezka in plik_lista:
        try:
            print(f"Wczytywanie: {sciezka}")

            # Wyciąganie roku z nazwy pliku lub folderu
            dopasowanie = re.search(r'(\d{4})', sciezka)
            if dopasowanie:
                rok = int(dopasowanie.group(1))
            else:
                print(f"Nie można rozpoznać roku z: {sciezka}")
                continue

            # Konfiguracja skiprows
            if rok <= 2015:
                skiprows = 0  # Nagłówek to 1. wiersz
            else:
                skiprows = 1  # Nagłówek to 2. wiersz

            # Wczytanie pliku
            df = pd.read_excel(sciezka, skiprows=skiprows, header=0, decimal=",")

            # Usunięcie niepotrzebnych wierszy z danymi po nagłówku
            if rok <= 2015:
                df = df.drop(index=[0,1], errors="ignore")  # Usuwa 2. i 3. wiersz
            else:
                df = df.drop(index=[0,1,2,3], errors="ignore")  # Usuwa 2–5. wiersz

            # Przetwarzanie kolumny z datą
            df.rename(columns={df.columns[0]: "Data"}, inplace=True)
            df["Data"] = pd.to_datetime(df["Data"], errors='coerce')
            df.set_index("Data", inplace=True)

            df_list.append(df)

        except Exception as e:
            print(f"Błąd w pliku {sciezka}: {e}")

    # Łączenie danych
    df_all = pd.concat(df_list, axis=0).sort_index()
    # 1. Zamień przecinki na kropki, usuń spacje i inne znaki, a potem konwertuj
    #def clean_column(series):
    #    s = series.astype(str).str.strip()
    #    s = s.str.replace(',', '.', regex=False)
    #    s = s.replace(r'[^0-9\.\-]', '', regex=True)
    #    return pd.to_numeric(s, errors='coerce')
    df_all = df_all.apply(pd.to_numeric, errors='coerce')
    # 2. Zastosuj do całego DataFrame
    #df_all = df_all.apply(clean_column)
    #df_all = df_all.resample('D').mean()

    df_meta = pd.read_excel("./meta.xlsx", decimal=",")
    df_meta.set_index("Nr", inplace = True, drop = True)
    df_meta.columns = df_meta.columns.str.strip().str.lower().str.replace(r'\s+', '_', regex=True)
    df_meta = df_meta.rename(columns={'stary_kod_stacji_(o_ile_inny_od_aktualnego)': 'stary_kod'})
    df_meta = df_meta.rename(columns={
    'wgs84_φ_n': 'lat',
    'wgs84_λ_e': 'lon'
    })

    alias_map = {}

    for _, row in df_meta.iterrows():
        kod = row['kod_stacji']

        # Dodaj główny kod stacji jako alias samego siebie
        if pd.notna(kod):
            alias_map[kod] = kod

        # Rozbij stary_kod jeśli istnieje
        if pd.notna(row['stary_kod']):
            for alias in str(row['stary_kod']).split(','):
                alias = alias.strip()
                if alias:
                    alias_map[alias] = kod

    df_renamed = df_all.copy()

    # Przypisz nowe nazwy kolumn zgodnie z alias_map
    new_columns = {
        col: alias_map.get(col, col) for col in df_renamed.columns
    }

    df_renamed = df_renamed.rename(columns=new_columns)
    print(df_renamed)

    # Agregacja: np. średnia, ale możesz też użyć np. .first(), .max()
    df_merged = df_renamed.T.groupby(level=0).mean(numeric_only=True).T
    print(df_merged)

    df_avg = df_merged.mean().reset_index()
    df_avg.columns = ['kod_stacji', 'srednia']

    df_avg = df_avg.merge(df_meta, on='kod_stacji', how='left')
    missing_coords = df_avg[df_avg[['lat', 'lon']].isna().any(axis=1)]
    print("⚠️ Stacje bez współrzędnych:")
    print(missing_coords[['kod_stacji']])
    df_avg = df_avg.dropna(subset=['lat', 'lon'])

    return df_merged, df_avg
