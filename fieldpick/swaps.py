import pandas as pd
import logging
from helpers import short_division_names

from frametools import (
    save_frame,
)
from gsheets import publish_df_to_gsheet


logging.basicConfig(
    format="%(asctime)s %(levelname)s\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger()


# Load calendar
logger.info("Loading calendar data")
save_file = "data/calendar.pkl"
cFrame = pd.read_pickle(save_file)
print(f"Loaded {len(cFrame)} slots")


def team_swap(cf, teamA, teamB):
    cf.replace(teamA, "TEMP_TEAM", inplace=True)
    cf.replace(teamB, teamA, inplace=True)
    cf.replace("TEMP_TEAM", teamB, inplace=True)
    return cf

team_swap(cFrame, "Rookie_AL_03", "Rookie_NL_06")

save_frame(cFrame, "calendar.pkl")
