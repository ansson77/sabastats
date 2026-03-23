import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import pandas as pd

# Kaukalon tulee olla kooltaan 40 x 20 metriä ja sen ympärillä on oltava laidat, jonka kulmat ovat pyöristetyt.
RINK_SCALER = 1
RINK_LENGTH = 40 * RINK_SCALER
RINK_WIDTH = 20 * RINK_SCALER

def create_pitch(ax, length=RINK_LENGTH, width=RINK_WIDTH):
    corner_radius = 2 * RINK_SCALER
    # Draw straight segments (leave gaps of length=radius near corners)
    ax.plot([corner_radius, length - corner_radius], [0, 0], color='black')          # bottom
    ax.plot([corner_radius, length - corner_radius], [width, width], color='black')  # top
    ax.plot([0, 0], [corner_radius, width - corner_radius], color='black')           # left
    ax.plot([length, length], [corner_radius, width - corner_radius], color='black') # right
    ax.plot([length / 2, length / 2], [0, width], color='black')


    corners = [
    ((corner_radius, corner_radius), 180, 270),                   # bottom-left
    ((length - corner_radius, corner_radius), 270, 360),          # bottom-right
    ((length - corner_radius, width - corner_radius), 0, 90),     # top-right
    ((corner_radius, width - corner_radius), 90, 180),            # top-left
    ]
    for center, t1, t2 in corners:
        arc = Arc(
            center,
            2 * corner_radius,  # width (diameter)
            2 * corner_radius,  # height (diameter)
            angle=0,
            theta1=t1,
            theta2=t2,
            color='black',
            linewidth=1.5
        )
        ax.add_patch(arc)
    
    x_big_goalie = [1.75 * RINK_SCALER, (1.75 + 4) * RINK_SCALER]
    y_big_goalie = [width/2 - (2.5 * RINK_SCALER), width/2 + (2.5 * RINK_SCALER)]

    # Here we draw the large goalie area left.
    ax.plot([x_big_goalie[0], x_big_goalie[0], x_big_goalie[1], x_big_goalie[1], x_big_goalie[0]],
             [y_big_goalie[0], y_big_goalie[1], y_big_goalie[1], y_big_goalie[0], y_big_goalie[0]], color="black")
    
    x_small_goalie = [x_big_goalie[0] + 0.65 * RINK_SCALER, x_big_goalie[0] + (1.65 * RINK_SCALER)]
    y_small_goalie = [width/2 - (1.25 * RINK_SCALER), width/2 + (1.25 * RINK_SCALER)]

    # Draw small goalie area left.
    ax.plot([x_small_goalie[0], x_small_goalie[0], x_small_goalie[1], x_small_goalie[1], x_small_goalie[0]],
             [y_small_goalie[0], y_small_goalie[1], y_small_goalie[1], y_small_goalie[0], y_small_goalie[0]], color='black')


    plt.axis('off')

    # Draw both goalie areas on the right.
    x_big_goalie = [length - x_big_goalie[0], length - x_big_goalie[1]]
    ax.plot([x_big_goalie[0], x_big_goalie[0], x_big_goalie[1], x_big_goalie[1], x_big_goalie[0]],
             [y_big_goalie[0], y_big_goalie[1], y_big_goalie[1], y_big_goalie[0], y_big_goalie[0]], color="black")
    
    x_small_goalie = [length - x_small_goalie[0], length - x_small_goalie[1]]
    ax.plot([x_small_goalie[0], x_small_goalie[0], x_small_goalie[1], x_small_goalie[1], x_small_goalie[0]],
             [y_small_goalie[0], y_small_goalie[1], y_small_goalie[1], y_small_goalie[0], y_small_goalie[0]], color='black')


def draw_shots(ax, df):
    df['x_coord'] = df['X'] * 0.01 * RINK_LENGTH
    df['y_coord'] = (100 - df['Y']) * 0.01 * RINK_WIDTH
    ax.scatter(df['x_coord'].to_numpy(), df['y_coord'].to_numpy(), s=6, alpha=0.6)


def main():
    fig, ax = create_pitch()

    df = pd.read_parquet('match_folder/2025-2026/a_b_2025_1_1.parquet')


    mask = (df['Team name'] == 'b')
    view = df.loc[mask, ['X', 'Y']]

    draw_shots(ax, view)
    plt.show()

if __name__ == '__main__':
    main()