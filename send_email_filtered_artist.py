import pandas as pd
import datetime as dt

def parse_release_date_to_date(row):
    date_dict = {'Jan':1, 'Feb':2, 'Mar':3, 'Apr':4, 'May':5, 'Jun':6, 'Jul':7, 'Aug':8, 'Sept':9, 'Oct':10, 'Nov':11, 'Dec':12}
    date_str = row['release_date']

    if "Premiered on" in date_str:
        date_str = date_str[len("Premiered on")+1:]


    splt_date_info = date_str.split(' ')

    print(f"date_str -> {date_str}")
    year = int(splt_date_info[2])
    month = int(date_dict[splt_date_info[1]])
    day = int(splt_date_info[0])

    date = dt.datetime(year, month, day)

    row['birthday'] = date

    return row

def filter_artists(df, artists):
    df_list = []
    for artist in artists:
        df_aux = df[df['title'].str.contains(artist)]
        df_list.append(df_aux)

    df_artists = pd.concat(df_list)

    df_artists = df_artists.sort_values(by=['birthday'])
    df_artists = df_artists.reset_index(drop=True)
    artists_names = '-'.join(artists)
    df_artists.to_excel(f'{artists_names}.xlsx')



def main():
    artists = ['Rival', 'Cadmium', 'Cartoon']
    df = pd.read_excel("nocopyrightsounds-2023-03-22.xlsx")
    df = df.apply(lambda row: parse_release_date_to_date(row), axis=1)
    filter_artists(df, artists)

if __name__ == "__main__":
    main()