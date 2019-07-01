############# Vide and Audio
import mutagen
import json
##############################
############# Images
from PIL import Image
from PIL.ExifTags import TAGS
##############################
############# PDF FILES
from PyPDF2 import PdfFileReader 
##############################
############# OFFICE DOCS
from xml.etree import ElementTree as etree
import zipfile
##############################
############# OTHERS
import sqlite3
from sqlite3 import Error
import os
from os import lstat
from datetime import datetime
###### Used for mime type even if it doesn't recognize office !!
import filetype
verbos=False
def main():
    global verbos
    print("")
    print("")
    print("███╗   ███╗███████╗████████╗ █████╗ ")
    print("████╗ ████║██╔════╝╚══██╔══╝██╔══██╗")
    print("██╔████╔██║█████╗     ██║   ███████║")
    print("██║╚██╔╝██║██╔══╝     ██║   ██╔══██║")
    print("██║ ╚═╝ ██║███████╗   ██║   ██║  ██║")
    print("╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝")
    print("")
    print( "Meta data extraction for Audio/Video/pdf/Office ")
    print("version 1.0")
    path=input("Past the folder link you want to process:\n")
    verb=input("Type V for verbos\n")
    if(verb.lower()=="v"):
        print(verb)
        verbos=True
    checkFiles(path)
#############################################
#### DB STUFF
#############################################
def create_db(path):
    try:
        conn=sqlite3.connect(path)
        print("+ New data base created :",path)
        c=conn.cursor()
        c.execute(''' CREATE TABLE FILES_METADATA
                  ([PATH] text,[TAG] text,[VALUE] text)''')
        conn.commit()
    except Error as e:
        print(e)
    finally:
        conn.close
def insertData(db,data):
    try:
        conn=sqlite3.connect(db)
        c=conn.cursor()
        c.executemany("INSERT INTO FILES_METADATA VALUES (?,?,?)",data)
        conn.commit()
    except Error as e:
        print("BOOOM"*10)
        print(e)
    finally:
        conn.close
def getFileMeta(db,file):
    try:
        data=[]
        conn=sqlite3.connect(db)
        c=conn.cursor()
        print("+select TAG,VALUE from FILES_METADATA WHERE PATH='{}'\n".format(file))
        for row in c.execute("select TAG,VALUE from FILES_METADATA WHERE PATH='{}'".format(file)):
            data.append(row)
    except Error as e:
        print(e)
    finally:
        conn.close
        return data
def getData(db,query):
    try:
        data=[]
        conn=sqlite3.connect(db)
        c=conn.cursor()
        for row in c.execute(query):
            print(row)
            data.append(row)
        
    except Error as e:
        print(e)
    finally:
        conn.close
        return data
def process_image(path,db):
    ## image/
    data=[]
    img_file = Image.open(path)
    exif_data = img_file._getexif()
    if exif_data is None:
        print("No EXIF data found")
        return None
    for name, value in exif_data.items():
       mytag = TAGS.get(name, name)
       if(verbos):print(mytag,value)
       data.append([path,mytag,str(value)])
    insertData(db,data)
def process_pdf(path,db):
    ## application/pdf
    data=[]
    pdf_file = PdfFileReader(path)
    xmpm = pdf_file.getXmpMetadata()

    if xmpm is None:
       print("No XMP metadata found in document.")
       return None
    data.append([path,"title",custom_vals( xmpm.dc_title)])
    data.append([path,"Creator(s)",custom_vals( xmpm.dc_creator)])
    data.append([path,"Contributors",custom_vals( xmpm.dc_contributor)])
    data.append([path,"Subject", custom_vals(xmpm.dc_subject)])
    data.append([path,"Description",custom_vals( xmpm.dc_description)])
    data.append([path,"Created", custom_vals(xmpm.xmp_createDate)])
    data.append([path,"Modified",custom_vals( xmpm.xmp_modifyDate) ])
    data.append([path,"Event Dates",custom_vals( xmpm.dc_date)])
    if xmpm.custom_properties:
       if(verbos):print("Custom Properties:")
       
       for k, v in xmpm.custom_properties.items():
          if(verbos):print("\t{}: {}".format(k, v))
          data.append([path,k,v])
    insertData(db,data)
    
