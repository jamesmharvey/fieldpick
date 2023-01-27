import calendar
from datetime import datetime, timedelta
import pandas as pd
import sys

from inputs import blackout_days, week_split_data, field_info
import logging

logger = logging.getLogger()


# Helper date conversion functions
def date_string_to_datetime(date):
    # print(f"Converting {date} to datetime")
    return datetime.strptime(date, "%m/%d/%Y")


# Create a list of days between start and end
def range_of_dates(start_date, end_date):
    start_date = date_string_to_datetime(start_date)
    end_date = date_string_to_datetime(end_date)
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)


def add_time_slots(
    fields=None,  # One or many fields matching this pattern
    days_of_week=None,  # One or many days valid days of the week
    start_day=None,
    end_day=None,
    times=None,
    blackout_days=blackout_days,
    week_split_data=week_split_data,
    field_data=field_info,
    only_days=None,
    input=pd.DataFrame(),
):


    if isinstance(fields, str):
        fields = [fields]

    output = pd.DataFrame()

    # If given explicit days, use those
    if only_days:
        date_range = [date_string_to_datetime(i) for i in only_days]
    # Otherwise, use the range of dates
    else:
        date_range = range_of_dates(start_day, end_day)

    for single_date in date_range:
        day_of_week = calendar.day_name[single_date.weekday()]

        # Skip conditions
        if day_of_week not in days_of_week:
            continue
        if single_date in blackout_days:
            continue

        # Determine week number
        schedule_week = "UNKNOWN"
        week_number = "UNKNOWN"
        for (week, week_start) in week_split_data.items():
            if single_date >= week_start:
                schedule_week = week
                week_number = schedule_week.split(" ")[1]

        # Apply for multiple fields
        for field in fields:
            for (start_time, end_time) in times:
                logger.info(f"Creating slot for {day_of_week} {single_date.date()} {start_time}-{end_time} {field}")
                (hours, minutes) = start_time.split(":")
                datestamp = single_date + timedelta(
                    hours=int(hours), minutes=int(minutes)
                )

                # Calculate field time length
                (start_h, start_m) = start_time.split(":")
                (end_h, end_m) = end_time.split(":")
                game_length = (60 * int(end_h) + int(end_m)) - (
                    60 * int(start_h) + int(start_m)
                )
                game_length_pretty = game_length

                mydata = dict(
                    Week_Name=f"{schedule_week}",
                    Week_Number=week_number,
                    Day_of_Week=f"{day_of_week}",
                    Date=f"{single_date.date()}",
                    Start=f"{start_time}",
                    End=f"{end_time}",
                    Time_Length=f"{game_length_pretty}",
                    Datestamp=datestamp,
                    Day_of_Year=f"{single_date.timetuple().tm_yday}",
                    Field=f"{field}",
                    Division=None,
                    Home_Team=None,
                    Home_Team_Name=None,
                    Away_Team=None,
                    Away_Team_Name=None,
                    Game_ID=None,
                )
                # adds field data
                if field not in field_data:
                    logger.error(f"ERROR Field {field} not found in field data -- check inputs.py")
                    sys.exit(1)
                for (key, value) in field_data[field].items():
                    if key == "field_name":
                        continue  # redundant
                    mydata[key] = value
                mydf = pd.DataFrame(mydata, index=[0])

                output = pd.concat([output, mydf], ignore_index=True)

    if not input.empty:
        return pd.concat([input, output], ignore_index=True)
    else: 
        return output


################################################################################
# Macros
fort_scott = ["Ft. Scott - North", "Ft. Scott - South"]
farm_scott_goode = ["Ft. Scott - South", "Paul Goode Practice"]
tepper_ketcham = ["Tepper", "Ketcham"]
ti = tepper_ketcham
weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
monday_thursday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]
tuesday_thursday = ["Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]
anyday_but_friday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Saturday", "Sunday"]


short_division_names = {
    "Farm - Lower": "FML",
    "Farm - Upper": "FMU",
    "Rookie": "RK",
    "Minors AA": "AA",
    "Minors AAA": "AAA",
    "Majors": "MAJ",
    "Juniors": "JRS",
    "Seniors": "SRS",
    "Softball": "SFT",
    "Tee Ball": "TB",
}
