import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, shape


import folium
import folium.plugins
from folium.plugins import Draw
import requests
import json



def main():

    #initalize map titles
    min_lon, max_lon = 17.70891393315022, 18.536390448353895 #gotta increase these 
    min_lat, max_lat = 59.216339768502074, 59.4527626869623

    m = folium.Map(location=(59.330179255373515, 18.057957648090127),
        tiles="cartodb positron",
        max_bounds=True,
        zoom_start = 11,
        min_zoom=10,
        max_zoom=20,
        control_scale=True,
        # min_lat=min_lat,
        # max_lat=max_lat,
        # min_lon=min_lon,
        # max_lon=max_lon,
    )
    cartonDB = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
    folium.TileLayer(
        max_bounds=True,
        tiles= cartonDB,
	    attr= '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
	    name = 'cartonDB',
        subdomains= 'abcd',
        zoom_start = 11,
        min_zoom=10,
        max_zoom=20,
        # min_lat=min_lat,
        # max_lat=max_lat,
        # min_lon=min_lon,
        # max_lon=max_lon,
    ).add_to(m)


    #All Other map features

    # playableArea(m)
    municipalities(m)
    districts(m)
    train(m)
    M_lines(m)
    T_lines(m)
    stations(m)

    amusementParks(m)


    radar(m)
    
    

    #Add location request
    #folium.plugins.LocateControl(auto_start=False).add_to(m)

    #Add layer control
    folium.LayerControl().add_to(m)

    #Add draw function
    Draw(export=False).add_to(m)

    #Add lat, lon popup
    m.add_child(
        folium.ClickForLatLng(format_str='lat + "," + lng ', alert=True)
    )


    #map generation
    print("sucessfully generated map.")
    file_name = r'E:\TUE\Projects\Jet-Lag-Stockholm\Stockholm'
    m.save(file_name + '.html')

    #Function to plop the cities

# def playableArea(m):
#     range = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\45min.geojson")

#     folium.GeoJson(
#         range,
#         name = "45min distance",
#             style_function=lambda x: {
#             'fillColor': 'green',
#             'color': 'black',
#             'weight': 3
#         },
#         show = True
#     ).add_to(m)


def municipalities(m):
    
    #read Stockholm json data
    raw_municialities = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\sweden-municipalities2.geojson")

    #clean up data
    cleaned_data = []
    cleaned_data = raw_municialities[['name', 'geometry']]

    #build a GeoDataFrame with the cleaned data
    global game_area
    game_area = gpd.GeoDataFrame(cleaned_data, crs="EPSG:4326")

    #Create a mask, which plots world_borer - game_area,
    world_border = [[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]
    world_poly = Polygon(world_border)
    world_gdf = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[world_poly])
    mask_gdf = gpd.overlay(world_gdf, game_area, how='difference')
    
    #Add the masked layers to the map
    folium.GeoJson(
        mask_gdf,
        name="Out of Bounds",
        control=False
    ).add_to(m)
    

    #Add boundaries of municipalities to the map
    folium.GeoJson(
        game_area,
        name= "Municipalities",
        style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 3
        },
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            aliases=['Municipality:']
        ),
        show = True,
        control=False
    ).add_to(m)

def districts(m):
    districts = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\stockholm-districts.geojson")

    folium.GeoJson(
        districts,
        name = "Districts",
            style_function=lambda x: {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 2
        },
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            aliases=['Districts:'],
        ),
        show = True
    ).add_to(m)

def train(m):

    train_lines = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\train.geojson")

    #reduce length of tram line names 
    train_lines['name'] = train_lines['name'].str.split(':').str[0].str.strip()

    #plot train lines
    folium.GeoJson(
        train_lines,
        name = "Train lines",
            style_function=lambda feature: {
                'color':"#6E6E6E",
                'opacity': 0.8,
                'dashArray': '10, 10'
        },
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            labels = False
        ),
        show = True,
        control=False
    ).add_to(m)

def M_lines(m):
    metro_lines = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\metro-lines.geojson")

    #reduce length of metro line names
    metro_lines['name'] = metro_lines['name'].str[:13]

    #plot metro lines
    folium.GeoJson(
        metro_lines,
        name = "Metro Lines",
            style_function=lambda feature: {
                'color': feature['properties'].get('colour', '#555555'),
                'width': 1
        },
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            labels = False
        ),
        show = True
    ).add_to(m)

