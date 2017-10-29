from bs4 import BeautifulSoup
import requests
import Queue
import threading
import time
import csv
from fake_useragent import UserAgent

start_time = time.time()

ua = UserAgent()
phoneNumbers = dict()
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
# print headers
pageSeperator = '-'
city = "Chandigarh"
domains = ["toys"]
startingLinkTemplate = "http://www.justdial.com/{City}/{Domain}"
storeQueue = Queue.Queue();
storeCount = 0
ACCESS_DENIED = "Access Denied"

# with open('domains.csv', 'r') as domainFile:
#     rows = domainFile.read().split('\r')
#     for row in rows:
#         if str(row).strip('\n') != "":
#             domains.append(str(row).strip('\n'))
# print domains

num_worker_threads = len(domains)*5

# Consumer Thread task
def addPhoneNumberByVisiting(url, store, domain):
    try:
        # print str(threading.current_thread().name) + " Exception Visiting Store: " + store
        r = requests.get(url, headers=headers).text
        soup = BeautifulSoup(r, "html.parser")
        accessDeniedMessage = soup.find("h1")
        if ACCESS_DENIED in accessDeniedMessage:
            print "Access Denied on: " + url
            storeQueue.put((url, store, domain))
            return
        numbers = soup.find_all("a", class_="tel")
        for element in numbers:
            num = element.b.get_text()[-10:] if element.b is not None else element.get_text()[-10:]
            if '-' not in num and len(num) is 10:
                phoneNumbers[num] = (store, domain)
    except:
        print str(threading.current_thread().name) + " Exception Visiting Store: " + store

def addPhoneNumbers(url, pageNumber, domain):
    global storeCount
    print("Visiting: " + url)
    r = requests.get(url, headers=headers).text
    soup = BeautifulSoup(r, "html.parser")
    numbers = soup.find_all("p", class_="contact-info")
    sublinkspans = soup.find_all("span", class_="jcn")

    if len(numbers)+len(sublinkspans) is 0:
        return None

    for element in numbers:
        num = element.b.get_text()[-10:] if element.b is not None else element.a.get_text()[-10:]
        if '-' not in num:
            phoneNumbers[num] = ("",domain)

    for span in sublinkspans:
        try:
            storeCount += 1
            tup = (span.a["href"], span.a["title"], domain)
            storeQueue.put(tup)
        except KeyError:
            continue

    if pageNumber is not 1:
        return url.rsplit(pageSeperator, 1)[0] + pageSeperator + str(pageNumber+1)

    nextAnchorTag = soup.find("a", rel="next")
    try:
        return nextAnchorTag["href"] if nextAnchorTag is not None else None
    except KeyError:
        return None

def worker():
    while True:
        param = storeQueue.get()
        addPhoneNumberByVisiting(param[0], param[1], param[2])
        storeQueue.task_done()


def producer(domain):
    # print "Checkpoint 1"
    pageNum = 1
    nextPage = startingLinkTemplate.format(City=city, Domain=domain)
    try:
        while nextPage is not None:
            nextPage = addPhoneNumbers(nextPage, pageNum, domain)
            pageNum += 1
    except:
        print("Problem visiting pageNum: " + str(pageNum))

for i in range(num_worker_threads):
    t = threading.Thread(target=worker, args=(), name="Thread"+str(i))
    t.daemon = True
    t.start()

threads = []
for domain in domains:
    thread = threading.Thread(target=producer, args=(domain,), name="Producer "+domain)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

storeQueue.join()

with open('MobileNumbers.csv', 'wb') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in phoneNumbers.items():
        writer.writerow([value[0], key, value[1]])

print str(len(phoneNumbers)) + " MobileNumbers found in " + str(time.time()-start_time) + " secs from " + str(storeCount) + " stores"
# print "Averages: visit -> " + str(visitAverage) + " page -> " + str(pageAverage)
