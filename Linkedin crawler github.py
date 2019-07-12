# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 17:53:40 2019

@author: zhuoli

Today update: maybe I could login the Linkedin account manually, and then search for the people I need
"""

#packages
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from selenium import webdriver
from time import sleep
import pickle
import os
from fake_useragent import UserAgent
import random
from parsel import Selector

#set path
os.chdir(r"C:\mypath")


#******************************************************************************
""" 
This part prepares for searching on Linkedin: sincec we cannot search people directly 
on LinkedIn due to account limitation, we change to search "APPLE linkedin+ ruler name" on 
Google, and save the links containing "linkedin". The result is saved as google_ruler.csv
"""
#******************************************************************************
# import APPLE ruler name
ruler = pd.read_csv("raw\APPLE_rules_with_author_names.csv")

# save rulers whose linkedin urls are successfully scrapied from Google
google_ruler=pd.DataFrame(columns=('Date','Release No.','Rule Name','URL','FK Score','Names','Google URL'))
# rulers remain to be searched
google_ruler_todo=ruler

# For most linkedin href, they are contained in a string have such format 
# <cite class="iUh30">https://www.linkedin.com/in/jerry-marlatt-90683212</cite>
# so we use href_extract (with re.findall below) to get the content we need
href_extract=r'<cite class="iUh30">(.*?)</cite>' 

# get some IP from "https://free-proxy-list.net/"
# because Google would block your request once you search too many people using the same IP
# here my solution is: change VPN account every 200 ruler

# ruler number, 1885
rulernbr=ruler['Names'].shape[0]

#change VPN account whenever SSLError happens
t=0

for i in range(t,rulernbr):
    # set random header to simulate browsers. Google would find out robots without headers
    header={"User-Agent":UserAgent().random}
    
    # use "t" to get the index where last error happens
    t=i

    # search the people in dataframe
    url="https://google.com/search?q=APPLE+linkedin+"+ruler['Names'][i]
    s=requests.get(url,headers=header)
    soup=BeautifulSoup(s.text)
    
    # when Google block us
    changevpn="Sometimes you may be asked to solve the CAPTCHA if you are using advanced terms that robots are known to use, or sending requests very quickly."
    if changevpn in str(soup):
        break
    
    # obs in the dataframe
    temp=ruler.iloc[i:i+1,:]

    # iUh30 is linkedin label, use this to pinpoint linkedin website
    content=soup.find_all('cite',class_="iUh30")
    
    effect_obs=0
    # for every item in the content, save href from Linkedin
    for urls in content:   
        # use href_extract to match the href
        href_save = re.findall(href_extract, str(urls), re.S | re.M)
        if href_save==[]:
            pass
        else:
            effect_obs+=1
            href_save=href_save[0].replace("\"","")
            # filter those unrelated to Linkedin
            if 'linkedin' in href_save:
                # append the finished ruler into google_ruler
                google_ruler=google_ruler.append(temp,ignore_index=True)
                google_ruler.iat[google_ruler.shape[0]-1,2]=href_save
                # see the where the process has been
                print(str(i)+":"+str(effect_obs))
        
    # delete the finished ruler from google_ruler_todo
    google_ruler_todo=google_ruler_todo.drop(index=[i])
    
    # save data google_ruler/google_ruler_todo
    output=open(r'final\google_ruler','wb')
    pickle.dump(google_ruler,output)
    output.close() 
    output=open(r'final\google_ruler_todo','wb')
    pickle.dump(google_ruler_todo,output)
    output.close()
    
    print(i)
    sleep(1)

# export as csv file
google_ruler.to_csv(r'final\google_ruler.csv')
#******************************************************************************




#******************************************************************************
#packages
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from selenium import webdriver
from time import sleep
import pickle
import os
from fake_useragent import UserAgent
import random
from parsel import Selector

#set path
os.chdir(r"C:\mypath")

# open the selenium webdriver, and login in manually
driver = webdriver.Chrome(r"C:\Users\zhuoli\AppData\Local\Google\Chrome\Application\chromedriver")
driver.get('https://www.linkedin.com/')

# import Linkedin urls
rulerurl = pd.read_excel(r'final\google_ruler.xlsx',sheetname=[0])[0]
# save rulers whose linkedin urls are successfully scrapied from Google
linkedin=pd.DataFrame(columns=('myindex','Date','FK Score','Names','Release No.','Rule Name','URL','Google URL','n','Company','Title','Time'))
# rulers remain to be searched
linkedin_todo=rulerurl
rulerurl['state']='drop'
# Since google is powerful enough, those urls ranked after top 5 are not likely to be right pages
templist=linkedin_todo[(linkedin_todo.n>5)].index.tolist()
linkedin_todo=linkedin_todo.drop(index=templist)
linkedin_todo=linkedin_todo.rename(columns={'index':'myindex'})

# read linkedin file
pkl_file=open(r'final\linkedin','rb')
linkedin=pickle.load(pkl_file)
pkl_file.close()

# core function defined
def get_data(df):
    # to save contents
    content=pd.DataFrame(columns=('myindex','Date','FK Score','Names','Release No.','Rule Name','URL','Google URL','n','Company','Title','Time','Linkedin Name'))

    # google url
    url=df.iat[0,7]
    # ruler name: to check if it is the right website
    name_url=df.iat[0,3]
    firstname=name_url.split()[0]
    lastname=name_url.split()[-1]
    
    # login in!
    driver.get(url)

    # match ruler name
    text=driver.page_source
    soup=BeautifulSoup(text)
    name_=soup.find_all('li',class_="inline t-24 t-black t-normal break-words")
    if name_==[]:
        return 0
    name_extract=r'<li .*?>(.*?)</li>' 
    name= re.findall(name_extract, str(name_), re.S | re.M)[0].strip()
    content['Linkedin Name']=name
    firsttocheck=name.split()[0]
    lasttocheck=name.split()[-1]
    
    # if the name on the website does not match with the name in database, return 0
    # First Last, sometimes it could be Last, First
    # usually, a name containing "," would be very special, let's leave it aside
    # names with more than 3 contents are complicated
    if "," not in name_url:
        if len(name_url.split())<3:
            if firsttocheck==firstname:
                if lasttocheck==lastname:
                    pass
                else:
                    return 0
            else:
                 if firsttocheck==lastname:
                     if lasttocheck==firstname: 
                         pass
                     else:
                         return 0
    
    # click all the bottons like "Show 1 more role/Show 3 more education"
    while(1>0):
        try:
            driver.find_element_by_css_selector("[class='pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link']").click()            
        except:
            break
    
    # get the page code
    sleep(3)
    stopwhile=0
    text=driver.page_source
    soup=BeautifulSoup(text)
    while(soup==[] and stopwhile<=5):
        text=driver.page_source
        soup=BeautifulSoup(text)
        stopwhile+=1
        
    # match experience
    # lock the whole experience part
    experience_=soup.find_all('section',id="experience-section")
    # import jobs one by one  
    jobs1=experience_[0].find_all('li',class_="pv-profile-section__card-item-v2 pv-profile-section pv-position-entity ember-view")
    jobs2=experience_[0].find_all('li',class_="pv-profile-section__sortable-card-item pv-profile-section pv-position-entity ember-view")
    jobs=jobs1+jobs2
    # there are two sets of experience: (1) simple: the ruler only have one title in the
    # company; (2) complicated: the ruler have more than one titles during in the company
    # use company name to distinguish them.
    
    for job in jobs:
        # (1) simple
        temp=job.find_all('span',class_="pv-entity__secondary-title")
        if temp!=[]:    
            #company name
            # company name is included in <h3>
            temp=job.find_all('h3',class_="t-16 t-black t-bold")
            # use regular expression to extract company information
            _extract=r'<h3 .*?>(.*?)</h3>' 
            if temp==[]:
                company_name=''
            else:
                name= re.findall(_extract, str(temp[0]), re.S | re.M)
                # delete "\n"(etc.) in the name; and also, linkedin use "&amp" to denote "&"
                company_name=name[0].strip().replace("&amp;","&")
            
            # job title
            temp=job.find_all('span',class_="pv-entity__secondary-title")
            # use regular expression to extract company information
            _extract=r'<span .*?>(.*?)</span>' 
            if temp==[]:
                title=''
            else:
                name= re.findall(_extract, str(temp[0]), re.S | re.M)
                # delete "\n"(etc.) in the name; and also, linkedin use "&amp" to denote "&"
                title=name[0].strip().replace("&amp;","&")
            
            # time span
            temp=job.find_all('h4',class_="pv-entity__date-range t-14 t-black--light t-normal")
            if temp==[]:
               temp=job.find_all('h4',class_="pv-entity__date-range t-14 t-black t-normal") 
            # use regular expression to extract company information
            _extract=r'<span>(.*?)</span>' 
            if temp==[]:
                time=''
            else:
                name= re.findall(_extract, str(temp[0]), re.S | re.M)
                # delete "\n"(etc.) in the name; and also, linkedin use "&amp" to denote "&"
                time=name[0].strip().replace("&amp;","&")
            
            df['Company']=company_name
            df['Title']=title
            df['Time']=time
            content=content.append(df,ignore_index=True)
            
        # (2) complicated
        else:
            #company name
            # company name is included in <h3>
            temp=job.find_all('h3',class_="t-16 t-black t-bold")
            # use regular expression to extract company information
            _extract=r'<span>(.*?)</span>' 
            name= re.findall(_extract, str(temp[0]), re.S | re.M)
            # delete "\n"(etc.) in the name; and also, linkedin use "&amp" to denote "&"
            company_name=name[0].strip().replace("&amp;","&")
            
            # job title
            alltitle=job.find_all('div',class_="pv-entity__role-details")
            # use regular expression to extract company information
            _extract=r'<span>(.*?)</span>' 
            
            for eachtitle in alltitle:
                infolist= re.findall(_extract, str(eachtitle), re.S | re.M)
                # delete "\n"(etc.) in the name; and also, linkedin use "&amp" to denote "&"
                infolist+=['','']
                title=infolist[0]
                time=infolist[1]
                
                # add observations 
                df['Company']=company_name
                df['Title']=title
                df['Time']=time             
                content=content.append(df,ignore_index=True)
    
    return content

case=0
timestop=0
# iterate the urls in linkedin_todo
while(linkedin_todo.shape[0]>0):
    timestop+=1
    if timestop>0 and isinstance(timestop/100,int):
        sleep(120)

    print(linkedin_todo.iat[0,0])
    # use date and name to lock in one ruler
    name_todo=linkedin_todo.iat[0,3]
    date_todo=linkedin_todo.iat[0,1]
    
    
    # tempdf have all urls for one ruler
    templist=linkedin_todo[(linkedin_todo.Date==date_todo)&(linkedin_todo.Names==name_todo)].index.tolist()
    tempdf=linkedin_todo.loc[templist,:]
    
    dfrow=tempdf.shape[0]
    for row in range(dfrow):
        dftotry=tempdf.iloc[row:row+1,:]
        # a self-defined function
        # if the url passes, then get_data
        try:
            # get_data return a dataframe containing experience list
            content=get_data(dftotry)
            sleep(random.randint(1,5))
        except:
            content=0
        
        if isinstance(content,int):
            tempdroplist=linkedin_todo[(linkedin_todo.myindex==int(dftotry['myindex']))].index.tolist()
            linkedin_todo=linkedin_todo.drop(index=tempdroplist) 
            print(name_todo+": Fail")
        else:            
            # if this people have worked in APPLE, we think this ruler is founded 
            # (Name consistency is checked in "get_data")
            Loopnames=list(content['Company'])+list(content['Title'])+list()
            APPLEinit=0
            for loopnames in Loopnames:
                if "APPLE" in loopnames:
                    APPLEinit=1
                    break
            else:
                pass
            
            if APPLEinit==1:
                # for example, if the first url of X.X is right, we break the for loop, and delete X.X from todo
                linkedin=linkedin.append(content,ignore_index=True)
                try:
                    linkedin_todo=linkedin_todo.drop(index=templist)
                except:
                    templist=linkedin_todo[(linkedin_todo.Date==date_todo)&(linkedin_todo.Names==name_todo)].index.tolist()
                    linkedin_todo=linkedin_todo.drop(index=templist)                
                case+=1
                print(name_todo+": Success +"+ str(case)+"!")
                break
            else:                
                tempdroplist=linkedin_todo[(linkedin_todo.myindex==int(dftotry['myindex']))].index.tolist()
                linkedin_todo=linkedin_todo.drop(index=tempdroplist)     
                print(name_todo+": Fail + 1")

    # save data google_ruler/google_ruler_todo
    output=open(r'final\linkedin','wb')
    pickle.dump(linkedin,output)
    output.close() 

linkedin.to_csv(r'final\linkedin_APPLE_experience.csv',encoding='utf_8_sig')





