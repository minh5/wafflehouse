from BeautifulSoup import BeautifulSoup
import urllib2, sys
import re
import itertools
import pandas as pd
import geocoder
    
def waffles(state):    
    #first - code to request website info
    url  = "http://www.menuism.com/restaurant-locations/waffle-house-78955/us/" + state
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}

    req = urllib2.Request(url, headers=hdr)
    page = urllib2.urlopen(req)
    content = page.read()
    soup = BeautifulSoup(content)
    
    #second - code to grab all the addresses on the page
    rawhtml = soup.findAll("ul", {"class":""})

    #getting addresses
    itemList = []
    for item in rawhtml:
        itemList.append(''.join(item.findAll(text=True)).split("\n\n\n"))

    #flattening the list and removing white space
    chain = itertools.chain(*itemList)
    chainedList = (list(chain))
    addresses = map(lambda x: x.strip(), chainedList)

    #getting cities 
    itemList = []
    for item in rawhtml:
        itemList.append(item)

    #same chaining but this time, i take the raw html tags and flatten them
    chain = itertools.chain(*itemList)
    chainedList = (list(chain))
    y = [item for item in chainedList if len(item) > 1]

    #getting final list of cities
    cities = []
    for i in range(0, len(y)):
        cities.append(y[i].a['title'].split('-')[0].split(" in ")[1])

    #creating dataframe from lists
    data = pd.DataFrame({'raw': addresses,
                         'cities': cities})
    data['address'] = map(lambda x: x[x.find(" at ")+4:len(x)], data['raw'])
    data['zip'] = map(lambda x: x[16:21], data['raw'])

    #third - get list of all the cities available
    allLinks = soup.find("ul", {"class":"list-unstyled-links"}).findAll("a")

    allCities = []
    for item in allLinks:
        title = item['title']
        if title not in allCities:
            allCities.append(title)

    #clean up list of all cities
    newList = map(lambda x: x[16:x.find(" - ")], allCities)

    #find cities that does not have multiple locations because we'll have to pull data from them separately
    toRemove = map(lambda x:x.strip(), data['cities'].drop_duplicates().tolist())
    remainder = [city for city in newList if city not in toRemove]

    #mapping the remainder list and pair it with their respective values to get link
    newDict = dict(zip(newList, allCities))

    finalDict = {}
    for key, value in newDict.iteritems():
        if key in remainder:
            finalDict[key] = value
    
    #fourth - scrap addresses from cities with only one restaurant
    restaurantList = []
    for key, value in finalDict.iteritems():
        #load up new url from finalDict values 
        newUrl = soup.find("a", {"title": value})["href"]

        #request the new page
        req2 = urllib2.Request(newUrl, headers=hdr)
        page2 = urllib2.urlopen(req2)
        content2 = page2.read()
        soup2 = BeautifulSoup(content2)

        #parse address from soup2
        addyText = str(soup2.find("span",{"data-listing-attr":"address.street"}).contents)
        newAddress = re.sub(r'\\n+\\t\\t\\t\\t\\t\\t\\t\\t', ' ', addyText).split('\\t')[1].replace("']","").strip()

        #parsing zipcode from soup2
        zipText = str(soup2.find("span",{"data-listing-attr":"address.postal_code"}).contents)
        zipCode = re.sub(r'\\n+\\t\\t\\t\\t\\t\\t\\t\\t', ' ', zipText).split('\\t')[1].replace("']","").strip()

        #create an array of arrays to append to the dataframe
        toAdd = [key, "single loc", newAddress, zipCode]
        restaurantList.append(toAdd)
    
    #fifth - combine everything together into a dataframe
    if len(restaurantList) == 0:
        waffles = data
        return waffles
    else:
        final = pd.DataFrame(restaurantList)
        final.columns = ['cities', 'raw','address','zip']
        waffles = data.append(final)
        return(waffles)
        
listOfStates = ['al','ar','az','ca','co','de','fl','ga',
               'il','in','ks','ky','la','md','mi','mo',
               'ms','nc','nm','ny','oh','ok','pa','sc',
               'tn','tx','va','wi','wv']
               
wafflesdf = pd.DataFrame()
for item in listOfStates:
    print "processing " + item
    tempdf = waffles(item)
    wafflesdf = wafflesdf.append(tempdf)
    print "finished with " + item
    
    
data = pd.read_csv('~/waffles.csv')
data['full'] = data['address'] + ", " + data['cities'] + " " + data['zip']


coordinates = []
for a in data['full']:
    print a
    coordinates.append(geocoder.bing(a, key = keyString).latlng)

coordinates = pd.DataFrame(coordinates)
coordinates.columns = ['lats','lon']
data = data.loc[:, "full"]
data = pd.concat([data, coordinates], axis=1)
data.to_csv('~/geoWaffles.csv')