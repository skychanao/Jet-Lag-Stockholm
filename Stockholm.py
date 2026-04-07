import streamlit as st
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation 

import warnings
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, shape, Point


import folium
import folium.plugins
from folium.plugins import Draw
import requests
import json



def main():

    #ignore warnings
    warnings.filterwarnings("ignore")

    #OS stuff
    os.environ['CPL_LOG'] = 'NUL'
    os.environ['CPL_LOG_ERRORS'] = 'OFF'    

    #read local file path
    global script_folder
    script_folder = Path(__file__).parent
    
    #Setup Streamlit
    st.set_page_config(page_title="Stockholm Map", layout="wide")
    st.markdown(
        """
        <style>
        /* Prevent Streamlit from making elements stale/gray during reruns */
        div[data-testid="stElementContainer"], iframe {
            opacity: 1 !important;
            transition: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    #Streamlit Features
    streamlit_features()

    #initalize map titles
    min_lon, max_lon = 17.70891393315022, 18.536390448353895 #gotta increase these 
    min_lat, max_lat = 59.216339768502074, 59.4527626869623

    m = folium.Map(location=(59.330179255373515, 18.057957648090127),
        tiles="OpenStreetMap",
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

    #Base Map features
    # playableArea(m)
    municipalities(m)
    districts(m)
    train(m)
    M_lines(m)
    T_lines(m)
    stations(m)

    #Point of Interest for Seeking
    amusementParks(m)
    zoo(m)
    aquarium(m)
    golf(m)

    #Seeking Tooks
    draw_radar(m)
    
    

    #Add location request
    folium.plugins.LocateControl(auto_start=False).add_to(m)

    #Add layer control
    folium.LayerControl().add_to(m)

    #Add draw function
    Draw(export=False).add_to(m)

    #Add lat, lon popup
    # m.add_child(
    #     folium.ClickForLatLng(format_str='lat + "," + lng ', alert=True)
    # )


    #map generation
    # print("sucessfully generated map.")
    # file_name = script_folder / "Stockholm.html"
    # m.save(file_name)

    st_folium(m,
        use_container_width=True,
        height=900
    )


    #Functions to plop the cities features

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

def streamlit_features():

    if "radars" not in st.session_state:
        st.session_state.radars = []

    # read user input
    with st.sidebar:
        st.header("Radar")
        
        location = streamlit_geolocation()

        def copy_to_text_box():
            if location['latitude'] is not None and location['longitude'] is not None:
                #Format Number
                st.session_state.coord_input = f"{location['latitude']}, {location['longitude']}"
            else:
                st.warning("Still searching for GPS...")
        
        st.button("Autofill Coordinates", on_click=copy_to_text_box, use_container_width=True)

        coordinate = st.text_input(label = "Coordinate", placeholder = "lat, lon",key="coord_input")

        radius = st.number_input(label = "Radius", placeholder = "x (km)", step=0.5, min_value=0.0)
        radar_type = st.radio("Radar Type", ["Hit", "Miss"])



    #read coordinate
    if "," in coordinate:
        parts = coordinate.split(',')
        
        try:
            latitude = float(parts[0].strip())
            longitude = float(parts[1].strip())
            
        except ValueError:
            st.sidebar.error("Error: Please only type numbers.")

    if st.sidebar.button("Plot Radar", use_container_width=True):
        st.session_state.radars.append({
                "lat": latitude,
                "lon": longitude,
                "size": radius,
                "type": radar_type
            })

    if st.sidebar.button("Undo Radar", use_container_width=True):
        if st.session_state.radars:
            st.session_state.radars.pop() # Removes the last drawn radar   

def municipalities(m):
    
    #read Stockholm json data
    raw_municialities = gpd.read_file(script_folder / "sweden-municipalities2.geojson")

    #clean up data
    cleaned_data = clean_geometry(raw_municialities[['name', 'geometry']])

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
        style_function=lambda x: {
            'fillColor': '#3388ff',
            'color': '#3388ff',       
            'weight': 3,
            'fillOpacity': 0.4
        },
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
    raw_districts = gpd.read_file(script_folder / "stockholm-districts.geojson")
    districts = clean_geometry(raw_districts)

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
    raw_train_lines = gpd.read_file(script_folder / "train.geojson")
    train_lines = clean_geometry(raw_train_lines)

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
    raw_metro_lines = gpd.read_file(script_folder / "metro-lines.geojson")
    metro_lines = clean_geometry(raw_metro_lines)

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
    raw_TLines = gpd.read_file(script_folder / "tram-lines.geojson")
    tram_lines = clean_geometry(raw_TLines[['name','geometry','colour']])

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
    raw_Tstations = gpd.read_file(script_folder / "tram-stations.geojson")
    raw_Mstations = gpd.read_file(script_folder / "metro-stations.geojson")


    #extract name and geometry of unique tram stations 
    tram_stations = clean_geometry(raw_Tstations[['name','geometry']].drop_duplicates(subset=['name']))
    #only select stations within the game area
    tram_stations = gpd.clip(tram_stations, game_area)
    #select starting tram stations of the game
    start_T = tram_stations[tram_stations['name'] == "T-Centralen"][['name','geometry']]
    #remove starting tram stations from other tram stations
    tram_stations = tram_stations[~tram_stations['name'].isin(start_T['name'])]

    #extract name and geometry of unique metro stations 
    metro_stations = clean_geometry(raw_Mstations[['name','geometry']].drop_duplicates(subset=['name']))
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
    raw_amusementParks = gpd.read_file(script_folder / "Amusement-Park.geojson")
    amusementParks = clean_geometry(raw_amusementParks)
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

def zoo(m):
    raw_zoos = gpd.read_file(script_folder / "zoos.geojson")
    zoos = clean_geometry(raw_zoos)
    zoos['label'] = zoos['label'].str.split(' - ').str[0].str.strip()

    folium.GeoJson(
        zoos,
        name = "Zoos",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='darkred',
                icon='paw', 
                prefix='fa')
        ),
        popup=folium.GeoJsonPopup(
            fields = ['label'],
            labels=False
        ),
        show = False
    ).add_to(m)

def aquarium(m):
    raw_aquariums = gpd.read_file(script_folder / "aquariums.geojson")
    aquariums = clean_geometry(raw_aquariums)
    aquariums['label'] = aquariums['label'].str.split(' - ').str[0].str.strip()

    folium.GeoJson(
        aquariums,
        name = "Aquariums",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='lightblue',
                icon='fish', 
                prefix='fa')
        ),
        popup=folium.GeoJsonPopup(
            fields = ['label'],
            labels=False
        ),
        show = False
    ).add_to(m)

def golf(m):
    raw_golfcourses = gpd.read_file(script_folder / "golf-courses.geojson")
    golf_courses = clean_geometry(raw_golfcourses)
    golf_courses['label'] = golf_courses['label'].str.split(' - ').str[0].str.strip()

    folium.GeoJson(
        golf_courses,
        name = "Golf Courses",
        marker=folium.Marker(
            icon=folium.Icon(
                color ='darkgreen',
                icon='golf-ball', 
                prefix='fa')
        ),
        popup=folium.GeoJsonPopup(
            fields = ['label'],
            labels=False
        ),
        show = False
    ).add_to(m)

#function to drop NULL values
def clean_geometry(gdf):
    #Drop data with no shape data
    gdf = gdf.dropna(subset=['geometry'])
    
    #Keep only the standard shapes that Folium knows how to draw
    supported_shapes = ['Point', 'MultiPoint', 'LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']
    gdf = gdf[gdf.geometry.type.isin(supported_shapes)]
    return gdf

# Tools
def draw_radar(m):

    for r in st.session_state.radars:
    
        #Read Circle data
        center = Point(r["lon"], r["lat"])  
        circle_gdf = gpd.GeoDataFrame(geometry=[center], crs="EPSG:4326")
        circle_meters = circle_gdf.to_crs(epsg=3006) 
        circle_shape = circle_meters.buffer(r["size"] * 1000).to_crs(epsg=4326).geometry.iloc[0]
        inverted_mask = game_area.geometry.unary_all.difference(circle_shape)        
        #If radar is hit, keep only radar circle unfilled
        if r["type"] == "Hit":
            #keep only radar area unfilled
            folium.GeoJson(
                inverted_mask,
                style_function=lambda x: {
                    'fillColor': '#3388ff',
                    'color': '#3388ff',       
                    'weight': 3,
                    'fillOpacity': 0.4
                },
                control=False
            ).add_to(m)

        #If radar is a miss, fill the circle

        elif r["type"] == "Miss":
            #plot a filled cicle
            folium.GeoJson(
                circle_shape,
                name="Miss Mask",
                style_function=lambda x: {
                    'fillColor': '#3388ff',
                    'color': '#3388ff',       
                    'weight': 3,
                    'fillOpacity': 0.4
                },
                control=False
            ).add_to(m)

def clip_tool(feature, mask_area):
    if feature.empty or mask_area.geometry.iloc[0].is_empty:
        return mask_area.iloc[0:0]  
    clipped_data = gpd.clip(feature, mask_area)
    return clipped_data


if __name__ == "__main__":
    main()
