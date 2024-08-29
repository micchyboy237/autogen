from datetime import datetime, timedelta
import calendar
import requests

# Constants based on the provided schedule and hourly rate
WEEKLY_SCHEDULE = {
    'Monday': 6.5,
    'Tuesday': 6.5,
    'Thursday': 7
}
HOURLY_RATE = 15


def calculate_cutoff_salary(start_date, end_date):
    """
    Calculates the total salary for the given cutoff period based on the weekly schedule and hourly rate.

    :param start_date: The start date of the cutoff period.
    :param end_date: The end date of the cutoff period.
    :return: The total salary for the period.
    """
    total_hours = 0
    current_date = start_date

    while current_date <= end_date:
        weekday = current_date.strftime('%A')
        if weekday in WEEKLY_SCHEDULE:
            total_hours += WEEKLY_SCHEDULE[weekday]
        current_date += timedelta(days=1)

    return total_hours * HOURLY_RATE


def get_cutoff_dates(start_date):
    """
    Gets the cutoff start and end dates for the given start date.

    :param start_date: The start date to calculate the cutoff.
    :return: A tuple of (start_date, end_date) for the cutoff period.
    """
    day = start_date.day
    month = start_date.month
    year = start_date.year

    if day <= 14:
        start_cutoff = datetime(year, month, 1)
        end_cutoff = datetime(year, month, 14)
    else:
        start_cutoff = datetime(year, month, 15)
        last_day = calendar.monthrange(year, month)[1]
        end_cutoff = datetime(year, month, last_day)

    return start_cutoff, end_cutoff


def get_next_cutoff_dates(current_start, current_end):
    """
    Calculates the next cutoff dates based on the current cutoff dates.

    :param current_start: The start date of the current cutoff.
    :param current_end: The end date of the current cutoff.
    :return: A tuple of (next_start, next_end) for the next cutoff period.
    """
    if current_start.day == 1:  # Current cutoff is 1 - 14
        next_start = datetime(current_start.year, current_start.month, 15)
        next_end = datetime(current_start.year, current_start.month,
                            calendar.monthrange(current_start.year, current_start.month)[1])
    else:  # Current cutoff is 15 - end of the month
        next_month = current_start.month + 1 if current_start.month < 12 else 1
        next_year = current_start.year + 1 if next_month == 1 else current_start.year
        next_start = datetime(next_year, next_month, 1)
        next_end = datetime(next_year, next_month, 14)

    return next_start, next_end


def convert_to_php(amount_gbp):
    """
    Converts the given amount from GBP to PHP using the latest conversion rate from the Frankfurter API.

    :param amount_gbp: The amount in GBP to be converted.
    :return: The equivalent amount in PHP and the conversion rate.
    """
    # Get today's date in the format YYYY-MM-DD
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.frankfurter.app/{today}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        rate = data['rates']['PHP'] / data['rates']['GBP']
        return amount_gbp * rate, rate
    except requests.exceptions.RequestException as e:
        print(f"Error fetching conversion rate: {e}")
        return 0, 0


def salary_calculator(cutoffs):
    """
    Calculates the total salary for the given number of cutoffs starting from the current date's cutoff period.

    :param cutoffs: Number of salary cutoffs to calculate.
    """
    current_date = datetime.now()
    results = []
    total_salary = 0
    total_salary_php = 0

    # Determine the current cutoff period
    current_start, current_end = get_cutoff_dates(current_date)

    for i in range(cutoffs):
        # Calculate the total salary for the current cutoff
        salary_gbp = calculate_cutoff_salary(current_start, current_end)
        salary_php, conversion_rate = convert_to_php(salary_gbp)
        results.append((current_start, current_end, salary_gbp, salary_php))
        total_salary += salary_gbp
        total_salary_php += salary_php

        # Get the next cutoff period
        current_start, current_end = get_next_cutoff_dates(
            current_start, current_end)

    # Output the results
    for start, end, salary_gbp, salary_php in results:
        print(f"Cutoff: {start.strftime('%B %d')} - {end.strftime('%d')}")
        print(
            f"Total Salary: £{salary_gbp:.2f} / ₱{salary_php:.2f} (Conversion rate: 1 GBP = {conversion_rate:.2f} PHP)\n")

    print(
        f"Total Salary for all cutoffs: £{total_salary:.2f} / ₱{total_salary_php:.2f}")


# Example usage
if __name__ == "__main__":
    cutoffs_count = int(input("Enter the number of salary cutoffs: "))
    salary_calculator(cutoffs_count)
