import os
import time
import alarm
import board
import displayio
from adafruit_magtag.magtag import MagTag

# --- Configuration (Pulled safely from settings.toml) ---
LAT = os.getenv("LATITUDE")
LON = os.getenv("LONGITUDE")
TIMEZONE = os.getenv("TIMEZONE")

URL = (
    f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}"
    f"&current=temperature_2m,relative_humidity_2m,uv_index,weather_code"
    f"&hourly=temperature_2m,weather_code&temperature_unit=fahrenheit"
    f"&timezone={TIMEZONE}&forecast_days=1"
)

# Initialize MagTag
magtag = MagTag()

# --- HARDWARE DEEP SLEEP CHECK FOR BUTTON PUSH ---
# If the board woke up because you pressed Button A, we can detect it instantly
# right here before it does anything else.
button_woke_us_up = False
if isinstance(alarm.wake_alarm, alarm.pin.PinAlarm):
    print("\n*** Button Press woke the board up! Forced manual refresh. ***")
    button_woke_us_up = True
else:
    print("\n*** Timer alarm woke the board up! Running scheduled update. ***")

#connect to the internet
magtag.network.connect()


# --- WMO Code to Filename Helper ---
def get_icon_name(wmo_code):
    """Maps Open-Meteo WMO codes to base filenames (minus extension/size)"""
    if wmo_code == 0:
        return "sunny"
    elif wmo_code in [1, 2, 3]:
        return "cloudy"
    elif wmo_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "rain"
    elif wmo_code in [71, 73, 75, 77, 85, 86]:
        return "snow"
    elif wmo_code in [95, 96, 99]:
        return "thunderstorm"
    else:
        return "unknown"

# --- Text Layout Configuration ---
magtag.add_text(text_position=(65, 35), text_scale=3)        # Index 0: Main Temp
magtag.add_text(text_position=(175, 20), text_scale=1)       # Index 1: RH
magtag.add_text(text_position=(175, 40), text_scale=1)       # Index 2: UV
magtag.add_text(text_position=(100, 68), text_scale=1)        # Index 3: Date

# Bottom Timeline Text Layout (6 Columns)
labels = ["6-9a", "9-12p", "12-3p", "3-6p", "6-9p", "9-12a"]
hourly_ranges = [
    (6, 9), (9, 12), (12, 15), (15, 18), (18, 21), (21, 24)
]
start_x = 13
column_width = 48
y_time_label = 85   # Nudged up slightly for image clearance
y_temp_label = 120  # Nudged up slightly for image clearance

for i, label in enumerate(labels):
    magtag.add_text(text_position=(start_x + (i * column_width), y_time_label), text_scale=1) 
    magtag.add_text(text_position=(start_x + (i * column_width), y_temp_label), text_scale=1) 

# --- Graphics / Icon Layout Configuration ---
main_group = displayio.Group()
magtag.graphics.splash.append(main_group)

