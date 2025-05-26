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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "England & Wales Housing Affordability Dashboard"


#Function that created the choropleth map
def generate_affordability_map(df, title):
#creates bands for the affordability index to use when colouring the choropleth map
    bins = [0, 6, 9, 12, float("inf")]
    labels = ["Very Affordable", "Affordable", "Expensive", "Very Expensive"]

    df["Affordability Level"] = pd.cut(
        df["Housing Affordability Index"],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    color_map = {
        "Very Affordable": "green",
        "Affordable": "yellow",
        "Expensive": "orange",
        "Very Expensive": "red"
    }

#The choropleth map code
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="LAD23CD",
        featureidkey="properties.LAD23CD",
        color="Affordability Level",
        color_discrete_map=color_map,
        hover_name="Location",
        custom_data=[
            "Housing Affordability Index", 
            "Median House Price", 
            "Median Salary"
        ],
        title=title
    )

#Formats the information displayed so that the index rounds to 2 decimal places and the price values are in pricing format
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" +
                      "Affordability Index: %{customdata[0]:.2f}<br>" +
                      "Median House Price: £%{customdata[1]:,.0f}<br>" +
                      "Median Salary: £%{customdata[2]:,.0f}<extra></extra>"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})

    return fig

if __name__ == "__main__":
    app.run(debug=True)