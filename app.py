import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json

#Loads the cleaned and processed data thats going to be used.
#This includes median house price, median salary, and housing affordability index that I calculated
MergedData = pd.read_csv("Merged data.csv")

#Loads the boundary data for England and Wales which was edited during processing to use EPSG:4326 for the lat/lon coordinates
with open("fixed_boundaries.geojson") as f:
    geojson = json.load(f)