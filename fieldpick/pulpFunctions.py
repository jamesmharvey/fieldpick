from pulp import lpSum, LpStatus, PULP_CBC_CMD
import sys
import logging
import math


logging.basicConfig(
    format="%(asctime)s %(levelname)s\t%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger()

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


# Common constraints for all divisions
def common_constraints(prob, slots_vars, teams, slot_ids, working_slots):

    days_of_year = working_slots["Day_of_Year"].unique()

    # Basic constraints
    prob = one_game_per_slot(prob, slots_vars, teams, slot_ids)
    prob = cannot_play_yourself(prob, slots_vars, teams, slot_ids)

    # Limit consecutive games
    prob = no_back_to_back(prob, days_of_year, working_slots, slots_vars, teams)
    prob = limit_3_in_5(prob, days_of_year, working_slots, slots_vars, teams)
    prob = limit_3_in_6(prob, days_of_year, working_slots, slots_vars, teams)


    # Limit games per day
    prob = limit_games_per_day(prob, days_of_year, working_slots, slots_vars, teams, limit=1)

    # Limit games per week
    prob = limit_weekday_games_per_week(prob, teams, working_slots, slots_vars, limit=1)

    return prob

def same_opponent(prob, slots_vars, teams, slot_ids):
    # Minimize games played against a single opponent
    for k in teams:
        for j in teams:
            if i != j:
                prob += lpSum([slots_vars[i, j, k] + slots_vars[i, k, j] for i in slot_ids]) <= 1, f"Max_faceoffs_{k}_vs_{j}"

    return prob

def one_game_per_slot(prob, slots_vars, teams, slot_ids):
    # 1 game per slot
    for i in slot_ids:
        prob += lpSum([slots_vars[i, j, k] for j in teams for k in teams]) <= 1, f"Only_one_game_per_slot_{i}"
    return prob

def cannot_play_yourself(prob, slots_vars, teams, slot_ids):
    # Cannot play self
    for i in slot_ids:
        prob += lpSum([slots_vars[i, j, j] for j in teams]) == 0, f"Cannot_play_self_{i}"
    return prob

def minimum_games_per_team(prob, teams, slots_vars, slot_ids, min_games=11):
    # Each team must play at least $min_games
    for j in teams:
        prob += (
            lpSum([slots_vars[i, j, k] for i in slot_ids for k in teams])
            + lpSum([slots_vars[i, k, j] for i in slot_ids for k in teams])
        ) >= min_games, f"min_games_per_team_{j}"
    return prob

def maximum_games_per_team(prob, teams, slots_vars, slot_ids, max_games=11):
    # Each team must play at least $min_games
    for j in teams:
        prob += (
            lpSum([slots_vars[i, j, k] for i in slot_ids for k in teams])
            + lpSum([slots_vars[i, k, j] for i in slot_ids for k in teams])
        ) <= max_games, f"max_games_per_team_{j}"
    return prob

def minimum_faceoffs(prob, slots_vars, teams, slot_ids, limit=1):
    # No team should play another team more than once
    for j in teams:
        for k in teams:
            if j != k:
                prob += (
                    lpSum([slots_vars[i, j, k] for i in slot_ids]) 
                    + lpSum([slots_vars[i, k, j] for i in slot_ids])
                ) >= limit, f"Min_games_between_team_{j}_and_{k}_atleast_{limit}"
    return prob

def limit_faceoffs(prob, slots_vars, teams, slot_ids, limit=1):
    # No team should play another team more than once
    for j in teams:
        for k in teams:
            if j != k:
                prob += (
                    lpSum([slots_vars[i, j, k] for i in slot_ids]) 
                    + lpSum([slots_vars[i, k, j] for i in slot_ids])
                ) <= limit, f"Total_games_between_team_{j}_and_{k}"
    return prob

def limit_3_in_5(prob, days_of_year, working_slots, slots_vars, teams):
    # 3 games in 5 days
    for day in days_of_year:
        this_day = working_slots[working_slots["Day_of_Year"] == day].index
        next_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 1)].index
        third_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 2)].index
        fourth_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 3)].index
        fifth_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 4)].index
        for j in teams:
            prob += (
                (
                    lpSum([slots_vars[i, j, k] for i in this_day for k in teams])  # home team on day
                    + lpSum([slots_vars[i, k, j] for i in this_day for k in teams])  # away team on day
                    + lpSum([slots_vars[i, j, k] for i in next_day for k in teams])  # home team on day+1
                    + lpSum([slots_vars[i, k, j] for i in next_day for k in teams])  # away team on day+1
                    + lpSum([slots_vars[i, j, k] for i in third_day for k in teams])  # home team on day+2
                    + lpSum([slots_vars[i, k, j] for i in third_day for k in teams])  # away team on day+2
                    + lpSum([slots_vars[i, j, k] for i in fourth_day for k in teams])  # home team on day+3
                    + lpSum([slots_vars[i, k, j] for i in fourth_day for k in teams])  # away team on day+3
                    + lpSum([slots_vars[i, j, k] for i in fifth_day for k in teams])  # home team on day+4
                    + lpSum([slots_vars[i, k, j] for i in fifth_day for k in teams])  # home team on day+4
                )
                <= 2,
                f"Max_three_five_{day}_team_{j}",
        )
    return prob