def T_lines(m):
    raw_TLines = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\tram-lines.geojson")
    tram_lines = raw_TLines[['name','geometry','colour']]

    #reduce length of tram line names 
    tram_lines['name'] = tram_lines['name'].str.split(':').str[0].str.strip()

    #plot tram lines
    folium.GeoJson(
        tram_lines,
        name = "Tram Lines",
        style_function=lambda feature: {
            'color': feature['properties'].get('colour', '#555555'),
            'width': 1
        },
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            labels = False
        ),
        show = True
    ).add_to(m)

def stations(m):
    #read data from GeoJson
    raw_Tstations = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\tram-stations.geojson")
    raw_Mstations = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\metro-stations.geojson")

    #extract name and geometry of unique tram stations 
    tram_stations = raw_Tstations[['name','geometry']].drop_duplicates(subset=['name'])
    #only select stations within the game area
    tram_stations = gpd.clip(tram_stations, game_area)
    #select starting tram stations of the game
    start_T = tram_stations[tram_stations['name'] == "T-Centralen"][['name','geometry']]
    #remove starting tram stations from other tram stations
    tram_stations = tram_stations[~tram_stations['name'].isin(start_T['name'])]

    #extract name and geometry of unique metro stations 
    metro_stations = raw_Mstations[['name','geometry']].drop_duplicates(subset=['name'])
    #only select stations within the game area
    metro_stations = gpd.clip(metro_stations, game_area)
    #select starting metro stations of the game
    start_M = metro_stations[metro_stations['name'] == "T-Centralen"][['name','geometry']]
    #remove starting tram stations from other tram stations
    metro_stations = metro_stations[~metro_stations['name'].isin(start_M['name'])]

    #plot starting points
    start = pd.concat([start_M,start_T])
    folium.GeoJson(
        start,
        name = "Starting Point",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='black',
                icon='flag-checkered', 
                prefix='fa')
        ),
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            labels=False
        ),
        show = True
    ).add_to(m)

    
    #plot stations with metro
    folium.GeoJson(
        metro_stations,
        name = "Metro Stations",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='darkblue',
                icon='train-subway', 
                prefix='fa')
        ),
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            labels=False
        ),
        show = False
    ).add_to(m)

    #plot stations with tram
    folium.GeoJson(
        tram_stations,
        name = "Tram Stations",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='red',
                icon='train-tram', 
                prefix='fa')
        ),
        tooltip=folium.GeoJsonTooltip(
            fields = ['name'],
            labels=False
        ),
        show = False
    ).add_to(m)
    
    # plop hiding zones
    all_station = pd.concat([metro_stations,tram_stations,start])
    hiding_zone = folium.FeatureGroup(name="Hiding Zone", show=False)

    for idx, row in all_station.iterrows():
        hidingZones(hiding_zone,250,row.geometry.y,row.geometry.x)

    hiding_zone.add_to(m)

def hidingZones(group,radius,lat,long):
    folium.Circle(
        location=[lat, long],
        radius=radius,
        color = '#5F5F5F',
        weight=0.5,
        fill_color = '#5F5F5F',
        fill_opacity=0.3,
        show=False,
    ).add_to(group)

def amusementParks(m):
    amusementParks = gpd.read_file(r"E:\TUE\Projects\Jet-Lag-Stockholm\Amusement-Park.geojson")
    amusementParks['label'] = amusementParks['label'].str.split('-').str[0].str.strip()

    folium.GeoJson(
        amusementParks,
        name = "Amusement Parks",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='pink',
                icon='ticket', 
                prefix='fa')
        ),
        popup=folium.GeoJsonPopup(
            fields = ['label'],
            labels=False
        ),
        show = False
    ).add_to(m)

# Tools
def radar(m):
    #GPS function for radars
    folium.plugins.LocateControl(
        position="topleft",
        drawCircle=True,
        flyTo=True,
        metric=True,
    ).add_to(m)

    with open(r"E:\TUE\Projects\Jet-Lag-Stockholm\radar-panel.html", "r", encoding="utf-8") as f:
        radar_panel_html = f.read()
        
    m.get_root().html.add_child(folium.Element(radar_panel_html))



if __name__ == "__main__":
    main()
