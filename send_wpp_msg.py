import pywhatkit
import datetime as dt
import pandas as pd
import time

def get_hour_minute():
    now = dt.datetime.now()
    if now.minute < 60:
        hour = now.hour
        if now.second < 30:
            minute = now.minute + 1
        else:
            minute = now.minute + 2
    else:
        if hour < 24:
            hour = now.hour + 1
            minute = 0
        else:
            hour = 0
            minute = 0

    return hour, minute

def generate_msg(df):
    if not df.empty:
        df_str = df.to_string(index=False, header=False, justify='left')
        str = f"Novas musicas da NCS saindo do forno!\n{df_str}\nBora dar um salve!"
    else:
        str = "Sem novos lançamentos da NCS por agora. Assim que lançarem aviso aqui!"

    return str

def send_wpp_msg(group_id, str, hour, minute):
    sent = False
    while not sent:
        try:
            pywhatkit.sendwhatmsg_to_group(group_id, str, hour, minute, tab_close=True)
            sent = True
        except:
            time.sleep(5)

def generate_send_wpp_msg(df):
    group_id = 'GfQhTsAR1K9Gs7QJgiOjTy'
    hour, minute = get_hour_minute()
    str = generate_msg(df)
    send_wpp_msg(group_id, str, hour, minute)
    

if __name__ == "__main__":
    generate_send_wpp_msg(df=pd.DataFrame())

