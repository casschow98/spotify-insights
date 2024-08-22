import streamlit as st
import pandas as pd
import math
from pathlib import Path
from google.oauth2 import service_account
from google.cloud import bigquery
import db_dtypes
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px



# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Spotify dashboard',
    page_icon=':earth_americas:', # This is an emoji shortcode. Could be a URL too.
)

# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# -----------------------------------------------------------------------------
# Declare some useful functions.

# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def run_query(query):
    query_job = client.query(query)
    # rows_raw = query_job.result()
    # Convert to list of dicts. Required for st.cache_data to hash the return value.
    # rows = [dict(row) for row in rows_raw]
    df = client.query(query).to_dataframe()
    return df

summary_df = run_query("SELECT * FROM `famous-muse-426921-s5.spotify_cchow_dataset.spotify_summary`")
tracks_df = run_query("SELECT * FROM `famous-muse-426921-s5.spotify_cchow_dataset.spotify_cchow_table`")

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: Spotify dashboard

This is an analysis of my Spotify listening history as of August 2024. These insights are an analysis of various elements of the music I listen to.
'''

# Add some spacing
''
''

# min_value = gdp_df['Year'].min()
# max_value = gdp_df['Year'].max()

# from_year, to_year = st.slider(
#     'Which years are you interested in?',
#     min_value=min_value,
#     max_value=max_value,
#     value=[min_value, max_value])

# countries = gdp_df['Country Code'].unique()

# if not len(countries):
#     st.warning("Select at least one country")

# selected_countries = st.multiselect(
#     'Which countries would you like to view?',
#     countries,
#     ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

# ''
# ''
# ''

# Filter the data
# filtered_gdp_df = gdp_df[
#     (gdp_df['Country Code'].isin(selected_countries))
#     & (gdp_df['Year'] <= to_year)
#     & (from_year <= gdp_df['Year'])
# ]

st.header('Top Tracks', divider='gray')

''

st.dataframe(
    summary_df,
    width=1000,
    column_order=('Row','track_name','artists','times_played','spotify_url'),
    column_config={
        "Row": "Rank",
        "track_name": "Name",
        "artists": "Artists",
        "times_played": "Times Played",
        "spotify_url": st.column_config.LinkColumn("Spotify URL")
    },
    hide_index=True
)

''
''

st.header(f'Tempo Distribution', divider='gray')

''

# Calculate mean and median for annotation
mean_tempo = tracks_df['tempo'].mean()
median_tempo = tracks_df['tempo'].median()

# Create a histogram using Plotly
fig1 = px.histogram(
    tracks_df,
    x='tempo',
    nbins=10,
    labels={
        'tempo': 'Tempo (BPM)'
    }
)

# Add mean and median lines
fig1.add_vline(x=mean_tempo, line=dict(color='red', dash='dash'), annotation_text=f'Mean: {mean_tempo:.2f}', annotation_position='top right')
fig1.add_vline(x=median_tempo, line=dict(color='green', dash='dash'), annotation_text=f'Median: {median_tempo:.2f}', annotation_position='top left')

# Show the plot in Streamlit
st.plotly_chart(fig1)

st.write(f"**Mean Tempo:** {mean_tempo:.2f} BPM")
st.write(f"**Median Tempo:** {median_tempo:.2f} BPM")

''
''

st.header('Speechiness vs. Instrumentalness')

''

# Create a scatter plot using Plotly
fig2 = px.scatter(
    tracks_df,
    x='speechiness',
    y='instrumentalness',
    title='Speechiness vs. Instrumentalness',
    labels={
        'speechiness': 'Speechiness',
        'instrumentalness': 'Instrumentalness'
    }
)

# Show the plot in Streamlit
st.plotly_chart(fig2)


''
''

st.header(f'Stats', divider='gray')

''

cols = st.columns(3)

with cols[0]:
    count = len(tracks_df)
    st.metric("Total Tracks" , count, delta=None, help=None, label_visibility="visible")

with cols[1]:
    major_count = tracks_df[tracks_df['mode'] == 0].shape[0]
    minor_count = tracks_df[tracks_df['mode'] == 1].shape[0]
    if minor_count == 0:
        ratio = float('inf')  # Avoid division by zero
    else:
        gcd = math.gcd(major_count, minor_count)
        major_ratio = major_count // gcd
        minor_ratio = minor_count // gcd
        ratio_string = f"{major_ratio}:{minor_ratio}"
    st.metric("Ratio of Tracks in Major Keys to Minor Keys" , ratio_string, delta=None, help=None, label_visibility="visible")

with cols[2]:
    artist_counts = tracks_df['artists'].value_counts()
    top_artist = artist_counts.idxmax()

    st.metric("Most Listened to", top_artist, delta=None, help=None, label_visibility="visible")