def limit_3_in_6(prob, days_of_year, working_slots, slots_vars, teams):
    # 3 games in 6 days
    for day in days_of_year:
        this_day = working_slots[working_slots["Day_of_Year"] == day].index
        next_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 1)].index
        third_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 2)].index
        fourth_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 3)].index
        fifth_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 4)].index
        sixth_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 5)].index
        for j in teams:
            # This is a bogus hack
            if "02" in j:
                continue
            prob += (
                (
                    lpSum([slots_vars[i, j, k] for i in this_day for k in teams])  # home team on day
                    + lpSum([slots_vars[i, k, j] for i in this_day for k in teams])  # away team on day
                    + lpSum([slots_vars[i, j, k] for i in next_day for k in teams])  # home team on day+1
                    + lpSum([slots_vars[i, k, j] for i in next_day for k in teams])  # away team on day+1
                    + lpSum([slots_vars[i, j, k] for i in third_day for k in teams])  # home team on day+2
                    + lpSum([slots_vars[i, k, j] for i in third_day for k in teams])  # away team on day+2
                    + lpSum([slots_vars[i, j, k] for i in fourth_day for k in teams])  # home team on day+3
                    + lpSum([slots_vars[i, k, j] for i in fourth_day for k in teams])  # away team on day+3
                    + lpSum([slots_vars[i, j, k] for i in fifth_day for k in teams])  # home team on day+4
                    + lpSum([slots_vars[i, k, j] for i in fifth_day for k in teams])  # home team on day+4
                    + lpSum([slots_vars[i, j, k] for i in sixth_day for k in teams])  # home team on day+4
                    + lpSum([slots_vars[i, k, j] for i in sixth_day for k in teams])  # home team on day+4
                )
                <= 2,
                f"Max_three_six_{day}_team_{j}",
        )
    return prob


def no_back_to_back(prob, days_of_year, working_slots, slots_vars, teams):
    # No team can play back to back games
    for day in days_of_year:
        this_day = working_slots[working_slots["Day_of_Year"] == day].index
        next_day = working_slots[working_slots["Day_of_Year"] == str(int(day) + 1)].index
        for j in teams:
            prob += (
                (
                    lpSum([slots_vars[i, j, k] for i in this_day for k in teams])  # home team on day
                    + lpSum([slots_vars[i, k, j] for i in this_day for k in teams])  # away team on day
                    + lpSum([slots_vars[i, j, k] for i in next_day for k in teams])  # home team on day+1
                    + lpSum([slots_vars[i, k, j] for i in next_day for k in teams])  # away team on day+1
                )
                <= 1,
                f"Max_backtoback_{day}_team_{j}",
            )
    return prob

def limit_games_per_day(prob, days_of_year, working_slots, slots_vars, teams, limit=1):
    # No team can play more than $limit game per day
    for day in days_of_year:
        this_day = working_slots[working_slots["Day_of_Year"] == day].index
        for j in teams:
            prob += (
                (
                    lpSum([slots_vars[i, j, k] for i in this_day for k in teams])
                    + lpSum([slots_vars[i, k, j] for i in this_day for k in teams])  # home team on day  # away team on day
                )
                <= limit,
                f"Max_{limit}_games_per_day_{day}_team_{j}",
            )
    return prob

def limit_games_per_week(prob, weeks, working_slots, slots_vars, teams, limit=2):
     # No team can play more than $limit games per week
    for week in weeks:
        slots_in_week = working_slots[working_slots["Week_Name"] == week].index
        for j in teams:
            prob += (
                (
                    lpSum([slots_vars[i, j, k] for i in slots_in_week] for k in teams)
                    + lpSum([slots_vars[i, k, j] for i in slots_in_week] for k in teams)
                )
                <= limit,
                f"Max_{limit}_games_per_week_{week}_team_{j}",
            )
    return prob

def limit_games_per_team(prob, teams, slots_vars, slot_ids, max_games_per_team=11):
    for j in teams:
        prob += (
            lpSum([slots_vars[i, j, k] for i in slot_ids for k in teams])
            + lpSum([slots_vars[i, k, j] for i in slot_ids for k in teams])
        ) >= max_games_per_team, f"max_games_per_team_{j}"
    return prob