def process_office(path,db):
    ## openxmlformats
    data=[]
    zipfile.is_zipfile(path)
    zfile = zipfile.ZipFile(path)
    core_xml = etree.fromstring(zfile.read('docProps/core.xml'))
    app_xml = etree.fromstring(zfile.read('docProps/app.xml'))
    core_mapping = {
       'title': 'Title',
       'subject': 'Subject',
       'creator': 'Author(s)',
       'keywords': 'Keywords',
       'description': 'Description',
       'lastModifiedBy': 'Last Modified By',
       'modified': 'Modified Date',
       'created': 'Created Date',
       'category': 'Category',
       'contentStatus': 'Status',
       'revision': 'Revision'
    }
    app_mapping = {
       'TotalTime': 'Edit Time (minutes)',
       'Pages': 'Page Count',
       'Words': 'Word Count',
       'Characters': 'Character Count',
       'Lines': 'Line Count',
       'Paragraphs': 'Paragraph Count',
       'Company': 'Company',
       'HyperlinkBase': 'Hyperlink Base',
       'Slides': 'Slide count',
       'Notes': 'Note Count',
       'HiddenSlides': 'Hidden Slide Count',
    }
    for element in core_xml.getchildren():
        if('date' in element.tag.lower() and isinstance(element.text, datetime)):
            text=datetime.strptime(element.text, "%Y-%m-%dT%H:%M:%SZ")
        else:
            text=element.text
        data.append([path,element.tag,text])
        if(verbos):print("{}: {}".format(element.tag, text))
    for element in app_xml.getchildren():
        if('date' in element.tag.lower() and isinstance(element.text, datetime)):
            text=datetime.strptime(element.text, "%Y-%m-%dT%H:%M:%SZ")
        else:
            text=element.text
        data.append([path,element.tag,text])
        if(verbos):print("{}: {}".format(element.tag, text))
    insertData(db,data)
    
def process_video(path,db):
    ## video/
    data=[]
    mp4_file=mutagen.File(path)
    if(mp4_file!=None and mp4_file.info!=None):
        data.append([path,"general info",mp4_file.info.pprint()])
        if(mp4_file.tags==None):
            print("BOOO Nothing VIDEO !!")
        else:
            cp_sym = u"\u00A9"
            qt_tag = {
              cp_sym + 'nam': 'Title', cp_sym + 'art': 'Artist',
              cp_sym + 'alb': 'Album', cp_sym + 'gen': 'Genre',
              'cpil': 'Compilation', cp_sym + 'day': 'Creation Date',
              'cnID': 'Apple Store Content ID', 'atID': 'Album Title ID',
              'plID': 'Playlist ID', 'geID': 'Genre ID', 'pcst': 'Podcast',
              'purl': 'Podcast URL', 'egid': 'Episode Global ID',
              'cmID': 'Camera ID', 'sfID': 'Apple Store Country',
              'desc': 'Description', 'ldes': 'Long Description'}
            if(verbos):print("{:22} | {}".format('Name', 'Value'))
            if(verbos):print("-" * 40)
            genre_ids = json.load(open('apple_genres.json'))
            for name, value in mp4_file.tags.items():
                tag_name = qt_tag.get(name, name)
                if isinstance(value, list):
                  value = "; ".join([str(x) for x in value])
                if name == 'geID':
                  value = "{}: {}".format(
                  value, genre_ids[str(value)].replace("|", " - "))
                if(verbos):print("{:22} | {}".format(tag_name, value))
                data.append([path,tag_name,value])
        insertData(db,data)

