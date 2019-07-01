from tkinter import *
import tkinter.messagebox as box
from tkinter import filedialog
from metaExtractor import *
class ttt:
    def __init__(self):
        frame = Frame( root )
        self.listbox = Listbox(root, width=60, height=50, selectmode=SINGLE)
        self.listbox.grid(row=0, column=0)
        self.listbox.bind('<<ListboxSelect>>',lambda event: self.displayDetails())
        self.listbox.place(x=40,y=40)
        #self.listbox.pack()
        self.labelContent=StringVar()
        self.labelMetaData = Label(root,textvariable=self.labelContent,bg='grey',font=('Arial',12))
        self.labelContent.set("META DATA INFOS :")
        self.labelMetaData.place(x=450,y=40)
        #self.labelMetaData.pack()
        self.boutonMeta = Button(root,text='Selectionner un dossier',command=self.getFolder)
        self.boutonMeta.place(x=10,y=10)
        self.str1 = StringVar()
        self.e1 = Entry(root, textvariable=self.str1)
        self.str1.trace_add('write', self.filterListBox)
        self.e1.place(x=200,y=10)
        self.lblInfo=StringVar()
        self.labelInfo=Label(root,textvariable=self.lblInfo,font=('Agency',12))
        self.labelInfo.place(x=400,y=10)
    def getFolder(self, name='', index='', mode=''):
        root.directory = filedialog.askdirectory()
        self.lblInfo.set("Processing Please wait  !")
        self.labelInfo.update_idletasks()
        ########  Database Creation
        self.data=checkFiles(root.directory)#data =[dbName,listFiles]
        self.lblInfo.set("Data base created : "+self.data[0])
        self.labelInfo.update_idletasks()
        ########  ListBox Update
        self.fillListBox(self.data[1])
        self.lblInfo.set("Data base created and ready for use :"+self.data[0])
        self.labelInfo.update_idletasks()
    def fillListBox(self,data):
      for p in data:
          self.listbox.insert("end",p)
    def filterListBox(self,name='', index='', mode=''):
        # get File Name
        tmp = self.str1.get()
        if(tmp):
            self.listbox.delete(0,'end')
            # Filter files using typed tmp
            for f in self.data[1]:
                if(tmp in f):
                    self.listbox.insert("end",f)
    def displayDetails(self):
        # Data extraction from database
        index = int(self.listbox.curselection()[0])
        path = self.listbox.get(index)
        try:
            data=getFileMeta(self.data[0],path)
            text=""
            for d in data:
                text=text+"\n"+d[0]+" : "+d[1]
            self.labelContent.set(text)
            self.labelMetaData.update_idletasks()
        except :
            print("ERREUUUR")
root = Tk()
root.title('Metadata EXTRACTOR GUI V1.0')
root.geometry('900x700')
t = ttt()
root.mainloop()
