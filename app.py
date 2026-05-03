from dash import Dash, html, dcc, Output, Input, callback
import pandas as pd
# from io import BytesIO
import plotly.graph_objects as go
import numpy as np
from plotly.colors import qualitative as qual
from datetime import date
from pathlib import Path

RINK_LENGTH = 40
RINK_WIDTH = 20
GOAL_HEIGHT = 115
GOAL_WIDTH = 160

BINSIZE = 0.75  # adjust via slider if you want

x_edges = np.arange(0, RINK_LENGTH + BINSIZE, BINSIZE)
y_edges = np.arange(0, RINK_WIDTH + BINSIZE, BINSIZE)
x_centers = (x_edges[:-1] + x_edges[1:]) / 2
y_centers = (y_edges[:-1] + y_edges[1:]) / 2

def _player_sort(s):
    num_token, _, _ = s[1:].partition(' ')
    if num_token == 'OG' or num_token == 'M':
        return 100
    return int(num_token)

def _quarter_arc(cx, cy, r, theta1_deg, theta2_deg, n=64):
    """Return x,y points for a circular arc centered at (cx,cy) with radius r,
    from theta1 to theta2 in degrees."""
    thetas = np.radians(np.linspace(theta1_deg, theta2_deg, n))
    x = cx + r * np.cos(thetas)
    y = cy + r * np.sin(thetas)
    return x, y