def process_audio(path,db):
    data=[]
    ## Audio/
    id3_file=mutagen.File(path)
    if(id3_file!=None and id3_file.info!=None):
        data.append([path,"general info",id3_file.info.pprint()])
        if(id3_file.tags==None):
            print("BOOOOOO Nothing Audio !!")
        else:
            id3_frames = {'TIT2': 'Title', 'TPE1': 'Artist', 'TALB': 'Album','TXXX':
              'Custom', 'TCON': 'Content Type', 'TDRL': 'Date released','COMM': 'Comments',
                 'TDRC': 'Recording Date'}
            if(verbos):print("{:15} | {:15} | {:38} | {}".format("Frame", "Description","Text","Value"))
            if(verbos):print("-" * 85)
            for frames in id3_file.tags.values():
              frame_name = id3_frames.get(frames.FrameID, frames.FrameID)
              desc = getattr(frames, 'desc', "N/A")
              text = getattr(frames, 'text', ["N/A"])[0]
              value = getattr(frames, 'value', "N/A")
              if "date" in frame_name.lower():
                 text = str(text)
              data.append([path,frame_name,desc+";"+text+";"+value])
              if(verbos):print("{:15} | {:15} | {:38} | {}".format(
                 frame_name, desc, text, value))
        insertData(db,data)

def custom_vals( value):
   if isinstance(value, list):
      return str(", ".join(value))
   elif isinstance(value, dict):
      fmt_value = [":".join((k, v)) for k, v in value.items()]
      return str(", ".join(fmt_value))
   elif isinstance(value, str) or isinstance(value, bool):
      return str(value)
   elif isinstance(value, bytes):
      return str(value.decode())
   elif isinstance(value, datetime):
      return str(value.isoformat())
   else:
      return "N/A"
def simpleMeta(path,db):

    stat_info = lstat(path)
    atime = datetime.utcfromtimestamp(stat_info.st_atime)
    mtime = datetime.utcfromtimestamp(stat_info.st_mtime)
    ctime = datetime.utcfromtimestamp(stat_info.st_ctime)
    data=[]
    data.append([path,"Access time",str(datetime.fromtimestamp(stat_info.st_atime))])
    data.append([path,"File mode",str(stat_info.st_mode)])
    data.append([path,"File inode",str(stat_info.st_ino)])
    data.append([path,"Device ID",str(stat_info.st_dev)])
    data.append([path,"Number of hard links",str(stat_info.st_nlink)])
    data.append([path,"Owner User ID",str(stat_info.st_uid)])
    data.append([path,"Group ID", str(stat_info.st_gid)])
    data.append([path,"File Size",str(stat_info.st_size)])
    data.append([path,"Is a symlink",str(os.path.islink(path))])
    if(verbos):print(data)
    insertData(db,data)
def checkFiles(path):
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
    # Create a database
    # DB NAME
    when=datetime.now()
    dbName=when.strftime("File%Y-%m-%d_%H-%M-%S.db")
    create_db(dbName)
    for f in files:
        kind=filetype.guess(f)
        if kind is None:
            simpleMeta(f,dbName)  
            continue
        elif "video/" in kind.mime:
            print("+",f,"VIDEO")
            simpleMeta(f,dbName)
            process_video(f,dbName)
        elif "audio/" in kind.mime:
            print("+",f,"AUDIO")
            simpleMeta(f,dbName)
            process_audio(f,dbName)
        elif "image/" in kind.mime:
            simpleMeta(f,dbName)
            process_image(f,dbName)
            print("+",f,"IMAGE")
        elif "application/pdf" in kind.mime:
            simpleMeta(f,dbName)
            process_pdf(f,dbName)
            print("+",f,"pdf")
        elif (".docx" in f) or (".xlsx" in f):
            simpleMeta(f,dbName)
            process_office(f,dbName)
            print("+",f,"OFFICE")
        else:
            simpleMeta(f,dbName)            
            print("#" *100)
            print (kind.mime)
    return [dbName,files]
    
if __name__ == '__main__':
	main()
