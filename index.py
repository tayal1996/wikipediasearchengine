import os
import re
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords 
stemmer = SnowballStemmer("english")
import xml.sax
import string
import datetime
import sys
index_dictionary = {}
invertedindex_stat_1 = 0
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
files_to_index_at_a_time = 50000
# files_to_index_at_a_time = 2500

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

def isEnglish(s):
    try:
        encoding = 'utf-8'
        s.encode(encoding=encoding).decode('ascii')
    except:
        return False
    else:
        return True

def write_to_temp_index(index_dictionary,file_num):
    print(str(page.pid+1)+" articles processed")
    outF = open("tempind_/"+str(file_num)+".txt", "w")
    sorted_keys = sorted(index_dictionary.keys())
    for key in sorted_keys:
        line = key+":"
        for sub_list in index_dictionary[key]:
            sublist_split = sub_list.split(" ");
            is_page_number = True
            for elem in sublist_split:
                if is_page_number:
                    line+=elem+"-"
                    is_page_number=False
                else:
                    line+=elem
            line+="|"
        outF.write(line[:-1])
        outF.write("\n")
    outF.close()
    index_dictionary.clear()

class Page:

    def __init__(self):
        self.wikiItems = {}
        self.wikiItems["title"] = []
        self.wikiItems["body"] = []
        self.wikiItems["info"] = []
        self.wikiItems["category"] = []
        self.wikiItems["links"] = []
        self.wikiItems["references"] = []
        self.pid = -1

    def set_title(self,title):
        self.wikiItems["title"] = title

    def set_Field_Text(self,body_text):
        for key in self.wikiItems.keys():
            if key != "title":
                self.wikiItems[key] = []

        all_lines = body_text.split('\n')
        
        len_lines = len(all_lines)
        external_links = ["== external links ==","==external links ==","== external links==","==external links=="]
        references = ["== references ==","==references ==","== references==","==references=="]
        i=0
        while i < len_lines:
            if "{{infobox" in all_lines[i]:
                open_curly_brackets = 0
                while i < len_lines:
                    open_curly_brackets += (all_lines[i].count("{{")-all_lines[i].count("}}"))
                    if open_curly_brackets > 0:
                            splitted_first_line = all_lines[i].split("{{infobox");
                            if("{{infobox" in all_lines[i] and len(splitted_first_line) >= 2 and len(splitted_first_line[1])>0):
                                self.wikiItems["info"].append(splitted_first_line[1])
                            else :
                                self.wikiItems["info"].append(all_lines[i])
                    else:
                        break
                    i+=1
     
            elif "[[category:" in all_lines[i]:
                category_line_split = all_lines[i].split("[[category:")
                if(len(category_line_split)>1):
                    self.wikiItems["category"].append(category_line_split[1].split("]]")[0])
                    self.wikiItems["category"].append(' ')

            

            elif any(link in all_lines[i] for link in external_links):
                i+=1
                while i < len_lines:
                    if "*[" in all_lines[i] or "* [" in all_lines[i]:
                        self.wikiItems["links"].extend(all_lines[i].split(' '))
                        i+=1
                    else:
                        break 

            elif any(ref in all_lines[i] for ref in references):
                open_curly_brackets = 0
                i+=1
                while i < len_lines:
                    open_curly_brackets += (all_lines[i].count("{{")-all_lines[i].count("}}"))
                    if open_curly_brackets > 0:
                        if "{{vcite" not in all_lines[i] and "{{cite" not in all_lines[i] and "{{reflist" not in all_lines[i]:
                            self.wikiItems["references"].append(all_lines[i])
                    else:
                        break
                    i+=1
            else:
                self.wikiItems["body"].append(all_lines[i])
            i+=1

        for key in self.wikiItems.keys():
            self.wikiItems[key] = ''.join(self.wikiItems[key])
        

    def process(self):
        global invertedindex_stat_1
        for key in self.wikiItems.keys():
            self.wikiItems[key] = re.sub(r'<(.*?)>','',self.wikiItems[key]) #Remove tags if any
            self.wikiItems[key] = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', self.wikiItems[key]) #Remove Url
            self.wikiItems[key] = re.sub(r'{\|(.*?)\|}', '', self.wikiItems[key]) #Remove CSS
            self.wikiItems[key] = re.sub(r'\[\[file:(.*?)\]\]', '', self.wikiItems[key]) #Remove File
            self.wikiItems[key] = re.sub(r'[.,;_()"/\'=]', ' ', self.wikiItems[key]) #Remove Punctuaion
            self.wikiItems[key] = re.sub(r'[~`!@#$%&\-^*+{\[}\]()":\|\\<>/?]', ' ', self.wikiItems[key])
            
            self.wikiItems[key] = Tokenize(self.wikiItems[key])
            invertedindex_stat_1 += len(self.wikiItems[key])
            self.wikiItems[key] = stop_word_removal(self.wikiItems[key])
            self.wikiItems[key] = Stemming(self.wikiItems[key])
        



    def create_index(self):
        final_dictionary = {}
        dictionary_local = {}
        for key in self.wikiItems.keys():
            title_split = self.wikiItems[key]
            for word in title_split:
                dictionary_local.setdefault(word,0)
                dictionary_local[word]+=1
            for word in dictionary_local:
                final_dictionary.setdefault(word,"p"+str(self.pid))
                final_dictionary[word]+= " "+key[0]+str(dictionary_local[word])
            dictionary_local.clear()

        for word in final_dictionary:
            index_dictionary.setdefault(word,[])
            index_dictionary[word].append(final_dictionary[word])
        dictionary_local.clear()
        final_dictionary.clear()


