import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import json

#Loads the cleaned and processed data thats going to be used.
#This includes median house price, median salary, and housing affordability index that I calculated
MergedData = pd.read_csv("Merged data.csv")

MergedData["Original Affordability Index"] = MergedData["Housing Affordability Index"].copy()

#Loads the boundary data for England and Wales which was edited during processing to use EPSG:4326 for the lat/lon coordinates
with open("fixed_boundaries.geojson") as f:
    geojson = json.load(f)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = "England & Wales Housing Affordability Index Dashboard"


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

#The choropleth map code used during the data processing
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
        title=title,
        template="plotly_dark"
    )

#Formats the information displayed so that the index rounds to 2 decimal places and the price values are in pricing format
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>" +
                      "Affordability Index: %{customdata[0]:.2f}<br>" +
                      "Median House Price: £%{customdata[1]:,.0f}<br>" +
                      "Median Salary: £%{customdata[2]:,.0f}<extra></extra>"
    )

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0},
                      paper_bgcolor="#2a2a2a",
                      plot_bgcolor="#2a2a2a")

    return fig

#Creates a html table which will be used to show the top 5 most affordable/expensive places to live
def df_to_html_table(df):
    header = [html.Th(col) for col in df.columns]
    rows = [html.Tr([html.Td(cell) for cell in row]) for row in df.values]
    return [html.Thead(html.Tr(header)), html.Tbody(rows)]

#The app layout design is below, using dash bootstrap
app.layout = dbc.Container([
    #adds a title to the page
    dbc.Row([
        dbc.Col(html.H1("Housing Affordability Index for England & Wales", className="dashboard-title"), width=12)
    ]),
    #adds the location for where the choropleth map will show once loaded
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="choropleth-map", className="custom-graph")
        ])
    ], className="custom-row"),
    #adds the section where users will be able to enter their own salary to see updates on the map
    dbc.Row([
        dbc.Col([
            html.Label("Enter your annual salary (£):", className="input-label"),
            html.Div([
                dcc.Input(
                    id="salary-input",
                    type="number",
                    placeholder="Enter your annual salary",
                    step=1,
                    className="custom-input me-2"
                ),
                dbc.Button(
                    "Reset Map",
                    id="reset-button",
                    color="secondary",
                    className="custom-button"
                )
            ], className="d-flex flex-column flex-md-row align-items-stretch align-items-md-end"),
            dbc.Alert(
                id="salary-warning",
                color="danger",
                is_open=False,
                dismissable=True,
                className="custom-alert mt-2"
            )
        ], xs=12, md=8)
    ], justify="center", className="custom-row"),

    #adds 2 tables to show the top 5 most/least affordable areas 
    dbc.Row([
        dbc.Col([
            html.H4("Top 5 Most Affordable Areas", className="affordable-table-header"),
            dbc.Table(id="affordable-table", bordered=True, hover=True, striped=True, responsive=True, className="custom-table")
        ], xs=12, md=6),

        dbc.Col([
            html.H4("Top 5 Most Expensive Areas", className="expensive-table-header"),
            dbc.Table(id="expensive-table", bordered=True, hover=True, striped=True, responsive=True, className="custom-table")
        ], xs=12, md=6)
    ], className="custom-row")
], fluid=True)

#Callbacks to show changes made due to user inputs
@app.callback(
    Output("choropleth-map", "figure"),
    Output("affordable-table", "children"),
    Output("expensive-table", "children"),
    Output("salary-warning", "children"),
    Output("salary-warning", "is_open"),
    Input("salary-input", "value"),
    Input("reset-button", "n_clicks")
)
#function that updates the dashboard depending on user input
def update_dashboard(user_salary, reset_clicks):
    warning_message = ""
    show_warning = False
    df = MergedData.copy()

    ctx = dash.callback_context
    triggered_by_reset = ctx.triggered and ctx.triggered[0]["prop_id"] == "reset-button.n_clicks"

    if triggered_by_reset:
        df["Housing Affordability Index"] = df["Original Affordability Index"]
        warning_message = ""
        show_warning = False
    #displays an error message prompting the user to enter a valid number if they input something invalid for the salary
    elif user_salary is not None and user_salary > 0:
        df["Housing Affordability Index"] = df["Median House Price"] / user_salary
        warning_message = ""
        show_warning = False

    elif user_salary is not None and user_salary <= 0:
        warning_message = "\u26a0 Please enter a valid salary greater than £0."
        df["Housing Affordability Index"] = df["Original Affordability Index"]
        show_warning = True
    #creates new index based on the user's inputted salary
    else:
        df["Housing Affordability Index"] = df["Original Affordability Index"]
        warning_message = ""
        show_warning = False
    
    #bins that are used for colour coding the choropleth map depending on the affordability index score
    bins = [0, 6, 9, 12, float("inf")]
    labels = ["Very Affordable", "Affordable", "Expensive", "Very Expensive"]
    df["Affordability Level"] = pd.cut(df["Housing Affordability Index"], bins=bins, labels=labels)

    # pulls in the top 5 most/least affordable places
    top_affordable = df.nsmallest(5, "Housing Affordability Index")[["Location", "Median House Price", "Median Salary", "Housing Affordability Index"]].copy()
    top_expensive = df.nlargest(5, "Housing Affordability Index")[["Location", "Median House Price", "Median Salary", "Housing Affordability Index"]].copy()

    for col in ["Median House Price", "Median Salary"]:
        top_affordable[col] = pd.to_numeric(top_affordable[col], errors="coerce")
        top_expensive[col] = pd.to_numeric(top_expensive[col], errors="coerce")

        top_affordable[col] = top_affordable[col].map(lambda x: f"£{x:,.0f}" if pd.notnull(x) else "N/A")
        top_expensive[col] = top_expensive[col].map(lambda x: f"£{x:,.0f}" if pd.notnull(x) else "N/A")

    top_affordable["Housing Affordability Index"] = pd.to_numeric(top_affordable["Housing Affordability Index"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
    top_expensive["Housing Affordability Index"] = pd.to_numeric(top_expensive["Housing Affordability Index"], errors="coerce").map(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")

    title = "England & Wales Housing Affordability Map based on 2024 data"
    if not triggered_by_reset and user_salary and user_salary > 0:
        title = f"Affordability based on an annual salary of £{int(user_salary):,} "

    # Return updated map, tables, and warning
    return (
        generate_affordability_map(df, title),
        df_to_html_table(top_affordable),
        df_to_html_table(top_expensive),
        warning_message,
        show_warning
    )

if __name__ == "__main__":
    app.run(debug=True)