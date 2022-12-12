from math import log
import bisect
import datetime
import linecache
files_to_index_at_a_time = 50000

import re
import sys
from nltk.stem.snowball import SnowballStemmer
stemmer = SnowballStemmer("english")
from nltk.corpus import stopwords 


def isEnglish(s):
    try:
        encoding = 'utf-8'
        s.encode(encoding=encoding).decode('ascii')
    except:
        return False
    else:
        return True

def Tokenize(text):
    return text.split()

def lower(text):
    return text.lower()

STOPWORDS = set(stopwords.words('english')) 
STOPWORDS =  STOPWORDS.union(set(["http", "https", "www", "ftp", "com", "net", "org", "archives", "pdf", "html", "png", "txt", "redirect"]))
def stop_word_removal(text):
    return [x for x in text if x not in STOPWORDS and isEnglish(x)]

def Stemming(text):
    return [stemmer.stem(titl) for titl in text]
    

secondary_list=[]
index_folder_path = sys.argv[1]
if index_folder_path[len(index_folder_path)-1]=="/":
    index_folder_path = index_folder_path[:-1]
with open(index_folder_path+'/'+'secondary_index.txt') as f:
    secondary_list = [a.split(" ")[0] for a in f.read().splitlines() ]


def get_posting_list(word):
    global secondary_list
    offset_file_num = bisect.bisect_left(secondary_list,word)
    if(offset_file_num<len(secondary_list) and secondary_list[offset_file_num] == word):
        offset_file_num += 1
    offset_file_num = str(offset_file_num)

    posting_list =  ""
    if offset_file_num !="0":
        word_posting = {}
        fp = open(index_folder_path+"/offset"+offset_file_num+".txt")
        string_ = fp.readline().strip();
        while string_ != "":
            word_posting[string_.split(" ")[0]]=int(string_.split(" ")[1])
            string_ = fp.readline().strip();
            
        
        if word not in word_posting:
            return posting_list
        
        fp = open(index_folder_path+"/index"+offset_file_num+".txt")
        fp.seek(word_posting[word])
        posting_list = fp.readline().strip()
        posting_list = posting_list.split(":")[1]
        fp.close()
    return posting_list


def process_id_score(id_score,word,fields):
    posting_list = get_posting_list(word).split("|")
    posting_list_len = len(posting_list)

    if(posting_list[0]==""):
        return
    
    tf={}
    for part in posting_list:
        doc = int(part.split("-")[0][1:])
        pattern = re.findall(r""+str(fields)+'\d*',part.split("-")[1])
        tf.setdefault(doc,0)
        for p in pattern:
            tf[doc] += int(p[1:])
        

    Total_documents = 19567268+1 #page.pid+1
    idf = 1.0 + log(float(Total_documents) / posting_list_len)

    for key in tf.keys():
        id_score.setdefault(key,0)
        id_score[key]+=log(1+tf[key])*idf



with open(sys.argv[2]) as f:
    queries = f.read().splitlines() 

outStat = open("./​queries_op.txt​", "w")
for query in queries:
    k = int(query.split(',')[0])
    query = query.split(',')[1].strip()
    query_copy = query
    start_s = datetime.datetime.now()
    query.lower()
    query = Tokenize(query)
    query = stop_word_removal(query)
    query = Stemming(query)  

    id_score={}
    if ":" not in query[0]:
        id_score = {}
        for query_part in query:
            process_id_score(id_score,query_part,"[a-z]")

    else:
        id_score = {}
        field_dict = {}
        i=0
        while i<len(query):
            field = query[i].split(":")[0]
            word = query[i].split(":")[1]
            field_dict.setdefault(field,[])
            field_dict[field].append(word)
            i+=1
            while i<len(query) and ":" not in query[i]:
                field_dict[field].append(query[i])
                i+=1
            
             
        # print(field_dict)
        for key in field_dict.keys():
            lst = field_dict[key]
            for word in lst:
                process_id_score(id_score,word,key)
   
        

    sorted_x = sorted(id_score.items(), key=lambda kv: kv[1],reverse=True)
    # print(sorted_x)
    # res= get_titles()
    titles=[]
    doc_ids = [a[0] for a in sorted_x]
    i = 0
    while i<len(doc_ids) and i < k:
        file_num = int(doc_ids[i]/files_to_index_at_a_time)
        line_num = int(doc_ids[i]%files_to_index_at_a_time)+1
        title = linecache.getline(index_folder_path+"/title"+str(file_num)+".txt",line_num)
        titles.append((title[:-1],doc_ids[i]))

        i += 1

    
    end_s = datetime.datetime.now()


    outStat = open("./​queries_op.txt​", "a")
    for res in titles:
        outStat.write(str(res[1])+", "+res[0]+"\n")
    outStat.write(str((end_s - start_s).seconds)+", "+str((end_s - start_s).seconds/k)+"\n\n")
    # print("\nResults for Query \""+query_copy+"\" in ",(end_s - start_s).seconds," seconds")
    # i=1
    # for r in titles:
    #     print(str(i)+".",r[0])
    #     i += 1
    

