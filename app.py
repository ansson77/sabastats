from dash import Dash, html, dcc, Output, Input
import pandas as pd
from io import BytesIO
import plotly.graph_objects as go
import numpy as np

RINK_LENGTH = 40
RINK_WIDTH = 20


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

    fig.add_scattergl(
        x=view["X"], y=view["Y"], mode="markers",
        marker=dict(size=6, opacity=0.6),
        name="Shots",
    )

    return fig

app = Dash()

df = pd.read_parquet('match_folder/2025-2026/a_b_2025_1_1.parquet')
df['Y'] = 20 - df['Y']

view = df[df['Team name'] == 'a']
view = view[view['Player number'] == '77']


app.layout = html.Div([
    dcc.Graph(id="shots", figure=create_pitch_plotly())
])


if __name__ == '__main__':
    app.run(debug=True)
