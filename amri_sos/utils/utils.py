def get_25y_from_now():
    import datetime
    current_year = datetime.datetime.now().year
    dob = '1/1/{}'.format(current_year - 25)
    return dob