page = Page()
title_pid=[]
class ParseHandler( xml.sax.ContentHandler ):
    def __init__(self):
        self.page = False
    def startElement(self, tag, attributes):
        self.tag = tag
        self.buffer = ''
        if self.tag == "page":
            self.page = True
            page.pid+=1
    def endElement(self, tag):
        global file_num, outF_title, title_number, offset_title, outF_offset
        if tag == "page":
            self.page = False
            if (page.pid+1)%files_to_index_at_a_time==0:
                write_to_temp_index(index_dictionary,file_num)
                file_num=file_num+1
        elif tag == "text":
            page.set_Field_Text(self.buffer.lower())
            page.process()
            page.create_index()
            self.buffer = ''
        elif tag == "title":
            outF_title.write(self.buffer+"\n")
            page.set_title(''.join(self.buffer.lower()))
            self.buffer = ''
            if (page.pid+1)%files_to_index_at_a_time==0:
                outF_title.close()
                title_number += 1
                outF_title = open(index_folder_path+"/title"+str(title_number)+".txt", "w")
                

    def characters(self, content):
        if self.page == True:   
            if self.tag == "text":
                self.buffer +=content 
            elif self.tag == "title":
                self.buffer = content

import heapq
total_tokens = 0
def Kwaymerge():
    global total_tokens
    file_dic = {}
    heap = []
    num_files = len(os.listdir("tempind_"))
    file_num=1
    while file_num <= num_files:
        file_dic[file_num]=open('tempind_/'+str(file_num)+'.txt','r+')
        heap.append((file_dic[file_num].readline().strip(),file_num))
        file_num+=1
    heapq.heapify(heap)
    
    outS = open(index_folder_path+"/secondary_index.txt", "w")

    prev = "...."
    offset_file_size = 0
    max_offset_file_size = -1
    offset= 0 
    i_n = 1
    while(len(heap)>0):
        string = heap[0][0]
        file_number = heap[0][1]
        if string=='':
            heapq.heappop(heap)
            os.remove('tempind_/'+str(file_number)+'.txt')
        else:
            heapq.heappop(heap)
            heapq.heappush(heap,(file_dic[file_number].readline().strip(),file_number))  
            word = string.split(":")[0]
            posting = string.split(":")[1]
            if word == prev:
                outF.write("|"+posting)
                offset+=len("|"+posting)
            else:
                if(offset_file_size>max_offset_file_size):
                    offset_file_size=0
                    max_offset_file_size = 10*1024*1024    #10 MB
                    prev = "...."
                    outF = open(index_folder_path+"/index"+str(i_n)+".txt", "w")
                    outO = open(index_folder_path+"/offset"+str(i_n)+".txt", "w")
                    offset= 0  
                    i_n += 1
                    outS.write(string.split(":")[0]+" "+str(i_n-1)+"\n")
                    
                else:
                    outF.write("\n")  
                    offset+=1            
                prev = word
                outO.write(word+" "+str(offset)+"\n")
                offset_file_size += len(word+" "+str(offset)+"\n")
                outF.write(string)
                offset += len(string)
                total_tokens += 1






index_folder_path = sys.argv[2]
if index_folder_path[len(index_folder_path)-1]=="/":
    index_folder_path = index_folder_path[:-1]
try:
    os.mkdir(index_folder_path)
except:
    pass

title_number = 0
outF_title = open(index_folder_path+"/title"+str(title_number)+".txt", "w")
file_num=1

parser.setContentHandler( ParseHandler() )
start = datetime.datetime.now()



try:
    os.mkdir("tempind_")
except:
    pass

print("Temp Index started")
dump_data = sys.argv[1]
if dump_data[len(dump_data)-1]=="/":
    dump_data = dump_data[:-1]

num_files = os.listdir(dump_data)
for files in num_files:
    parser.parse(dump_data+"/"+files)

if index_dictionary:
    write_to_temp_index(index_dictionary,file_num)


outF_title.close()

print("K - way Merging ...")
Kwaymerge()


end = datetime.datetime.now()
hr = int((end-start).seconds/3600)
mn = int(((end-start).seconds%3600)/60)
secs = int(((end-start).seconds%3600)%60)
print("Indexing Time : ",hr," hrs ",mn," mns",secs," secs")
print("Total Articles : "+str(page.pid+1))



outStat = open("./stats.txt​", "w")

total_size = 0
for path, dirs, files in os.walk(index_folder_path):
    for f in files:
        fp = os.path.join(path, f)
        total_size += os.path.getsize(fp)

outStat.write(str(total_size/(10**6))+" MB\n")
outStat.write(str(len(os.listdir(index_folder_path)))+" files\n")
outStat.write(str(total_tokens)+" tokens\n")





