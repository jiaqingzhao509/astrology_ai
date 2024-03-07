from datetime import datetime, timedelta
import pytz
import swisseph as swe
from geopy.geocoders import Nominatim
from collections import defaultdict

# data altering
def to_jd_ut(birth_date, birth_time, timezone_pytz):
    # Convert birth date and time to UTC
    if isinstance(birth_date, str): 
        birth_datetime = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
    else:
        time_object = datetime.strptime(birth_time, "%H:%M").time()
        birth_datetime = datetime.combine(birth_date, time_object)
    local_timezone = pytz.timezone(timezone_pytz)  # Replace with the correct timezone
    birth_datetime = local_timezone.localize(birth_datetime)
    birth_datetime_utc = birth_datetime.astimezone(pytz.utc)

    # Calculate Julian Day for the birth date and time
    jd_ut = swe.julday(birth_datetime_utc.year, birth_datetime_utc.month, 
                          birth_datetime_utc.day, birth_datetime_utc.hour + 
                          (birth_datetime_utc.minute / 60)) 
    return jd_ut


# dates
def get_solar_return (jd_birth, birth_date, year):

    # Get natal Sun position
    natal_sun_position = swe.calc_ut(jd_birth, swe.SUN)[0][0]

    birth_datetime = datetime.strptime(f"{birth_date}", "%Y-%m-%d")

    # Find the Solar Return
    for day in range(365):  # Check each day of the year
        jd = swe.julday(year, birth_datetime.month, birth_datetime.day + day, 0)
        sun_position = swe.calc_ut(jd, swe.SUN)[0][0]
        if sun_position >= natal_sun_position:
            # Approximate time of Solar Return
            solar_return_time = jd
            break
    return solar_return_time


def get_lunar_return(natal_info, start_date):
    natal_moon_deg = natal_info['MOON'][2]  # Leo 29°01'

    # Convert natal degree to 360° format
    natal_moon_long = 120 + natal_moon_deg  # Leo starts at 120°

    # Function to find next Moon return
    def find_moon_return(start_date, natal_moon_long):

        date = datetime.strptime(start_date, "%Y-%m-%d")
        init_year = date.year
        counter = 0
        marker = 1
        dates = []
        while date.year <= init_year:
            jd = swe.julday(date.year, date.month, date.day)
            transiting_moon = swe.calc_ut(jd, swe.MOON)[0][0]
            #print(transiting_moon, natal_moon_long)
            if round(transiting_moon, 6) < round(natal_moon_long, 6) and marker == 1:
                marker = 0
            elif round(transiting_moon, 6) >= round(natal_moon_long, 6) and marker == 0: 
                marker = 1
                dates.append(date.strftime("%Y-%m-%d"))
                counter += 1
            else: 
                pass
            date += timedelta(days=1)
        return dates

    # Find next Moon return
    moon_return_date = find_moon_return(start_date, natal_moon_long)
    return moon_return_date

# house info
def astro_charts(jd_ut, latitude, longitude):

    
    # Planet names & zodiac dictionaris
    planet_names = ["SUN", "MOON", "MERCURY", "VENUS", "MARS", "JUPITER", "SATURN", "URANUS", "NEPTUNE", "PLUTO"]
    zodiac_dict_zero_based = {
        0: 'Aries',
        1: 'Taurus',
        2: 'Gemini',
        3: 'Cancer',
        4: 'Leo',
        5: 'Virgo',
        6: 'Libra',
        7: 'Scorpio',
        8: 'Sagittarius',
        9: 'Capricorn',
        10: 'Aquarius',
        11: 'Pisces'
    }

    # Prepare planet location & repective zodiac signs
    planets = {}
    zodiacs = {}
    for i in range(0,10):
        planets[planet_names[i]] = swe.calc_ut(jd_ut, i)[0][0] #% 30
        zodiacs[planet_names[i]] = zodiac_dict_zero_based[int(swe.calc_ut(jd_ut, i)[0][0]/30)]

    # Generate house info
    house_cusps, ascmc = swe.houses(jd_ut, latitude, longitude, b'P')
    #print(house_cusps)

    # Determine house positions of planets
    planet_houses = {}
    house_id = {}
    for i in range(0,12):
        house_id[i] = house_cusps[i] 
    
    
    house_sorted = dict(sorted(house_id.items(), key=lambda item: item[1]))
    #print(house_sorted)
    for planet, position in planets.items():
            planet_houses[planet] = list(house_sorted.keys())[-1] + 1
            for i, cusp in house_sorted.items():  # Start from the 2nd house
                if position < cusp and position >= min(house_cusps) and position <= max(house_cusps):
                    if i != 0:
                        planet_houses[planet] = i
                    else:
                        planet_houses[planet] = 12
                    break
    #Join all info
    joined_astro_info = defaultdict(list)
    planets.update({n: planets[n] % 30 for n in planets.keys()})
    for d in (planet_houses, zodiacs, planets): # you can list as many input dicts as you want here
        for key, value in d.items():
            joined_astro_info[key].append(value)
    
    return joined_astro_info, [zodiac_dict_zero_based[int(ascmc[0] / 30)], ascmc[0] % 30] 


# generate 2 years worth of info

def get_yearly_info(year, timezone_pytz, latitude, longitude, natal_info, birth_date, birth_time):
    years = [str(year)] #, str(int(year) + 1) ]
    years_dict = {}
   
    for y in years:
        y_date = y  + "-01-01"
        #year_start chart
        #year_info, ignore  = astro_charts(to_jd_ut(y_date, "00:00", timezone_pytz), latitude, longitude)

        #lunar return charts
        lunar_return_dates = get_lunar_return(natal_info, y_date)
        lunar_returns = {}
        for i in lunar_return_dates:
            lunar_returns[i] = astro_charts(to_jd_ut(i, "00:00", timezone_pytz), latitude, longitude)[0]

        #solar return charts
        # {"January 1st info" : year_info}
        solar_return_jd = get_solar_return(to_jd_ut(birth_date, birth_time, timezone_pytz), birth_date, int(y))
        solar_return, ignore = astro_charts(solar_return_jd, latitude, longitude)
        years_dict[y] = [{"Lunar return dates/charts":lunar_returns}, {"Solar return chart":solar_return}]
    return solar_return, years_dict