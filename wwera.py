"""
Python script world era land
261116 : ver. 1.0
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
drv = "c:/"
pth = "data/wwera"

if str(sys.platform).strip() != "win32":
    drv = "/"

fld = drv + "data/wwera/"

dataset = "reanalysis-era5-land-timeseries"

request = {
    "variable": [
        "2m_temperature",
        "total_precipitation",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_pressure",
    ],
    "location": {"latitude": 1, "longitude": 1},
    "date": ["1950-01-01/2030-12-31"],
    "data_format": "csv",
}
client = cdsapi.Client(progress=False, quiet=True, delete=True)

sql = f"""
SELECT DISTINCT 
    cc 
FROM 
    '{fld}1e3nom.parquet' 
"""

for row in duckdb.execute(sql).fetchall():
    upd = p = fld + row[0]
    p = Path(upd + "/t2m")
    p.mkdir(parents=True, exist_ok=True)
    p = Path(upd + "/tp")
    p.mkdir(parents=True, exist_ok=True)
    p = Path(upd + "/w")
    p.mkdir(parents=True, exist_ok=True)

upd = p = drv + "tmp/wwera"
p = Path(upd)
p.mkdir(parents=True, exist_ok=True)


# pick the cc / ccs
sql = f"""
SELECT DISTINCT 
    hcz, cc 
FROM 
    '{fld}1e3nom.parquet' 
WHERE 
    cc in  ('lu','dk')  
ORDER BY
    cc, hcz
"""

for row in duckdb.execute(sql).fetchall():

    hcz = row[0]
    lnd = row[1]

    lc = c.Location(hcz)
    lc = c.Location(lc.get_tt()[0], lc.get_tt()[1])

    sa = str(round(lc.get_lat(), 2))
    so = str(round(lc.get_lon(), 2))

    target = f"{upd}/{hcz}.zip"

    print(
        datetime.now().strftime("%H:%M:%S"),
        " done ",
        " : ",
        lnd,
        t,
    )
    t = t + 1

    request["location"]["latitude"] = sa
    request["location"]["longitude"] = so
    try:
        client.retrieve(dataset, request, target)
    except Exception as e:
        print("❌ retrieve", e)
        continue

    ph = f"{hcz}"

    with zipfile.ZipFile(target, "r") as zip_ref:
        for file_info in zip_ref.infolist():

            fn = os.path.basename(file_info.filename)

            nn = f"{lnd}/{ph}"

            nt = f"{ph}{fn}"
            file_info.filename = nt

            zip_ref.extract(file_info, path=upd)

            srt = ", ((min(t2m)*10)-2731.5)::int16 tn, ((avg(t2m)*10)-2731.5)::int16 tg, ((max(t2m)*10)-2731.5)::int16 tx"
            tp = "t2m"

            if nt.find("precipitation") > 0:
                srt = ", avg((sp/10))::uint16 sp, abs(sum(tp*10000))::uint16 tp"
                tp = "tp"

            if nt.find("sfc-wind") > 0:
                srt = ", min(u10*10)::int16 un, min(v10*10)::int16 vn,avg(u10*10)::int16 ug, avg(v10*10)::int16 vg, max(u10*10)::int16 ux, max(v10*10)::int16 vx"
                tp = "w"

            nn = f"{lnd}/{tp}/{ph}"
            if tp == "w":
                tp = "u10"

            ds = f"""
                COPY (
                select 
                cast(strftime(valid_time, '%Y%m%d') AS UINT32)  d
                {srt},
                {hcz}::int64 hcz 
                from '{upd}/{nt}' 
                where {tp} is not null
                group by d
                order by d
                ) TO '{fld}/{nn}.parquet' (COMPRESSION 'zstd')
                """

            try:
                duckdb.execute(ds)
            except Exception as e:
                print(f"❌ {hcz} no data from era ")

            Path(f"{upd}/{nt}").unlink(missing_ok=True)

    Path(f"{target}").unlink(missing_ok=True)

print("All done.")
