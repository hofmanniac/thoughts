from datetime import date, datetime, timedelta
from thoughts import context as ctx

def process(command, context):
    
    base_date = command["#date"]
    
    if base_date == "@today": 
        base_date = datetime.today()
    elif base_date == "@yesterday":
        base_date = datetime.today() + timedelta(days=-1)
    elif base_date == "@tomorrow":
        base_date = datetime.today() + timedelta(days=1)

    if "timezone" in command:
        timezone = command["timezone"]
        if (timezone != "0"):
            num_hours = int(timezone)
            base_date = datetime.utcnow()
            base_date = base_date + timedelta(hours=num_hours)

    if "locale" in command:
        locale_val = command["locale"]
        import locale
        locale.setlocale(locale.LC_TIME, locale_val)

    if "format" in command:
        format = command["format"]
        result = base_date.strftime(format)
    else:
        result = base_date.strftime("%B %d, %Y")

    ctx.RulesContext.store_item(context, command, result)

    return result