def create_pitch_plotly(length=RINK_LENGTH, width=RINK_WIDTH):
    corner_radius = 2
    r = corner_radius

    shapes = []

    # Straight segments (gaps near corners)
    shapes += [
        # bottom edge
        dict(type="line", x0=r, y0=0, x1=length - r, y1=0,
             line=dict(color="black", width=2)),
        # top edge
        dict(type="line", x0=r, y0=width, x1=length - r, y1=width,
             line=dict(color="black", width=2)),
        # left edge
        dict(type="line", x0=0, y0=r, x1=0, y1=width - r,
             line=dict(color="black", width=2)),
        # right edge
        dict(type="line", x0=length, y0=r, x1=length, y1=width - r,
             line=dict(color="black", width=2)),
        # center line
        dict(type="line", x0=length / 2, y0=0, x1=length / 2, y1=width,
             line=dict(color="black", width=2)),
    ]

    # Goalie areas (left side) — rectangles
    x_big_goalie = (1.75 , 1.75 + 4)
    y_big_goalie = (width/2 - 2.5, width/2 + 2.5)

    shapes.append(
        dict(
            type="rect",
            x0=x_big_goalie[0], y0=y_big_goalie[0],
            x1=x_big_goalie[1], y1=y_big_goalie[1],
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)"
        )
    )
    shapes.append(
        dict(
            type='rect',
            x0=length - x_big_goalie[0], y0=y_big_goalie[0],
            x1=length - x_big_goalie[1], y1=y_big_goalie[1],
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)"
        )
    )

    x_small_goalie = (x_big_goalie[0] + 0.65, x_big_goalie[0] + 1.65)
    y_small_goalie = (width/2 - 1.25, width/2 + 1.25)

    shapes.append(
        dict(
            type="rect",
            x0=x_small_goalie[0], y0=y_small_goalie[0],
            x1=x_small_goalie[1], y1=y_small_goalie[1],
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)"
        )
    )
    shapes.append(
        dict(
            type='rect',
            x0=length - x_small_goalie[0], y0=y_small_goalie[0],
            x1=length - x_small_goalie[1], y1=y_small_goalie[1],
            line=dict(color="black", width=2),
            fillcolor="rgba(0,0,0,0)"
        )
    )

    # Corner arcs: draw as line traces approximating quarter-circles
    corner_specs = [
        # (center_x, center_y, theta1, theta2)
        (r, r, 180, 270),                   # bottom-left
        (length - r, r, 270, 360),          # bottom-right
        (length - r, width - r, 0, 90),     # top-right
        (r, width - r, 90, 180),            # top-left
    ]

    arc_traces = []
    for cx, cy, t1, t2 in corner_specs:
        x, y = _quarter_arc(cx, cy, r, t1, t2, n=64)
        arc_traces.append(
            go.Scatter(
                x=x, y=y,
                mode="lines",
                line=dict(color="black", width=2),
                hoverinfo="skip",
                showlegend=False
            )
        )

    fig = go.Figure()
    # Add arcs first or last; shapes are always under data by default, so order isn’t critical
    for tr in arc_traces:
        fig.add_trace(tr)

    fig.update_layout(
        shapes=shapes,
        xaxis=dict(range=[0, length], visible=False),
        yaxis=dict(range=[0, width], visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    return fig

def add_team_trace(fig, view, team):
    color = team_colors.get(team, '#1f77b4')
    
    fig.add_trace(go.Scattergl(
        x=view['X'].to_numpy(),
        y=view['Y'].to_numpy(),
        mode='markers',
        marker=dict(size=8, color=color, opacity=0.85),
        name=team,
        # number=view['Player'],
        hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}<br>Team: %{text}<br>Player: %{number}<extra></extra>",
        text=view['Team name'],
        showlegend=False
    ))

def heatmap_trace(fig, view):
    opacity = 0.8
    if view.empty:
        z = np.zeros((len(y_centers), len(x_centers)), dtype=float)
    else:
        # histogram2d returns shape (len(x_edges)-1, len(y_edges)-1) with x-first; transpose for Plotly
        H, _, _ = np.histogram2d(view["X"].to_numpy(), view["Y"].to_numpy(),
                                 bins=[x_edges, y_edges])
        z = H.T  # transpose so z[y, x]

    fig.add_trace(go.Heatmap(
        x=x_centers,
        y=y_centers,
        z=z,
        colorscale='Inferno',
        zmin=0,
        zmax=None,        # let scale adapt; or set a cap for comparability
        opacity=opacity,
        colorbar=dict(title="Shots"),
        hovertemplate="x: %{x:.2f}<br>y: %{y:.2f}<br>shots: %{z}<extra></extra>"
    ))
    return fig

    
def make_figure(selected_teams, selected_player, seasons_to_include, shot_outcomes_selected, heatmap_toggle):
    shot_outcomes_selected = shot_outcomes_selected or []
    min_date = date(seasons_to_include[0], 6, 10)
    max_date = date(seasons_to_include[1] + 1, 6, 9)

    fig = create_pitch_plotly()

    mask = pd.Series(True, index=df.index)

    mask &= (df['date'] >= min_date)
    mask &= (df['date'] <= max_date)

    if selected_teams:  # list (may be empty)
        mask &= df["Team name"].isin(selected_teams)

    mask &= df["Shot outcome"].isin(shot_outcomes_selected)
    if selected_player != 'All':
        mask &= df['Player'] == selected_player

    # Slice once and keep only plotting columns
    view = df.loc[mask, ["X", "Y", "Team name", 'Player']]

    if heatmap_toggle == 'points':
        for team in selected_teams:
            sub = view[view['Team name'] == team]
            if not sub.empty:
                add_team_trace(fig, sub, team)
        fig.update_layout(legend=dict(orientation="h", x=0.5, xanchor="center", y=1.02))
    
    else:
        fig = heatmap_trace(fig, view)

    return fig

def create_goal_plotly():
    # Official dimensions are 115cm x 160cm
    height = GOAL_HEIGHT
    width = GOAL_WIDTH

    corner_radius = 12 # This can be vibed
    post_width = 15

    shapes = []

    shapes += [
        # left post
        dict(type="line", x0=0, y0=0, x1=0, y1=height,
             line=dict(color="black", width=post_width)),
        # Top bar
        dict(type='line', x0=0, y0=height, x1=width, y1=height,
             line=dict(color='black', width=post_width)),
        # Right post
        dict(type='line', x0=width, y0=height, x1=width, y1=0,
             line=dict(color='black', width=post_width))
        ]

    fig = go.Figure()

    fig.update_layout(
        shapes=shapes,
        xaxis=dict(range=[0, width], visible=False),
        yaxis=dict(range=[0, height], visible=False, scaleanchor="x", scaleratio=1),
        margin=dict(l=0, r=0, t=0, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig

def draw_shots_in_goal(fig, view):
    # -5.0 <= Goal_X <= 73
    # -4.0 <= Goal_Y <= 51.5
    # Bro wtf are these values?? These were the extreme values for the entire season 2025-2026,
    # In the original data the height is measured from the top, so we mirror it here after scaling it.
    # so theyre probably good enough to handle all edge cases.

    '''
    Even though values of shot coordinates vary between the values stated above, inspecting the extreme values 
    you can see they are obviously nonsense, as they are completely inside the posts or ground. 
    Therefore I clip them to sensible values.
    Equation used is ( (x - x_min) / (x_max - x_min) ) * (y_max - y_min) + y_min
    '''
    x = (view['Goal_X'].clip(0, 68).to_numpy() / 68 * (155 - 5) + 5)
    y = GOAL_HEIGHT - (view['Goal_Y'].clip(0, 50).to_numpy() / 50 * (112 - 5) + 5)
    
    fig.add_trace(go.Scattergl(
        x=x,
        y=y,
        mode='markers',
        marker=dict(size=24, color='lightblue', opacity=0.85),
        showlegend=False
    ))
    # test_df = pd.read_csv('test_csv.csv')
    # testx = ((test_df['Goal_X'].to_numpy() + 5) / (73 + 5) * (155 - 5) + 5)
    # testy = GOAL_HEIGHT - ((test_df['Goal_Y'].to_numpy() + 4) / (51.5 + 4) * (112 - 5) + 5)
    # # ( (x - x_min) / (x_max - x_min) ) * (y_max - y_min) + y_min
    # fig.add_trace(go.Scattergl(
    #     x=testx,
    #     y=testy,
    #     mode='markers',
    #     marker=dict(size=24, color='blue', opacity=0.85),
    #     showlegend=False
    # ))

def draw_goal(selected_teams, outfield_player_chosen, seasons_to_include, goalie='All'):
    fig = create_goal_plotly()
    min_date = date(seasons_to_include[0], 6, 10)
    max_date = date(seasons_to_include[1] + 1, 6, 9)

    mask = pd.Series(True, index=df.index)

    if goalie != 'All':
        mask &= (df['Goalie'] == goalie)
    
    mask &= (df['date'] >= min_date)
    mask &= (df['date'] <= max_date)
    if outfield_player_chosen != 'All':
        mask &= (df['Player'] == outfield_player_chosen)

    if selected_teams:  # list (may be empty)
        mask &= df["Team name"].isin(selected_teams)

    view = df.loc[mask, ["Goal_X", "Goal_Y"]]

    draw_shots_in_goal(fig, view)
    
    return fig


app = Dash()

data_dir = Path('match_folder/2025-2026')

full_df = pd.concat(
    pd.read_parquet(parquet_file)
    for parquet_file in data_dir.glob('*.parquet')
)

# df = pd.read_parquet('match_folder/testing/a_b_2025_1_1.parquet')

df = full_df

# Mirror shots on the Y axis, as the origin in the scraped data is top left, while mine is in bottom left.
df['Y'] = 20 - df['Y']
# Encode the shot outcome into binary variable for xG calculation.
df['is_goal'] = (df['Shot outcome'].eq('shot_goal')).astype('Int8')


teams = df['Team name'].unique().tolist()
teams.sort()
first_season = 2010
last_season = 2025

players_of_teams = {team: df[df['Team name'] == team]['Player'].unique().tolist() for team in teams}
all_goalies = df['Goalie'].dropna().unique().tolist()

palette = qual.Set2  # or qual.Set1, qual.D3, etc.
team_colors = {team: palette[i % len(palette)] for i, team in enumerate(teams)}

app.layout = html.Div([
    html.Div([
        dcc.RangeSlider(min=first_season, 
                   max=last_season, 
                   marks={i: f'{i}-{i+1}' for i in range(first_season, last_season + 1, 1)}, 
                   value=[2024,2025], 
                   reverse=False, 
                   included=True,
                   id='season_slider')
    ], style={'margin-bottom': '30px'}),

    html.Div([
        dcc.Checklist(options=teams, value=teams, id='team_selector')
    ], style={'width': '20%', 'display': 'inline-block'}),

    html.Div([
        dcc.Dropdown(id='player_selector', value='All')
    ], style={'width': '20%', 'display': 'inline-block'}),

    html.Div([
        dcc.Checklist(options=[
       {'label': 'Goal', 'value': 'shot_goal'},
       {'label': 'Saved', 'value': 'shot_saved'},
       {'label': 'Blocked', 'value': 'shot_blocked'},
       {'label': 'Miss', 'value': 'shot_offtarget'}
        ],

                value=['shot_goal', 'shot_saved', 'shot_blocked', 'shot_offtarget'],
                id='shot_outcome_selector')
    ], style={'width': '20%', 'display': 'inline-block', 'margin-left': '30px'}),

    html.Div([
        dcc.RadioItems(options=[{'label': 'Points', 'value': 'points'},
                                {'label': 'Heatmap', 'value': 'heatmap'}],
                        value='points',
                        id='heatmap_toggle')
    ], style={'width': '20%', 'display': 'inline-block', 'margin-left': '30px'}),

    dcc.Graph(id="graph_item", figure=create_pitch_plotly(), style={'margin-bottom': '50px', 'margin-top': '30px'}),

    html.Div([
        html.Div([
        dcc.Dropdown(id='goalie_selector', 
                     options=['All'] + sorted(all_goalies, key=_player_sort),
                     value='All')], style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
        dcc.Graph(id='goalie_graph_item', figure=create_goal_plotly(), style={'margin-bottom': '100px'})],
            style={'width': '65%', 'display': 'inline-block'})])
])


@callback(
    Output('player_selector', 'options'),
    Input('team_selector', 'value'))
def set_player_options(selected_team):
    list_of_players = [{'label': 'All', 'value': 'All'}]

    if len(selected_team) > 1:
        for team in selected_team:
            list_of_players += [{'label': i, 'value': i} for i in \
                                sorted(players_of_teams[team], \
                                       key=_player_sort)]
        return list_of_players
    
    elif len(selected_team) == 0:
        return list_of_players
    
    return list_of_players + [{'label': i, 'value': i} for i in \
                              sorted(players_of_teams[selected_team[0]], \
                                     key=_player_sort)]


@callback(
    Output('player_selector', 'value'),
    Input('player_selector', 'options'))
def set_player_value(available_options):
    return available_options[0]['value']


@callback(
    Output('graph_item', 'figure'),
    Input('team_selector', 'value'),
    Input('player_selector', 'value'),
    Input('season_slider', 'value'),
    Input('shot_outcome_selector', 'value'),
    Input('heatmap_toggle', 'value'))
def update_graph(teams_chosen, player_chosen, seasons_to_include, shot_outcomes_selected, heatmap_toggle):
    return make_figure(teams_chosen, player_chosen, seasons_to_include, shot_outcomes_selected, heatmap_toggle)

@callback(
    Output('goalie_graph_item', 'figure'),
    Input('team_selector', 'value'),
    Input('player_selector', 'value'),
    Input('season_slider', 'value'),
    Input('goalie_selector', 'value'))
def update_goalie_graph(teams_chosen,  player_chosen, seasons_to_include, goalie):
    return draw_goal(teams_chosen, player_chosen, seasons_to_include, goalie)


if __name__ == '__main__':
    app.run(debug=True)