# ---- MAIN EXECUTION BLOCK ----
try:
    print("Retrieving data...")
    response = magtag.network.fetch(URL)
    weather_data = response.json()
    # Read the data safely into JSON directly
    print("Data safely retrieved!") 
    
    # 2. Parse Current Weather
    current = weather_data["current"]
    curr_temp = int(round(current["temperature_2m"]))
    curr_hum = current["relative_humidity_2m"]
    curr_uv = current["uv_index"]
    current_wmo = current["weather_code"]
    
    # 1. Grab the raw date string (e.g., "2026-06-28")
    raw_date = current["time"].split("T")[0]
    year, month_num, day = raw_date.split("-")
    
    # 2. Map month numbers to their full text names
    months = {
        "01": "January", "02": "February", "03": "March", "04": "April",
        "05": "May", "06": "June", "07": "July", "08": "August",
        "09": "September", "10": "October", "11": "November", "12": "December"
    }
    
    # 3. Clean up the day string (remove any leading zero, e.g., "05" becomes "5")
    clean_day = str(int(day))
    
    # 4. Format into "Month DD, YYYY"
    formatted_date = f"{months[month_num]} {clean_day}, {year}"
    
    # Update text buffers
    magtag.set_text(f"{curr_temp} F", index=0, auto_refresh=False)
    magtag.set_text(f"RH: {curr_hum}%", index=1, auto_refresh=False)
    magtag.set_text(f"UV Index: {curr_uv}", index=2, auto_refresh=False)
    
    # Send our beautifully formatted date to index 3!
    magtag.set_text(formatted_date, index=3, auto_refresh=False)

    # Load Main Weather Icon
    main_icon_file = f"/icons/{get_icon_name(current_wmo)}.bmp"
    print(f"Loading main icon: {main_icon_file}")
    try:
        main_icon_bg = displayio.OnDiskBitmap(main_icon_file)
        main_icon_sprite = displayio.TileGrid(main_icon_bg, pixel_shader=main_icon_bg.pixel_shader)
        main_icon_sprite.x = 10
        main_icon_sprite.y = 10
        main_group.append(main_icon_sprite)
    except Exception as icon_err:
        print("Couldn't load main icon:", icon_err)

    # Parse Timeline Weather
    hourly = weather_data["hourly"]
    text_index_offset = 4 
    
    for i, (start_hour, end_hour) in enumerate(hourly_ranges):
        temp_slice = hourly["temperature_2m"][start_hour:end_hour]
        wmo_slice = hourly["weather_code"][start_hour:end_hour]
        avg_temp = int(round(sum(temp_slice) / len(temp_slice)))
        
        ts_codes    = [95, 96, 99]
        snow_codes  = [71, 73, 75, 77, 85, 86]
        rain_codes  = [51, 53, 55, 61, 63, 65, 80, 81, 82]
        
        if any(code in ts_codes for code in wmo_slice):
            timeline_wmo = 95  
        elif any(code in snow_codes for code in wmo_slice):
            timeline_wmo = 71  
        elif any(code in rain_codes for code in wmo_slice):
            timeline_wmo = 61  
        else:
            timeline_wmo = wmo_slice[1] 
            
        magtag.set_text(labels[i], index=text_index_offset, auto_refresh=False)
        magtag.set_text(f"{avg_temp}o", index=text_index_offset + 1, auto_refresh=False)
        text_index_offset += 2
        
        timeline_icon_file = f"/icons/{get_icon_name(timeline_wmo)}_small.bmp"
        try:
            time_icon_bg = displayio.OnDiskBitmap(timeline_icon_file)
            time_icon_sprite = displayio.TileGrid(time_icon_bg, pixel_shader=time_icon_bg.pixel_shader)
            time_icon_sprite.x = start_x + (i * column_width)  
            time_icon_sprite.y = 94 
            main_group.append(time_icon_sprite)
        except Exception as icon_err:
            print(f"Couldn't load timeline icon {timeline_icon_file}:", icon_err)

    # --- TRIGGER HARDWARE DISPLAY REFRESH ---
    print("Refreshing e-ink display screen now...")
    magtag.display.refresh()
    print("Refresh complete!")
    
except Exception as e:
    print("--- CRASH DETECTED ---")
    print("Error Type:", type(e).__name__)
    print("Error Message:", str(e))
    print("----------------------")

# --- ENTER DEEP SLEEP (BATTERY SAVING SAVIOR) ---
print("Going into deep sleep mode to save battery...")

#  Force release Button A from MagTag's internal peripheral system
# This prevents the "Pin in use" conflict entirely!
magtag.peripherals.buttons[0].deinit()

# 1. Set up a timer alarm to wake us up in 15 minutes (900 seconds)
time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 900)

# 2. Set up a pin alarm to wake us up immediately if Button A (D11) is pressed
# (Since MagTag buttons use Pull-Up resistors, a press pulls the pin LOW/False)
button_alarm = alarm.pin.PinAlarm(pin=board.BUTTON_A, value=False, pull=True)

# If the user just manually pushed the button, pause briefly so they can release it
if button_woke_us_up:
    time.sleep(2)

# 3. Put the board to sleep. This powers off the CPU until an alarm trips!
alarm.exit_and_deep_sleep_until_alarms(time_alarm, button_alarm)