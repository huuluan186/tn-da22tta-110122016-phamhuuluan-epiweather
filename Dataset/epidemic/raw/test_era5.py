import cdsapi

client = cdsapi.Client()

dataset = 'reanalysis-era5-single-levels'
request = {
    'product_type': ['reanalysis'],
    'variable': [
        '2m_temperature',
        'total_precipitation',
        '2m_dewpoint_temperature',
    ],
    'year': ['2020'],
    'month': ['01'],
    'day': ['01', '02', '03', '04', '05', '06', '07'],
    'time': ['12:00'],
    'data_format': 'netcdf',
    'grid': [1.0, 1.0],
}
target = 'era5_test.nc'

client.retrieve(dataset, request, target)
print("Tải xong!")

import xarray as xr

ds = xr.open_dataset("era5_test.nc")

print(ds)