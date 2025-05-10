def format_datetime(start_datetime):
    year = str(start_datetime.year)
    month = start_datetime.month
    day_of_month = start_datetime.day
    if month < 10:
        month_string = "0" + str(month)
    else:
        month_string = str(month)
    if day_of_month < 10:
        day_of_month_as_string = "0" + str(day_of_month)
    else:
        day_of_month_as_string = str(day_of_month)
    
    hour = start_datetime.hour
    minute = start_datetime.minute
    second = start_datetime.second
    if hour < 10:
        hour_as_string = "0" + str(hour)
    else:
        hour_as_string = str(hour)
    if minute < 10:
        minute_as_string = "0" + str(minute)
    else:
        minute_as_string = str(minute)
    if second < 10:
        second_as_string = "0" + str(second)
    else:
        second_as_string = str(second)

    return year + month_string + day_of_month_as_string + "T" + hour_as_string + minute_as_string + second_as_string + "\n"