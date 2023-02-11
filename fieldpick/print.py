import pandas as pd
import logging


logging.getLogger("weasyprint").setLevel(logging.ERROR)

from frametools import generate_team_schedules

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os



logging.basicConfig(
    format="%(asctime)s %(levelname)s\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.ERROR,
)
logger = logging.getLogger()


# Load calendar
logger.info("Loading calendar data")
save_file = "data/calendar.pkl"
cFrame = pd.read_pickle(save_file)
print(f"Loaded {len(cFrame)} slots")


# Jinja Template
env = Environment(loader=FileSystemLoader("."))
template = env.get_template("fieldpick/reports/html_schedule.j2")


divisionFrames = generate_team_schedules(cFrame)
for division in divisionFrames.keys():

    # if division != "Majors":
    #     continue


    html_pages = []

    for team in divisionFrames[division].keys():
        print (f"Generating schedule for {division} {team}")
        team_frame = divisionFrames[division][team]

        drop_columns = [
            "Week_Number",
            "Time_Length",
            "Day_of_Year",
            "Sunset",
            "Datestamp",
            "Division",
            "Home_Team",
            "Away_Team",
            "Notes",
            "location",
            "size",
            "type",
            "infield",
        ]

        team_frame.drop(columns=drop_columns, inplace=True)

        rename_columns = {
            "Week_Name": "Week",
            "Day_of_Week": "Day",
            "Home_Team_Name": "Home",
            "Away_Team_Name": "Away",
        }
        team_frame.rename(rename_columns, axis=1, inplace=True)

        # print(team_frame)

        template_vars = {
            "title": f"{division} Schedule",
            "team_name": f"{team}",
            "division_name": f"{division}",
            "division_data": team_frame.to_html(index=False),
        }
        html_out = template.render(template_vars)
        html_pages.append(html_out)


    base_url = os.path.dirname(os.path.realpath(__file__))

    pdf_pages = [HTML(string=html, base_url=base_url).render(stylesheets=["fieldpick/reports/style.css"]) for html in html_pages]

    page_one = pdf_pages[0]
    for page in pdf_pages[1:]:
        page_one.pages.extend(page.pages)

    page_one.write_pdf(f"Schedule_{division}.pdf")


