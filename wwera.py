"""
Python script world era land, average / day
261116 : ver. 1.0
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=download
demo , grid and pythonscript : http://212.227.167.148/
"""

import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import c.cls as c

from datetime import datetime
from pathlib import Path
import cdsapi
import zipfile
import duckdb

t = 0
drv = "/"
if sys.platform.strip() == "win32":
    drv = "c:/"

fld = drv + "data/wwera/"

dataset = "reanalysis-era5-land-timeseries"

request = {
    "variable": [
        "2m_temperature",
        "total_precipitation",
        "surface_pressure",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
    ],
    "location": {"latitude": 1, "longitude": 1},
    "date": ["1950-01-01/2030-12-31"],
    "data_format": "csv",
}
client = cdsapi.Client(progress=False, quiet=True, delete=True)

pt = Path(drv + "data/wwera/tmp")
pt.mkdir(parents=True, exist_ok=True)

# pick the cc / ccs with WHERE
sql = f"""
SELECT DISTINCT 
    hcz, cc 
FROM 
    '{fld}1e3nom.parquet' 
WHERE    cc >  'ag'
ORDER BY
    cc, hcz
"""
no = len(duckdb.execute(sql).fetchall())

for row in duckdb.execute(sql).fetchall():

    hcz = row[0]
    lnd = row[1]

    l = ["/t2m", "/tp", "/w"]
    for z in l:
        Path(fld + lnd + z).mkdir(parents=True, exist_ok=True)

    target = f"{pt}/{hcz}.zip"

    print(datetime.now().strftime("%H:%M:%S"), " done :", t, " of", no, " cc :", lnd)
    t = t + 1

    lc = c.Location(hcz)
    lc = c.Location(lc.get_tt()[0], lc.get_tt()[1])

    request["location"]["latitude"] = round(lc.get_lat(), 2)
    request["location"]["longitude"] = round(lc.get_lon(), 2)

    try:
        client.retrieve(dataset, request, target)
    except Exception as e:
        print("❌ retrieve", e)
        continue

    with zipfile.ZipFile(target, "r") as zr:
        for fi in zr.infolist():

            fn = os.path.basename(fi.filename)

            zr.extract(fi, path=pt)

            srt = ", ((min(t2m)*10)-2731.5)::int16 tn, ((avg(t2m)*10)-2731.5)::int16 tg, ((max(t2m)*10)-2731.5)::int16 tx"
            tp = "t2m"

            if fn.find("precipitation") > 0:
                srt = ", avg((sp/10))::uint16 sp, abs(sum(tp*10000))::uint16 tp"
                tp = "tp"

            if fn.find("sfc-wind") > 0:
                srt = ", min(u10*10)::int16 un, min(v10*10)::int16 vn,avg(u10*10)::int16 ug, avg(v10*10)::int16 vg, max(u10*10)::int16 ux, max(v10*10)::int16 vx"
                tp = "w"

            nn = f"{lnd}/{tp}/{hcz}"

            if tp == "w":
                tp = "u10"

            ds = f"""
                COPY 
                (
                select 
                cast(strftime(valid_time, '%Y%m%d') AS UINT32)  d
                {srt} ,
                {hcz}::int64 hcz 
                from '{pt}/{fn}' 
                where {tp} is not null
                group by d order by d
                ) 
                TO '{fld}/{nn}.parquet' (COMPRESSION 'zstd')
                """

            try:
                duckdb.execute(ds)
            except Exception as e:
                print(f"❌ {hcz} no data from era {tp}")

            Path(f"{pt}/{fn}").unlink(missing_ok=True)

    Path(target).unlink(missing_ok=True)

print("All done.")
