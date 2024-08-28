import streamlit as st
import pandas as pd
import math
from pathlib import Path
from google.oauth2 import service_account
from google.cloud import bigquery
import db_dtypes
import plotly.express as px
import pytz
import numpy as np
from sklearn.metrics import r2_score




# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Spotify Insights',
    page_icon='https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png'
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
st.markdown('''
<h1 style="font-size: 48px; display: flex; align-items: center;">
    <img src="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png" alt="Spotify Logo" style="width:50px; margin-right: 10px;">
    Spotify Insights
</h1>
            
<p>Welcome to my spotify data pipeline project! See below the results from analyses of my personal listening history as of August 2024. This data was obtained through the Spotify Web API.</p>
''', unsafe_allow_html=True)

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


''

tabs = st.tabs(["Top Tracks", "Recently Played"])

# Display Top Tracks
with tabs[0]:
    st.header("Top Tracks")
    st.dataframe(
        summary_df,
        width=1000,
        column_order=('rank','track_name','artists','times_played','spotify_url'),
        column_config={
            "rank": "Rank",
            "track_name": "Name",
            "artists": "Artists",
            "times_played": "Times Played",
            "spotify_url": st.column_config.LinkColumn("Spotify URL")
        },
        hide_index=True
    )

with tabs[1]:
    st.header("Recently Played")

    sorted_df = tracks_df.sort_values(by="played_at", ascending=False)
    rp_df = sorted_df.head(20)
    
    rp_df['played_at'] = pd.to_datetime(rp_df['played_at'], utc=True)
    rp_df['pt_dt'] = rp_df['played_at'].dt.tz_convert('America/Los_Angeles')
    rp_df['pt_dt'] = rp_df['pt_dt'].dt.strftime('%b %d, %Y %I:%M %p')

    st.dataframe(
        rp_df,
        width=1000,
        column_order=('track_name','artists','pt_dt','track_duration','spotify_url'),
        column_config={
            "track_name": "Name",
            "artists": "Artists",
            "pt_dt": "Played At (PT)",
            "track_duration": "Length",
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

fig1.update_layout(
    plot_bgcolor='rgba(14, 17, 23, 1)',
    paper_bgcolor='rgba(14, 17, 23, 1)',
)

# Add mean and median lines
fig1.add_vline(x=mean_tempo, line=dict(color='red', dash='dash'), annotation_text=f'Mean: {mean_tempo:.2f}', annotation_position='top right')
fig1.add_vline(x=median_tempo, line=dict(color='#39FF14', dash='dash'), annotation_text=f'Median: {median_tempo:.2f}', annotation_position='top left')

# Show the plot in Streamlit
st.plotly_chart(fig1,theme=None)

st.write(f"**Mean Tempo:** {mean_tempo:.2f} BPM")
st.write(f"**Median Tempo:** {median_tempo:.2f} BPM")

''
''

st.header('Speechiness vs. Instrumentalness')

''

# Create a scatter plot using Plotly
m, b = np.polyfit(tracks_df['speechiness'], tracks_df['instrumentalness'], 1)
tracks_df['y_pred'] = m * tracks_df['speechiness'] + b

r_squared = r2_score(tracks_df['instrumentalness'], tracks_df['y_pred'])


fig2 = px.scatter(
    tracks_df,
    x='speechiness',
    y='instrumentalness',
    labels={
        'speechiness': 'Speechiness',
        'instrumentalness': 'Instrumentalness'
    }
)

fig2.add_traces(px.line(tracks_df, x='speechiness', y='y_pred').data) 

fig2.add_annotation(
    x=0,
    y=-0.25,
    xref='paper',
    yref='paper',
    text=f"Slope: {m:.2f}",
    showarrow=False,
    font=dict(size=12)
)

fig2.add_annotation(
    x=0,
    y=-0.3,
    xref='paper',
    yref='paper',
    text=f"R-squared: {r_squared:.2f}",
    showarrow=False,
    font=dict(size=12)
)

fig2.update_layout(
    plot_bgcolor='rgba(14, 17, 23, 1)',
    paper_bgcolor='rgba(14, 17, 23, 1)',
    margin=dict(b=100)
)

# Show the plot in Streamlit
st.plotly_chart(fig2,theme=None)


''
''

st.header(f'Stats', divider='gray')

''

cols = st.columns(2)

with cols[0]:
    count = len(tracks_df)
    st.metric("Total Songs Listened" , count, delta=None, help=None, label_visibility="visible")

with cols[1]:
    major_count = tracks_df[tracks_df['mode'] == 0].shape[0]
    minor_count = tracks_df[tracks_df['mode'] == 1].shape[0]
    if major_count == 0:
        pct_str = f"100%"
    else:
        minor_pct = minor_count/count*100
        pct_str = f"{minor_pct:.1f}%"
    st.metric("Songs in Minor Key" , pct_str, delta=None, help=None, label_visibility="visible")

artist_counts = tracks_df['artists'].value_counts()
top_artist = artist_counts.idxmax()

st.metric("Most Listened to", top_artist, delta=None, help=None, label_visibility="visible")



''
''

st.header(f'Top 10 Audio Features', divider='gray')

''

af_df = summary_df[['track_name','danceability','energy','valence']]
af_df.set_index('track_name', inplace=True)

fig3 = px.bar(
    af_df.reset_index(),
    x='track_name',
    y=['danceability', 'energy', 'valence'],
    labels={
        'value': 'Score',
        'track_name': 'Track Name'
    },
    height=500
)

fig3.update_layout(
    plot_bgcolor='rgba(14, 17, 23, 1)',
    paper_bgcolor='rgba(14, 17, 23, 1)',
    xaxis=dict(
        tickangle=25,  # Angle of x-axis labels
        title_standoff=25  # Space between x-axis title and labels
    )
)

fig3.update_xaxes(automargin=True)

st.plotly_chart(fig3,theme=None)