def early_starts(prob, teams, slots_vars, early_slots, min=3, max=4):
    for j in teams:
        prob += (
            lpSum([slots_vars[i, j, k] for i in early_slots for k in teams])
            + lpSum([slots_vars[i, k, j] for i in early_slots for k in teams])
        ) >= min, f"min_early_games_for_team_{j}"

        prob += (
            lpSum([slots_vars[i, j, k] for i in early_slots for k in teams])
            + lpSum([slots_vars[i, k, j] for i in early_slots for k in teams])
        ) <= max, f"max_early_games_for_team_{j}"
    return prob

def min_weekends(prob, teams, working_slots, slots_vars, min=1):
    weekends = ["Saturday", "Sunday"]
    weekend_slots = working_slots[working_slots["Day_of_Week"].isin(weekends)].index
    for j in teams:
        prob += (
            (
                lpSum([slots_vars[i, j, k] for i in weekend_slots] for k in teams)  # home team on tepper weekend
                + lpSum([slots_vars[i, k, j] for i in weekend_slots] for k in teams) # away team on tepper weekend
            )
            >= min,
            f"get_weekends_team_{j}",
        )
    return prob

def min_weekday(prob, teams, working_slots, slots_vars, weekday="Monday", min=1):
    days = [weekday]
    weekend_slots = working_slots[working_slots["Day_of_Week"].isin(days)].index
    for j in teams:
        prob += (
            (
                lpSum([slots_vars[i, j, k] for i in weekend_slots] for k in teams)  # home team on tepper weekend
                + lpSum([slots_vars[i, k, j] for i in weekend_slots] for k in teams) # away team on tepper weekend
            )
            >= min,
            f"get_min_day_{weekday}_team_{j}",
        )
    return prob


def max_weekday(prob, teams, working_slots, slots_vars, weekday="Monday", max=1):
    days = [weekday]
    weekend_slots = working_slots[working_slots["Day_of_Week"].isin(days)].index
    for j in teams:
        prob += (
            (
                lpSum([slots_vars[i, j, k] for i in weekend_slots] for k in teams)  # home team on tepper weekend
                + lpSum([slots_vars[i, k, j] for i in weekend_slots] for k in teams) # away team on tepper weekend
            )
            <= max,
            f"get_max_day_{weekday}_team_{j}",
        )
    return prob


def limit_weekday_games_per_week(prob, teams, working_slots, slots_vars, limit=1):
    weeks = working_slots["Week_Name"].unique()

    for week in weeks:
        thisweek = working_slots[working_slots["Week_Name"] == week].index
        slots = working_slots[working_slots["Day_of_Week"].isin(WEEKDAYS)].index

        joined = thisweek.intersection(slots)
        for j in teams:
            prob += (
                (
                    lpSum([slots_vars[i, j, k] for i in joined] for k in teams)
                    + lpSum([slots_vars[i, k, j] for i in joined] for k in teams)
                )
                <= limit,
                f"Max_{limit}_games_per_week_in_{week}_team_{j}",
            )
    return prob


def field_limits(prob, teams, working_slots, slots_vars, field, min, max, variation=""):
    # set limits on field counts
    field_slots = working_slots[working_slots["Full_Field"].isin([field])].index

    for j in teams:
        prob += (
            lpSum([slots_vars[i, j, k] for i in field_slots for k in teams])
            + lpSum([slots_vars[i, k, j] for i in field_slots for k in teams])
        ) >= min, f"min_games_at_{field}_per_team_{j}_{variation}"

        prob += (
            lpSum([slots_vars[i, j, k] for i in field_slots for k in teams])
            + lpSum([slots_vars[i, k, j] for i in field_slots for k in teams])
        ) <= max, f"max_games_at_{field}_per_team_{j}_{variation}"
    return prob


def set_field_ratios(working_slots):
    fields = working_slots["Full_Field"].unique()
    field_ratios = {}
    for field in fields:
        field_mask = working_slots["Full_Field"] == field
        field_ratios[field] = len(working_slots[field_mask]) / len(working_slots)
    return field_ratios


def balance_fields(prob, teams, games_per_team, working_slots, slots_vars, fudge=0):
    field_ratios = set_field_ratios(working_slots)
    for field in field_ratios:
        min = math.floor(field_ratios[field] * games_per_team) - fudge
        max = math.ceil(field_ratios[field] * games_per_team) + fudge
        prob = field_limits(prob, teams, working_slots, slots_vars, field, min, max)
    return prob

def solveMe(prob, working_slots):
    # Solve (quietly)
    print("Solver starting...")
    prob.solve(PULP_CBC_CMD(msg=False))
    print("Solver finished...")
    # Check the solver status
    if LpStatus[prob.status] == "Infeasible":
        print("ERROR: The problem is infeasible")
        dir(prob.status)
        print(working_slots)
        sys.exit(1)
    elif LpStatus[prob.status] == "Optimal":
        print("An optimal solution has been found")
    return prob