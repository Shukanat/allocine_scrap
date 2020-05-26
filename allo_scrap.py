import requests
import bs4
import pandas as pd
import re
import time
import pickle
import sys
import argparse
import os

parser = argparse.ArgumentParser(description='Allo-ciné scraper')
parser.add_argument('--pages', default=5, type=int, help='Nombre de pages à scraper')
parser.add_argument('--csv_name', default='allo_cine.csv', type=str, help='Nom de fichier final')
args = parser.parse_args()

def is_the_only_string_within_a_tag(s):
    """Return True if this string is the only child of its parent tag."""
    return (s == s.parent.string)

def get_pages(token, nb):
    pages = []
    for i in range(1,nb+1):
        j = token + str(i)
        pages.append(j)
    return pages

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """see ref: https://gist.github.com/aubricus/f91fb55dc6ba5557fbab06119420dd6a"""
    
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix),),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()
    
def scrap_allo(soup):
    
    data={}
    regex_time = re.compile(r'\d+?h|\d+?min')
    
    # extraction de titres
    titres = soup.find_all("a", {"class":"meta-title-link"})
    titres = [titre.get_text() for titre in titres]
    data["titre"] = titres
    
    # note de presses
    film_list = soup.find_all("div", {"class":"card entity-card entity-card-list cf"})
    notes_de_press=[]
    for press in film_list:
        if len(press.find_all('span', text=" Presse ")) == 0:
            notes_de_press.append('Pas de press')
        else:
            note=press.find_all('span', text=" Presse ")[0].find_parent("div").find("span",{"class":"stareval-note"}).get_text()
            notes_de_press.append(note)
    data["press"] = notes_de_press

    # note de spectateurs
    notes_de_spectator=[]
    for press in film_list:
        if len(press.find_all('span', text=" Spectateurs ")) == 0:
            notes_de_spectator.append('Pas de note')
        else:
            note=press.find_all('span', text=" Spectateurs ")[0].find_parent("div").find("span",{"class":"stareval-note"}).get_text()
            notes_de_spectator.append(note)
    data["spectateurs"]=notes_de_spectator

    # dates
    film_info=soup.find_all("div", {"class":"meta-body-item meta-body-info"})
    dates=[]
    for date in film_info:
        if len(date.find_all("span", {"class":"date"})) == 0:
            dates.append('Inconnu')
        else:
            dates.append(date.find_all("span", {"class":"date"})[0].get_text())
    data["date"]=dates

    # durée
    time=[]
    for film in film_info:
        if len(regex_time.findall(film.text)) == 0:
            time.append("Pas d'info")
        else:
            time.append(' '.join(regex_time.findall(film.text)))
    data["time"]=time

    # realisateur
    realiz=[]
    for realiz_name in film_list:
        if len(realiz_name.find_all("div", {"class":"meta-body-item meta-body-direction light"})) == 0:
            realiz.append("Pas d'info")
        else:
            list_of_realiz = realiz_name.find_all("div", {"class":"meta-body-item meta-body-direction light"})
            for name in list_of_realiz:
                string=name.get_text()
                string=string.replace('De','')
                string=string.strip()
                realiz.append(string)
    data["realis"]=realiz

    # acteurs
    list_of_actors=[]
    for film_actors in film_list:
        if len(film_actors.find_all('div', {"class":"meta-body-item meta-body-actor light"})) == 0:
            list_of_actors.append("Pas d'info")
        else:
            actors=film_actors.find_all("div", {"class":"meta-body-item meta-body-actor light"})
            for actor in actors:
                string = ', '.join(actor.find_all(string=is_the_only_string_within_a_tag)[1:])
                list_of_actors.append(string)
    data["actors"]=list_of_actors

    # genres
    genres=soup.find_all("div", {"class":"meta-body-item meta-body-info"})
    list_of_genres=[]
    for genre in genres:
        if len(genre.find_all("span")) < 4:
            list_of_genres.append(', '.join([span.get_text() for span in genre.find_all("span")[2:]]))
        else:
            list_of_genres.append(', '.join([span.get_text() for span in genre.find_all("span")[3:]]))
    data["genre"]=list_of_genres

    # resume
    texts=[]
    for text in film_list:
        if len(text.find_all('div', {"class":"content-txt"})) == 0:
            texts.append('Pas de text')
        else:
            text=text.find_all('div', {"class":"content-txt"})[0].get_text()
            texts.append(text)

    pretty_text=[]       
    for text in texts:
        text.replace('/\n',' ')
        pretty_text.append(text.strip())
    data["resume"]=pretty_text
    
    return data

if __name__ == '__main__':
    
    token='http://www.allocine.fr/films/?page='
    pages = get_pages(token, args.pages)
    full_df=pd.DataFrame()

    print_progress(0, len(pages), prefix = 'Progress:', suffix = 'Complete', decimals=1, bar_length=50)
    for i, page in enumerate(pages):
        # récuperation et lecture de la page
        resp = requests.get(page)
        soup = bs4.BeautifulSoup(resp.text, 'html.parser')
        data=scrap_allo(soup)
        df=pd.DataFrame.from_dict(data)
        full_df=full_df.append(df, ignore_index=True)
        time.sleep(2)
        print_progress(i+1, len(pages), prefix = 'Progress:', suffix = 'Complete', decimals=1, bar_length=50)

    #full_df.to_csv(args.csv_name)
    print('File downloaded to: ' + os.getcwd() + '/' + args.csv_name)
