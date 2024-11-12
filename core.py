from re import X, template
from time import strftime
import xlrd
import xlwt
import os,json,sys
import datetime, pytz
import pickle
import locale
locale.setlocale(locale.LC_NUMERIC, 'hi_IN')
from copy import deepcopy
import firebase_admin
from firebase_admin import credentials, db
import dateutil.parser
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

# Fix for opening xlsx
xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True

# TODO: Check if the uploaded statement are in correct date range!

APP_NAME = "Record Matcher"

HDFC_TALLY_LEDGERNAME = "HDFC Bank A/c No.50200008623602"
ICICI_TALLY_LEDGERNAME_GOK = "ICICI Bank A/c No.099005000974"
ICICI_TALLY_LEDGERNAME_UNI = "ICICI 1027"
PAYMENT_INTERMEDIARY_TALLY_LEDGERNAME = "OTHER CREDITORS"
RECEIPT_INTERMEDIARY_TALLY_LEDGERNAME = "OTHER DEBTORS"

def get_current_time():
    t = datetime.datetime.now(pytz.timezone('Asia/Kolkata')) 
    # formatted_time = str(t.day)+'/'+str(t.month)+'/'+str(t.year)+' '+str(t.hour)+':'+str(t.minute)+' '
    formatted_time = t=strftime("%d/%m/%Y %I:%M %p") + '.'
    return formatted_time
def validate_path(path):
    if not path:
        return False
    if not os.path.isfile(path) or not os.path.exists(path) or not (path.split('.')[-1]=='xls' or path.split('.')[-1]=='xlsx'):
        return False
    else:
        return True  
def validate_save_path(path):
        if not os.path.isfile(path) or not os.path.exists(path) or not (path.split('.')[-1]=='fil'):
            return False
        else:
            return True             
def validate_date(date):
        try:
            datetime.datetime.strptime(date, '%d/%m/%y')
        except ValueError:
            return False             
        return True
def validate_chqno(chqno):
    try:
        int(chqno)
    except ValueError:
        return False
    if(len(chqno)>15):
        return False
    return True    
def validate_amount(amount):
    try:
        int(amount)
    except ValueError:
        try:
            float(amount)
        except ValueError:    
            return False
    if(float(amount)<0):
        return False
    return True       
def validateSavefile(filePath):
    if not filePath:
        return False 
    fileName = filePath.split('/')[-1]
    if(len(fileName)<1):
        return False
    if fileName.split('.')[-1].lower()!='fil':
        return 'add_ext'
    return True    
def format_chqNo(chqNo):
    if(len(chqNo)>0):
        zerolist = ""
        for i in range(0,16-len(chqNo)):
            zerolist+=('0')
        zerolist+=chqNo
        newChqNo = zerolist
        return newChqNo
def searchby_transdate(table, date):
    new_table = []
    for each in table:
        # print(each[0],date)
        # if(each[0]==date):
        stmtdate = each[0].split('/')
        querydate = date.split('/')
        if stmtdate[0] == querydate[0]:
            if stmtdate[1] == querydate[1]:
                if stmtdate[2][-2:] == querydate[2][-2:]:
                    new_table.append(each)
    return new_table   
def searchby_chqno(table, chqNo):
    new_table = []
    for each in table:
        if(format_chqNo( each[2])== format_chqNo( chqNo)):
            new_table.append(each)
    return new_table   
def searchby_amount(table, amount):   
    new_table = []
    for each in table:
        try:
            if(float(each[5])==float(amount)):
                new_table.append(each)
        except ValueError:
            pass
        try:        
            if(float(each[6])== float(amount)):
                new_table.append(each)    
        except ValueError:
            pass       
    return new_table     
def prepare_save_data(master_table, master_selected_rows, save_path, master_excel_export_path):
    data_to_save = []
    data_to_save.append(master_table)
    data_to_save.append(master_selected_rows)
    data_to_save.append(save_path)
    data_to_save.append(master_excel_export_path)    
    return data_to_save

class InfiChequeStatement:
    # trans_col = 0
    # transDate_col = 1
    # chqDate_col = 2 #dd-mm-yyyy
    # bankName_col = 3
    # ledgerName_col = 4
    # chqNo_col = 5
    # amount_col = 6
    # narration_col = 7
    # issueDate_col = 8
    # passDate_col = 9
    # voucher_col = 10

    def setPath(self, path):
        if validate_path(path):
            self.path = path
            self.workbook = xlrd.open_workbook(self.path)
            self.worksheet = self.workbook.sheet_by_index(0)
            return True
        else:
            return False    
    def __init__(self):
        self.start_row = 1
        self.path = None
        self.workbook = None
        self.worksheet = None
        self.entry_list = None
        self.year = None
        self.company = None
        self.last_edited_time = None
        # self.save_path = None
        # self.createSavePath()
        return    
    def get_json(self):
        dict = {}
        dict["entry_list"] = self.entry_list
        dict["year"] = self.year
        dict["company"] = self.company
        # dict["last_edited_time"] = self.last_edited_time
        return dict
    def set_entry_list(self, val):
        self.entry_list = val 
        self.update_last_edited_time()   

    # def createSavePath(self):
    #     self.save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\Snapshot_"+self.month+'_'+self.year+'_'+self.bank
    #     return
    def update_last_edited_time(self):
        self.last_edited_time = get_current_time()  
    def get_last_edited_time(self):
        return self.last_edited_time  
    def get_year(self):
        return self.year   
    def get_company(self):
        return self.company 
    def set_year(self, val):
        self.year = val
    def set_company(self, val):
        self.company = val
    def release_excel_file(self):
        self.workbook.release_resources()
        self.worksheet = None
        del self.workbook
        return True            
    def grab_data(self):
        i = self.start_row
        # transDate, transNo, book, code, ledgerName, chqNo, chqDate, transtypeVoucher, narration, debit, credit = None
        self.entry_list = []
        if not self.worksheet:
            return False
        while True:
            entry = []
            try:
                val = self.worksheet.cell(i,0).value
                # print(val)
            except IndexError:
                break   
            if val != "Receipt Voucher":
                i+=1
                continue
                # val_as_datetime = datetime.datetime(*xlrd.xldate_as_tuple(val, self.workbook.datemode))   
            val = self.worksheet.cell(i,1).value    
            # year, month, day, hour, minute, second = xlrd.xldate_as_tuple(val, self.workbook.datemode)
            # date_in_string = str(day)+'/'+str(month)+'/'+str(year)
            date_in_string = '/'.join(val.split('-'))
            entry.append(date_in_string)
            for j in range(2,11):
                val = None
                val = self.worksheet.cell(i,j).value
                entry.append(val)
                j+=1
            # print("entry: ",entry)    
            self.entry_list.append(entry)
            i+=1
        self.release_excel_file()  
        self.update_last_edited_time()
        return True

    def compare_date(self,infiChqStmtDate, bank_date):
        # infiChqStmtDate format dd/mm/yyyy
        # bank_date format dd/mm/yy or dd-bbb-yyyy
        assert datetime.datetime.strptime(infiChqStmtDate, "%d/%m/%Y")
        try:
            bank_date = dateutil.parser.parse(bank_date, dayfirst=True)
        except :
            print(bank_date)
            raise
        infiChqStmtDate = datetime.datetime.strptime(infiChqStmtDate, "%d/%m/%Y")
        if infiChqStmtDate>bank_date:
            return False
        return True    
                       

    def findMatchByChequeNumber(self,bank_chequeNumber, bank_debit, bank_date):
        match_list = []

        def makeChequeNumberStandard(input_cheque_number):
            zerolist = ""
            for i in range(0,16-len(input_cheque_number)):
                zerolist+=('0')
            zerolist+=input_cheque_number
            return zerolist

        for each in self.entry_list:
            infiChqNo = each[4]
            infiDebitamt = each[5]
            infiTransDate = each[0]
            # print(infiTransDate, bank_date) 
            # if infiChqNo=="531189":
            #     print(each, infiTransDate, bank_date)
            if(len(infiChqNo)>=1):
                newInfiChqNo = makeChequeNumberStandard(infiChqNo)
                bank_chequeNumber = makeChequeNumberStandard(bank_chequeNumber)
                # print("newInfiChqNo: ",newInfiChqNo,', bank_chequeNumber: ',bank_chequeNumber, each[5] )
                if newInfiChqNo==bank_chequeNumber and bank_debit==infiDebitamt and self.compare_date(infiTransDate,bank_date ):
                    match_list.append(each)
                # else:
                    # print("Skip")    
        return match_list
    def getEntryList(self):
        return self.entry_list
class HDFCBankChequeStatement:
    start_row = None
    path = None
    workbook = None
    worksheet = None
    entry_list = None

    def setPath(self, path):
        if validate_path(path):
            self.path = path
            self.workbook = xlrd.open_workbook(self.path)
            self.worksheet = self.workbook.sheet_by_index(0)
            self.find_start_row()
            return True
        else:
            return False    

    def find_start_row(self):
        i=0
        while True:
            try:
                val=self.worksheet.cell(i,0).value
            except IndexError:
                print("Cannot find startRow in HDfc statement.")
                return  
            if val == "Date":
                if self.worksheet.cell(i+1,0).value[0]=='*':
                    self.start_row=i+2
                else:
                    self.start_row=i+1
                break            
            i+=1

    def grab_data(self):
        i = self.start_row
        # transDate, transNo, book, code, ledgerName, chqNo, chqDate, transtypeVoucher, narration, credit, debit = None
        self.entry_list = []
        while True:
            entry = []
            try:
                val = self.worksheet.cell(i,0).value
            except IndexError:
                break     
            if(len(val.split('/'))!=3):
                print("Reached end of hdfc statement")
                break
            for j in range(0,7):
                val = None
                val = self.worksheet.cell(i,j).value
                entry.append(val)
                j+=1
            self.entry_list.append(entry)
            # print("entry", entry)
            i+=1

    def getEntryList(self):
        return self.entry_list
class ICICIBankChequeStatement:
    start_row = None
    path = None
    workbook = None
    worksheet = None
    entry_list = None
    narration = 5

    def setPath(self, path):
        if validate_path(path):
            self.path = path
            self.workbook = xlrd.open_workbook(self.path)
            self.worksheet = self.workbook.sheet_by_index(0)
            self.find_start_row()
            return True
        else:
            return False    
    def getPath(self):
        return self.path
    def find_start_row(self):
        i=6
        try:
            val=self.worksheet.cell(i,0).value
        except IndexError:
            print("Cannot find startRow in ICICI statement.")
            return  
        try: 
            val2 = self.worksheet.cell(i-1,0).value.split('-')[2]
        except:
            print("Invalid ICICI statement.")
            return
        if val == "No.":
            self.start_row=i+1
        else:
            print("Invalid ICICI statement.")
        return    
    
    def process_narration(self, entry):
        narration = entry[5]
        narration = narration.split('/')
        entry[4] = ''
        if narration[0] != 'CLG' or len(narration)<3:
            return entry
        chq_no = narration[2]
        entry[4] = chq_no
        # print(entry)
        return entry

    def process_date(self, entry):
        date = entry[2]
        try:
            date= dateutil.parser.parse(date , dayfirst=True)
        except :
            print(date)
            raise
        entry[2] = date.strftime('%d-%b-%Y')
        return entry        

    def grab_data(self):
        i = self.start_row
        # No.	Transaction_ID	Value_Date	Txn_Posted_Date	ChequeNo.	Description_Cr/Dr	Transaction_Amount(INR)	Available_Balance(INR)	
        self.entry_list = []
        while True:
            entry = []
            try:
                val = self.worksheet.cell(i,0).value
            except IndexError:
                print("Reached end of Icici statement")
                break
            for j in range(0,9):
                val = None
                val = self.worksheet.cell(i,j).value
                entry.append(val)
                j+=1
            entry = self.process_narration(entry)    
            entry = self.process_date(entry)
            if entry:
                self.entry_list.append(entry)
            # print("entry", entry)
            i+=1

    def getEntryList(self):
        return self.entry_list

class TableSnapshot:
    master_table = None
    master_selected_rows = None
    master_excel_export_path = None
    month = None
    year = None
    bank = None
    company = None
    save_path = None

    def __init__(self, *inp):
        if len(inp) == 1:
            self.initialize_mode1(inp[0])
        elif len(inp) == 7:
            self.initialize_mode2(inp[0], inp[1],inp[2] ,inp[3] ,inp[4] ,inp[5] ,inp[6])
        return  

    def initialize_mode2(self,company,month,year,bank,master_table, master_selected_rows, master_excel_export_path):
        self.master_table = master_table
        self.master_selected_rows = master_selected_rows
        self.master_excel_export_path = master_excel_export_path
        self.month = month.lower()
        self.year = year.lower()
        self.bank = bank.lower()
        self.company = company.lower()
        self.creation_time = get_current_time()
        self.last_edited_time = None
        self.createSavePath()
        self.update_last_edited_time()
        return
    def initialize_mode1(self, dict):
        self.master_table = dict["master_table"]
        self.month = dict["month"]
        self.year = dict["year"]
        self.bank = dict["bank"]
        self.company = dict["company"]
        self.creation_time = dict["creation_time"]
        # self.creation_time = get_current_time()
        self.master_selected_rows = []
        self.master_excel_export_path = None
        self.last_edited_time = None
        self.createSavePath()
        self.update_last_edited_time()
        return

    def get_json(self):
        dict = {}
        dict["master_table"] = self.master_table
        dict["month"] = self.month
        dict["year"] = self.year
        dict["bank"] = self.bank
        dict["company"] = self.company
        dict["creation_time"] = self.creation_time
        return dict  

    def update_last_edited_time(self):
        self.last_edited_time = get_current_time()
    def get_master_table(self):
        return self.master_table
    def set_master_table(self, table):
        self.master_table = table
        return
    def get_master_selected_rows(self):
        return self.master_selected_rows
    def get_master_excel_export_path(self):
        return self.master_excel_export_path  
    def get_save_path(self):
        return self.save_path  
    def get_month(self):
        return self.month
    def get_year(self):
        return self.year
    def get_bank(self):
        return self.bank 
    def get_company(self):
        return self.company 
    def set_company(self, val):
        self.company = val       
    def get_last_edited_time(self):
        return self.last_edited_time   
    def set_master_selected_rows(self, val):
        self.master_selected_rows = val
        self.update_last_edited_time()
    def set_master_excel_export_path(self, val):
        self.master_excel_export_path = val    
        self.update_last_edited_time()
    def createSavePath(self):
        self.save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\Snapshot_"+self.month+'_'+self.year+'_'+self.bank
        return

class ChequeReportCollection:
    save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\ChequeReportCollection.fil"
    years = ['2019','2020','2021','2022','2023', '2024']
    banks = ['hdfc', 'icici']
    companies = ['gokul','universal','gawel1','gawel2','focus']
    cheque_report_dict = {}
    def __init__(self):
        return
    def get_years(self):
        return self.years   
    def get_cheque_report_dict(self):
        return self.cheque_report_dict         
    def load_cheque_report_collection(self):
        # Checking if directory exists
        if os.getenv('APPDATA'):
            target_dir = os.path.join(os.getenv('APPDATA'), APP_NAME)
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                print(f"Directory created: {target_dir}")
            else:
                print(f"Directory already exists: {target_dir}")
        else:
            print("APPDATA environment variable is not set.")
            return
        try:
            # raise FileNotFoundError
            with open(self.save_path, 'rb') as f:
                data_loaded = pickle.load(f)
                self.cheque_report_dict = data_loaded
        except FileNotFoundError:
            return False
        print('LOAD OK')    
        self.print_cheque_report()    
        return
    def save_cheque_report_collection(self):
        if not self.cheque_report_dict:
            print('Empty dict, save skip')
            return(True, 0)
        try:
            # print(self.cheque_report_dict)
            with open(self.save_path, 'wb') as f:
                pickle.dump(self.cheque_report_dict, f)    
        except TypeError: 
            raise
            return None,-1
        except FileNotFoundError:    
            return None,-2
        print('SAVE OK')     
        # self.print_cheque_report()    
        return True, 0        
    def print_cheque_report(self):
        print("*******ChequeReportCollection*******")
        for key,val in self.cheque_report_dict.items():
            print(key,':',val)
        return                        
    def get_dict_reference(self, year,  company):
        company = company.lower()
        if(company in self.companies and year in self.years ):
            return company+'_'+'_'+year
        return None                
    def delete_cheque_report_from_collection(self,  year,  company):
        ref = self.get_dict_reference(year,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('deleting table of ',company,year,'from table list with ref',ref)    
        self.cheque_report_dict[ref] = None
        status, code = self.save_cheque_report_collection()
        if status:
            print('ChequeReportCollection save success!!')
        else:
            print('ChequeReportCollection save fail with code ',code)   
        return True   
    def add_cheque_report_to_collection(self, chequeReport,ref=None):
        if not ref:
            year = chequeReport.get_year()
            company = chequeReport.get_company()
            ref = self.get_dict_reference(year,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('adding chequeReport to chequeReportCollection with ref',ref)    
        self.cheque_report_dict[ref] = chequeReport
        status, code = self.save_cheque_report_collection()
        if status:
            print('ChequeReportCollection save success!!')
        else:
            print('ChequeReportCollection save fail with code ',code)   
        return True   
    def get_cheque_report_from_collection(self,  year, company):
        ref = self.get_dict_reference(year,company)
        return self.get_table_from_collection_by_reference(ref)
    def get_table_from_collection_by_reference(self, ref):
        if not ref:
            return None
        try:
            return self.cheque_report_dict[ref]
        except KeyError:
            return None    
                    

class TableSnapshotCollection:
    save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.filv2"
    save_path_old = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.fil"
    table_list = {}
    months = ['april','may','june','july','august','september','october','november','december','january', 'february', 'march']
    years = ['2019','2020','2021','2022','2023', '2024']
    banks = ['hdfc', 'icici']
    companies = ['gokul','universal','gawel1','gawel2','focus']
    def __init__(self):
        return
    def get_months(self):
        return self.months
    def get_years(self):
        return self.years 
    def rename_old_save_path(self):
        os.rename(self.save_path_old,self.save_path_old+'_000')        
    def load_table(self):
        print(self.save_path)
        try:
            with open(self.save_path, 'rb') as f:
                data_loaded = pickle.load(f)
                self.table_list = data_loaded
        except FileNotFoundError:
            print("Load Failed. New installation?.")
            return False
        print('LOAD OK')    
        # self.print_table()    
        return True
    def load_old_table(self):
        print(self.save_path_old)
        try:
            with open(self.save_path_old, 'rb') as f:
                data_loaded = pickle.load(f)
                self.table_list = data_loaded
        except FileNotFoundError:
            return False
        print('Old file loaded')    
        self.print_table(old = True)    
        return True  
    def get_table_list(self):
        return self.table_list    
    def save_table(self):
        try:
            # print(self.table_list)
            with open(self.save_path, 'wb') as f:
                pickle.dump(self.table_list, f)    
        except TypeError: 
            return None,-1
        except FileNotFoundError:    
            return None,-2
        print('SAVE OK')     
        # self.print_table()    
        return True, 0        
    def print_table(self, old=False):
        if old:
            print("*******OLDTableSnapshotCollection*******")    
        else:    
            print("*******TableSnapshotCollection*******")
        for key,val in self.table_list.items():
            print(key,':',val)
        return                        
    def get_dict_reference(self, month, year, bank, company):
        month = month.lower()  
        bank = bank.lower()
        company = company.lower()
        # print('bank', bank)
        if(company in self.companies and month in self.months and year in self.years and bank in self.banks):
            return company+'_'+month+'_'+year+'_'+bank
        return None                
    def delete_table_from_collection(self, month, year, bank, company):
        ref = self.get_dict_reference(month,year,bank,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('deleting table of ',company,month,year,bank,'from table list with ref',ref)    
        self.table_list[ref] = None
        status, code = self.save_table()
        if status:
            print('TableCollection save success!!')
        else:
            print('TableCollection save fail with code ',code)   
        return True   
    def add_table_to_colection(self, tableSnapshot, save=True):
        month = tableSnapshot.get_month()
        year = tableSnapshot.get_year()
        company = tableSnapshot.get_company()
        bank = tableSnapshot.get_bank()     
        print(month, year,company,bank, tableSnapshot.get_master_excel_export_path(), tableSnapshot.get_save_path())       
        ref = self.get_dict_reference(month,year,bank,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('adding table to ',month,year,bank,company,'to table list with ref',ref,'.')    
        self.table_list[ref] = tableSnapshot
        if not save: 
            return
        status, code = self.save_table()
        if status:
            print('TableCollection save success!!')
        else:
            print('TableCollection save fail with code ',code)   
        return True   
    def get_table_from_collection(self, month, year, bank,company):
        ref = self.get_dict_reference(month,year,bank,company)
        return self.get_table_from_collection_by_reference(ref)
    def get_table_from_collection_by_reference(self,ref):
        if not ref:
            return None
        try:
            return self.table_list[ref]
        except KeyError:
            return None
class  TableOperations:
    def __init__(self):
        # self.hdfcBankChequeStatement = HDFCBankChequeStatement()
        # self.iciciBankChequeStatement = ICICIBankChequeStatement()
        self.tableSnapshotCollection = TableSnapshotCollection()
        self.chequeReportCollection = ChequeReportCollection()
        if self.chequeReportCollection.load_cheque_report_collection():
            print('ChequeReportCollection load success!!')
        if self.tableSnapshotCollection.load_table():
            print('TablesnapshotCollection load success!!')
        self.TableSnapshot= None   
        self.firebaseControls = FirebaseControls()
        try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        req_path = os.path.join(base_path, 'data.json')
        self.leftMenuJsonPath = req_path
        return

    def upload_data_to_firebase_db(self, callbackFuncforProgress):
        print("Uploading left-menu values to db")
        callbackFuncforProgress("Processing Left Menu values", "Retrieving values to upload",0.0)
        with open(self.leftMenuJsonPath) as f:
            data = json.load(f)
        self.firebaseControls.set_leftMenu_data(data) 
        print("Uploading tableSnapshot values to db")
        callbackFuncforProgress("Processing Left Menu values", "Finished uploading",1.0)

        callbackFuncforProgress("Processing cheque reports", "Retrieving snapshots to upload",0.0)
        # print(self.chequeReportCollection.get_cheque_report_dict())
        collection_dict = self.chequeReportCollection.get_cheque_report_dict()
        total_val = len(collection_dict)
        count=0
        print(collection_dict)
        for key in collection_dict:
            count+=1
            print("Uploading chequeReport: ", key)
            callbackFuncforProgress("Processing cheque reports", "Uploading "+key,round(count*8/total_val)/10)
            child = key
            obj = collection_dict[key]
            if(obj):
                self.firebaseControls.set_chequeReport(child, obj.get_json())   
        callbackFuncforProgress("Processing cheque reports", "Finished",1.0)     

        callbackFuncforProgress("Processing table snapshots", "Retrieving values to upload",0.0)
        table_list = self.tableSnapshotCollection.get_table_list()
        total_val = len(table_list)
        count=0
        for key in table_list:
            count+=1
            callbackFuncforProgress("Processing table snapshots", "Uploading "+key,round(count*8/total_val)/10)
            print("Uploading tablesnapshot: ", key)
            child = key
            obj = table_list[key]
            if(obj):
                self.firebaseControls.set_tableSnapshot(child, obj.get_json())
        callbackFuncforProgress("Processing table snapshots", "Finished",1.0)
        return
    
    def get_data_from_firebase_db(self, callbackFuncforProgress):
        print("Getting left-menu values from db")
        callbackFuncforProgress("Processing Left Menu values", "Downloading values from Firebase",0.0)
        data = self.firebaseControls.get_leftMenu_data()
        data = json.dumps(data, indent=4)
        callbackFuncforProgress("Processing Left Menu values", "Writing values to local file",0.5)
        with open(self.leftMenuJsonPath, "w") as outfile:
            outfile.write(data)
        callbackFuncforProgress("Processing Left Menu values", "Finished",1.0)

        callbackFuncforProgress("Processing cheque reports", "Downloading values from Firebase",0.0)
        # incomingChequeReport = self.firebaseControls.get_chequeReport()
        # total_val = len(incomingChequeReport)
        # count=0
        # if chequeReport:
        #     for key in incomingChequeReport:
        #         count+=1
        #         callbackFuncforProgress("Processing cheque reports", "Writing "+key,round(count*8/total_val)/10)
        #         chequeReport = self.chequeReportCollection.get_table_from_collection_by_reference(key)
        #         if not chequeReport:
        #             print("New chequeReport: " , key)
        #         else:
        #             print("Replacing existing chequeReport: " , key)
        #         chequeReport = InfiChequeStatement()
        #         chequeReport.set_entry_list(incomingChequeReport[key]['entry_list'])
        #         self.chequeReportCollection.add_cheque_report_to_collection(chequeReport, key)
        #     callbackFuncforProgress("Processing cheque reports", "Finalizing",0.9)
        #     self.chequeReportCollection.save_cheque_report_collection()
        # else:
        #     # MOD FOR BUSY
        #     pass        
        print("Downloading tableSnapshot values to db")
        callbackFuncforProgress("Processing table snapshots", "Downloading values from Firebase",0.0)
        incomingTableSnapshotData = self.firebaseControls.get_tableSnapshot()
        total_val = len(incomingTableSnapshotData)
        count=0
        for key in incomingTableSnapshotData:
            count+=1
            callbackFuncforProgress("Processing table snapshots", "Writing "+key,round(count*8/total_val)/10)
            tableSnapshot = self.tableSnapshotCollection.get_table_from_collection_by_reference(key)
            if not tableSnapshot:
                print("new tableSnapshot for ", key)
                tableSnapshot = TableSnapshot(incomingTableSnapshotData[key])
                self.tableSnapshotCollection.add_table_to_colection(tableSnapshot)
            else:
                print("Existing tableSnapshot found for ", key, "Replacing master table data")    
                tableSnapshot.set_master_table(incomingTableSnapshotData[key]['master_table'])    
        callbackFuncforProgress("Processing table snapshots", "Finalizing",0.9)
        self.tableSnapshotCollection.save_table()
        return        

    def get_table_from_collection(self, month, year, bank, company):
        self.month = month
        self.year = year
        self.bank = bank
        self.company = company
        snapshot = self.tableSnapshotCollection.get_table_from_collection(month,year,bank,company) 
        if not snapshot:
            return snapshot,'', '', '', '', ''
        credit_bal = 0.0
        debit_bal = 0.0       
        master_table = snapshot.get_master_table()
        start_date, end_date = "", ""
        for each in master_table:
            try:
                bank_date = dateutil.parser.parse(each['Bank Date'], dayfirst=True)
            except:
                if(each['meta'] == 'double'):
                    each['Bank Narration'] = "Double Match"
                    continue
                else:
                    print("Error at entry ",each)
                    raise
            if start_date == "" or start_date>bank_date:
                start_date = bank_date 
            if end_date == "" or end_date<bank_date:
                end_date = bank_date  
            if(each['Credit'] != ''):
                credit_bal+=float(each['Credit'])
            if(each['Debit'] != ''):
                debit_bal+=float(each['Debit'])
        credit_bal = locale.format_string("%.2f", credit_bal, grouping=True)  
        debit_bal =  locale.format_string("%.2f", debit_bal, grouping=True)  
        # print(start_date, end_date)
        start_date = start_date.strftime("%Y/%m/%d")
        end_date = end_date.strftime("%Y/%m/%d")
        return snapshot, self.format_table_data(master_table), credit_bal, debit_bal, start_date, end_date

    def format_table_data(self, _tableData):
        tableData = deepcopy(_tableData)
        for each in tableData:
            if(each['Credit'] != ''):
                each['Credit'] = locale.format_string("%.2f", float(each['Credit']), grouping=True)
            if(each['Debit'] != ''):
                each['Debit'] = locale.format_string("%.2f", float(each['Debit']), grouping=True)
            if each['Closing Balance']!='':    
                each['Closing Balance'] = locale.format_string("%.2f", float(each['Closing Balance']), grouping=True)    
        return tableData    

    def delete_table_from_collection(self, month, year, bank, company):
        return self.tableSnapshotCollection.delete_table_from_collection(month,year,bank,company)        
    def delete_chequeReport_from_collection(self, year, company):
        return self.chequeReportCollection.delete_cheque_report_from_collection(year,company)          

    def get_chequeReport_from_collection(self, year, company):
        self.year = year
        self.company = company
        return self.chequeReportCollection.get_cheque_report_from_collection(year, company)     

    def prepare_table_data(self, statementObj, infiChequeStatement, previous_infiChequeStatement):
        # Bank
        # Date	Narration	Chq./Ref.No.	Value Dt	Withdrawal Amt.	Deposit Amt.	Closing Balance
        # 0     1           2               3           4               5               6
        # Infi
        # Trans. Date	Chq. Date	Bank Name	Account Head	Chq. No	Amount	Narration	Issued Date	Passed Date	Voucher
        # 0             1           2           3               4       5       6           7           8           9 
        if(self.bank=='hdfc'):
            bank_statement = statementObj.getEntryList()
            final_table = []
            for bank_entry in bank_statement:
                # if(not isinstance(bank_entry[2], int)):
                #     continue
                if not infiChequeStatement:
                    match_list = []
                else:
                    match_list = infiChequeStatement.findMatchByChequeNumber(bank_entry[2], bank_entry[5], bank_entry[0])
                # if len(match_list)>1:
                #     print("match_list: ",match_list)
                if len(match_list)==0 and previous_infiChequeStatement:
                    match_list = previous_infiChequeStatement.findMatchByChequeNumber(bank_entry[2], bank_entry[5], bank_entry[0])
                if len(match_list)>0:
                    for i in range(len(match_list)):
                        infi_entry = match_list[i]
                        if i==0:
                            table_row={}
                            table_row['Bank Date'] = bank_entry[0]
                            table_row['Bank Narration'] = bank_entry[1]
                            table_row['Chq No'] = bank_entry[2]
                            table_row['Party Name'] = infi_entry[3]
                            table_row['Infi Date'] = infi_entry[0]
                            table_row['Debit'] = bank_entry[4]
                            table_row['Credit'] = bank_entry[5]
                            table_row['Closing Balance'] = bank_entry[6]
                            if len(match_list)==1:
                                table_row['meta'] =""
                            else:
                                table_row['meta'] ="double"
                        else:
                            print("Double match found.")
                            table_row={}
                            table_row['Bank Date'] = ""
                            table_row['Bank Narration'] = ""
                            table_row['Chq No'] = bank_entry[2]
                            table_row['Party Name'] = infi_entry[3]
                            table_row['Infi Date'] = infi_entry[0]
                            table_row['Debit'] = ""
                            table_row['Credit'] = bank_entry[5]
                            table_row['Closing Balance'] = ""
                            table_row['meta'] = "double"
                        final_table.append(table_row)            

                else:
                    table_row={}
                    table_row['Bank Date'] = bank_entry[0]
                    table_row['Bank Narration'] = bank_entry[1]
                    table_row['Chq No'] = bank_entry[2]
                    table_row['Party Name'] = ""
                    table_row['Infi Date'] = ""
                    table_row['Debit'] = bank_entry[4]
                    table_row['Credit'] = bank_entry[5]
                    table_row['Closing Balance'] = bank_entry[6]
                    table_row['meta'] = ""                    
                    final_table.append(table_row)      

        elif(self.bank=='icici'):
            bank_statement = statementObj.getEntryList()
            final_table = []
            for bank_entry in bank_statement:
                if(bank_entry[4]!=None or bank_entry[4] != ''):
                    if not infiChequeStatement:
                        match_list = []
                    else:
                        match_list = infiChequeStatement.findMatchByChequeNumber(bank_entry[4], bank_entry[7], bank_entry[2])
                if len(match_list)==0 and previous_infiChequeStatement:
                    match_list = previous_infiChequeStatement.findMatchByChequeNumber(bank_entry[4], bank_entry[7], bank_entry[2])    
                cred_amt = ''
                deb_amt = ''
                if bank_entry[6] == 'CR':
                    cred_amt = bank_entry[7]
                elif bank_entry[6] == 'DR':
                    deb_amt = bank_entry[7]  
                if len(match_list)>0:
                    for i in range(len(match_list)):
                        infi_entry = match_list[i]
                        if i==0:
                            table_row={}
                            table_row['Bank Date'] = bank_entry[2]
                            table_row['Bank Narration'] = bank_entry[5]
                            table_row['Chq No'] = bank_entry[4]
                            table_row['Party Name'] = infi_entry[3]
                            table_row['Infi Date'] = infi_entry[0]
                            table_row['Credit'] = cred_amt
                            table_row['Debit'] = deb_amt
                            table_row['Closing Balance'] = bank_entry[8]
                            if len(match_list)==1:
                                table_row['meta'] = ""    
                            else:
                                table_row['meta'] = "double"    
                        else:
                            print("Double match found.")
                            table_row={}
                            table_row['Bank Date'] = ""
                            table_row['Bank Narration'] = ""
                            table_row['Chq No'] = bank_entry[4]
                            table_row['Party Name'] = infi_entry[3]
                            table_row['Infi Date'] = infi_entry[0]
                            table_row['Credit'] = cred_amt
                            table_row['Debit'] = deb_amt
                            table_row['Closing Balance'] = ""
                            table_row['meta'] = "double"
                        final_table.append(table_row)            

                else:
                    table_row={}
                    table_row['Bank Date'] = bank_entry[2]
                    table_row['Bank Narration'] = bank_entry[5]
                    table_row['Chq No'] = bank_entry[4]
                    table_row['Party Name'] = "" 
                    table_row['Infi Date'] = ""
                    table_row['Credit'] = cred_amt
                    table_row['Debit'] = deb_amt
                    table_row['Closing Balance'] = bank_entry[8]
                    table_row['meta'] = ""    
                    final_table.append(table_row)    
        return final_table      

    # DEPRACATED 
    # def convert_old_schema_to_new_schema(self):
    #     oldTableSnapshotCollection = TableSnapshotCollection()
    #     if not oldTableSnapshotCollection.load_old_table():
    #         print('No old table snapshot found')
    #         return False
    #     collection = oldTableSnapshotCollection.get_table_list()
    #     # for snapshot in collection:
    #     for key,snapshot in collection.items():    
    #         master_table = snapshot.get_master_table()
    #         root_dict = []
    #         if not snapshot.get_company():
    #             company = key.split('_')[0]
    #             snapshot.set_company(company)
    #         selected_rows_new = []    
    #         selected_rows_old = snapshot.get_master_selected_rows()
    #         for each in selected_rows_old:
    #             if isinstance(each, list):
    #                 selected_rows_new.append(each[0])
    #         if selected_rows_new!=[]:            
    #             snapshot.set_master_selected_rows(selected_rows_new)
    #         for row in master_table:
    #             row_dict={}
    #             row_dict['Bank Date'] = row[0]
    #             row_dict['Bank Narration'] = row[1]
    #             row_dict['Chq No'] = row[2]
    #             row_dict['Party Name'] = row[3]
    #             row_dict['Infi Date'] = row[4]
    #             row_dict['Credit'] = row[5]
    #             row_dict['Debit'] = row[6]
    #             row_dict['Closing Balance'] = row[7]
    #             row_dict['meta'] = row[8]
    #             root_dict.append(row_dict)  
    #         snapshot.set_master_table(root_dict) 
    #         self.tableSnapshotCollection.add_table_to_colection(snapshot)
    #     print('Renaming old file')
    #     oldTableSnapshotCollection.rename_old_save_path()
    #     print('Reloading table snapshot collection')
    #     if self.tableSnapshotCollection.load_table():
    #         print('TablesnapshotCollection reload success!!')
    #     return True
        
    def add_snapshot_to_table(self, statement_path):
        
        if self.month in ['january', 'february', 'march']:
            financial_year = str(int(self.year)-1)
        else:
            financial_year = self.year    
        
        # financial_year = self.year            
        previous_financial_year = str(int(financial_year)-1)   
        print("FINANCIAL YEAR =", financial_year)
        infiChequeStatement=self.chequeReportCollection.get_cheque_report_from_collection(financial_year,self.company)
        previous_infiChequeStatement=self.chequeReportCollection.get_cheque_report_from_collection(previous_financial_year,self.company)
        if not infiChequeStatement:
            # return False, -1
            # WORKAROUND FOR BUSY
            pass
        if self.bank == 'hdfc':
            hdfcBankChequeStatement = HDFCBankChequeStatement()
            if not hdfcBankChequeStatement.setPath(statement_path):
                return False, -3
            try:
                hdfcBankChequeStatement.grab_data()    
            except TypeError:
                return False, -3                    
            master_table = self.prepare_table_data(hdfcBankChequeStatement, infiChequeStatement, previous_infiChequeStatement)    
        else:
            iciciBankChequeStatement = ICICIBankChequeStatement()
            if not iciciBankChequeStatement.setPath(statement_path):
                return False, -4
            try:
                iciciBankChequeStatement.grab_data()    
            except TypeError:
                return False, -4    
            master_table = self.prepare_table_data(iciciBankChequeStatement, infiChequeStatement, previous_infiChequeStatement)    
        tableSnapshot = TableSnapshot(self.company, self.month, self.year, self.bank, master_table,[],None)
        self.tableSnapshotCollection.add_table_to_colection(tableSnapshot)
        return True, 1

    def save_snapshot_to_table(self, tableSnapshot):
        self.tableSnapshotCollection.add_table_to_colection(tableSnapshot)

    def save_chequeReport_to_collection(self, chequeReportpath):
        infiChequeStatement = InfiChequeStatement()
        if not infiChequeStatement.setPath(chequeReportpath):
            return False
        infiChequeStatement.grab_data()  
        infiChequeStatement.set_year(self.year)
        infiChequeStatement.set_company(self.company)
        self.chequeReportCollection.add_cheque_report_to_collection(infiChequeStatement)  
        return True

    def search(self, masterTableData, searchQuery, searchMode):
        # print(masterTableData)
        final_table = list()
        if searchQuery == "":
            return self.format_table_data(masterTableData)
        if searchMode == "bychqno":
            for each in masterTableData:
                # if(format_chqNo( each['Chq No'])== format_chqNo( searchQuery)):   
                if searchQuery in each['Chq No'].lower(): 
                    final_table.append(each)
        elif searchMode == "bydate":
            for each in masterTableData:
                date = dateutil.parser.parse(each['Bank Date'], dayfirst=True).strftime("%d/%m/%Y")
                stmtdate = date.split('/')
                querydate = searchQuery.split('/')
                if stmtdate[0] == querydate[0]:
                    if stmtdate[1] == querydate[1]:
                        if stmtdate[2][-2:] == querydate[2][-2:]:
                            final_table.append(each)
        elif searchMode == "bychqamt":
            for each in masterTableData:
                if searchQuery in str(each["Credit"]) or searchQuery in str(each["Debit"]):
                    final_table.append(each)
        else: final_table = masterTableData
        return self.format_table_data(final_table)

    def get_header(self):
        return ['Bank Date', 'Bank Narration', 'Chq No','Party Name' ,'Infi Date','Credit', 'Debit', 'Closing Balance' ]

    def export_to_excel(self, folder_url, snapshot):
        k=0
        k2=0
        k3=0
        k4=0
        k5=0
        export_workbook = xlwt.Workbook()
        export_worksheet = export_workbook.add_sheet('Sheet_1')
        selected_worksheet = export_workbook.add_sheet('Selected')
        unselected_worksheet = export_workbook.add_sheet('Unselected')
        matched_worksheet = export_workbook.add_sheet('Matched CHQReceipts(HDFC)')
        unmatched_worksheet = export_workbook.add_sheet('Unmatched CHQReceipts(HDFC)')
        row_color_select = xlwt.easyxf('pattern: pattern solid, fore_colour light_green')
        row = export_worksheet.row(k)
        row_s2 = selected_worksheet.row(k2)
        row_s3 = unselected_worksheet.row(k3)
        row_s4 = matched_worksheet.row(k4)
        row_s5 = unmatched_worksheet.row(k5)        
        j=0
        for each in self.get_header():
            row.write(j,str(each))
            row_s2.write(j,str(each))
            row_s3.write(j,str(each))
            row_s4.write(j,str(each))
            row_s5.write(j,str(each))
            j+=1
        k+=1
        for each in snapshot.get_master_table():
            row = export_worksheet.row(k)
            j=0
            a = k-1
            if a in snapshot.get_master_selected_rows():
                k2+=1
                row_s2 = selected_worksheet.row(k2)
            else:
                k3+=1
                row_s3 = unselected_worksheet.row(k3)
            if(each['Party Name'] != '' and each["Bank Narration"] != '' and each["Bank Narration"][0:7]=="CHQ DEP"):
                k4+=1
                row_s4 = matched_worksheet.row(k4) 
            elif(each["Bank Narration"][0:7]=="CHQ DEP"):
                k5+=1
                row_s5 = unmatched_worksheet.row(k5)      
            for header_item in self.get_header(): 
                cell = each[header_item]
                if a in snapshot.get_master_selected_rows():
                    row.write(j,cell,row_color_select)
                    row_s2.write(j,cell,row_color_select)
                else:    
                    row.write(j,cell)
                    row_s3.write(j,cell)
                if(each['Party Name'] != '' and each["Bank Narration"] != '' and each["Bank Narration"][0:7]=="CHQ DEP"):
                    row_s4.write(j,cell)
                elif(each["Bank Narration"][0:7]=="CHQ DEP"):  
                    row_s5.write(j,cell) 
                j+=1
            k+=1    
        if folder_url!='' and (folder_url.split('.')[-1].lower()!='xls'):
            save_file = folder_url + '/123.xls'
        else:
            save_file =  folder_url
        try:
            export_workbook.save(save_file)  
            master_excel_export_path = save_file
            os.startfile(save_file)
            return True, 0   
        except FileNotFoundError:
            return False, -2     
        except PermissionError:
            return False, -5          
        except Exception as e:
            return False, 99

    def validateIntermediateDaybook(self, path, fromDate, toDate, company):
        path = path[8:]
        self.intermediateDaybook = IntermediateDaybook(path, fromDate, toDate, company)
        return self.intermediateDaybook.validateAndSetValues()

    def generateIntermediateDaybook(self):
        # Step 1: Grab Date => Abstracted
        startDate = self.intermediateDaybook.getFromDate()
        endDate = self.intermediateDaybook.getToDate()
        company = self.intermediateDaybook.getCompany()
        list_of_months = []
        i=1
        tempDate = startDate
        while True:
            month_name = tempDate.strftime('%B')
            month = tempDate.month 
            year = tempDate.year
            list_of_months.append([month_name,year])
            if month == endDate.month and year == endDate.year:
                break
            tempDate = tempDate+relativedelta(months=+1)
        print(list_of_months)
        snapshot_list = []
        banks = ['icici']
        if company=='gokul':
            banks.append('hdfc')
        for bank in banks:
            for [month, year] in list_of_months:
                snapshot = self.tableSnapshotCollection.get_table_from_collection(month,str(year),bank,company) 
                if not snapshot:
                    print("No snapshot for ",month,year,bank,company)
                    return False, -7 , month +' '+ str(year) + ' ' + bank
                snapshot_list.append(snapshot)   
        # print(snapshot_list)            

        # Step 2: Prepare Consolidated Stmt from startDate to EndDate for MATCH RECEIPTS
        consolidatedReceiptVouchers = ConsolidatedReceiptVouchers(snapshot_list)
        consolidatedReceiptVouchers.prepare_df(startDate,endDate, mode="matched_cheques")
        # print(consolidatedReceiptVouchers.get_df().head())

        # Step 3: Prepare Consolidated Stmt from startDate to EndDate for PAYMENT RECEIPTS
        consolidatedReceiptVouchers.prepare_df(startDate,endDate, mode="chequeless_receipts")

        # Step 4: Prepare Consolidated Stmt from startDate to EndDate for NON-MATCH and Other RECEIPTS
        consolidatedPaymentVouchers = ConsolidatedPaymentVouchers(snapshot_list)
        consolidatedPaymentVouchers.prepare_df(startDate,endDate)

        self.intermediateDaybook.prepare_daybook(consolidatedReceiptVouchers.get_receipt_with_cheques_df(), consolidatedPaymentVouchers.get_payment_entries_df(), consolidatedReceiptVouchers.get_receipt_without_cheques_df() )
        return True, 1, ''
class FirebaseControls:
    def __init__(self):
        # correction for auto-py-to-exe
        try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        certificate_path = os.path.join(base_path, r"service-account\\recordmatcher-firebase-adminsdk-mfcn7-d0ee2c6bad.json")
        cred = credentials.Certificate(certificate_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://recordmatcher-default-rtdb.firebaseio.com/'
        })
        self.tableSnapshot_ref = db.reference("/tableSnapshot/") 
        self.leftMenu_ref = db.reference('/leftMenu/') 
        self.chequeReport_ref = db.reference('/chequeReport')
    def set_tableSnapshot(self, child, data):
        return self.tableSnapshot_ref.child(child).set(data)
    def remove_tableSnapshot(self, child):
        return self.tableSnapshot_ref.child(child).set({}) 
    def get_tableSnapshot(self):
        return self.tableSnapshot_ref.get() 
    def set_chequeReport(self, child, data):
        return self.chequeReport_ref.child(child).set(data)
    def remove_chequeReport(self, child):
        return self.chequeReport_ref.child(child).set({}) 
    def get_chequeReport(self):
        return self.chequeReport_ref.get()     
    def set_leftMenu_data(self, data):
        return self.leftMenu_ref.set(data)
    def get_leftMenu_data(self):
        return self.leftMenu_ref.get()

# class InfiDaybookModifier:
class IntermediateDaybook:
    path = None
    df = None
    header = None
    valid_ids = None
    id_count = 0

    def __init__(self, path, fromDate, toDate, company):
        self.path = path
        self.toDate = toDate
        self.fromDate = fromDate
        self.company = company
        return 
    def validateAndSetValues(self):
        if validate_path(self.path):
            try:
                self.df = pd.read_excel(self.path)
            except ValueError:
                return False, -8
            self.header = list(self.df.columns)
        else:
            return False, -1  
        try:             
            self.fromDate = datetime.datetime.strptime(self.fromDate, "%d/%m/%Y")
        except ValueError:
            return False, -2   
        try:             
            self.toDate = datetime.datetime.strptime(self.toDate, "%d/%m/%Y")   
        except ValueError:
            return False, -3
        if self.fromDate>=self.toDate:
            return False, -4    
        no_of_months = (self.toDate.year - self.fromDate.year) * 12 + (self.toDate.month - self.fromDate.month)
        if no_of_months>12:
            return False, -5    
        if self.company not in ['gokul','universal','gawel1','gawel2','focus']:
            return False, -6
        try:
            self.grab_data()
        except:
            raise        
        return True, 1    
    def getFromDate(self):
        return self.fromDate    
    def getToDate(self):
        return self.toDate  
    def getCompany(self):
        return self.company            
    def getPath(self):
        return self.path
    def getdf(self):
        return self.df      
    def convert_to_datetime_obj(self, date):
        try:
            val = datetime.datetime.strptime(date, '%d-%m-%Y')     
        except ValueError:
            val = datetime.datetime.strptime(date,'%d-%b-%Y')
        return val    
    def grab_data(self):
        self.df = self.df[self.df['Number'].notna()]
        self.df['Date'] = self.df['Date'].apply(self.convert_to_datetime_obj)
        return
    def prepare_valid_ids_without_bank_receipt_voucher_filtering(self):
        vouchers_with_receipt_df = self.df[(self.df["Voucher Type"]=="Receipt Voucher") & (self.df["Debit Ledger"] == "Cash Book")]
        # valid_ids__without_receipt = vouchers_without_receipt_df['Number'].unique()
        valid_ids__with_receipt = vouchers_with_receipt_df['Number'].unique()
        if valid_ids__with_receipt is []:
            return pd.DataFrame()
        vouchers_without_receipt_df = self.df[((self.df['Voucher Type']!="Receipt Voucher") & (self.df['Voucher Type']!="Payment Voucher"))]
        daybook_wih_fixed_data = self.df[ self.df['Number'].isin(valid_ids__with_receipt)].copy()
        daybook_wih_fixed_data = daybook_wih_fixed_data.append(vouchers_without_receipt_df, ignore_index=True)
        daybook_wih_fixed_data.reset_index(inplace=True, drop=True)
        daybook_wih_fixed_data = daybook_wih_fixed_data[(daybook_wih_fixed_data['Date']>=self.fromDate) & (daybook_wih_fixed_data['Date']<=self.toDate)]
        daybook_wih_fixed_data['Date'] = daybook_wih_fixed_data['Date'].apply(lambda x: str(datetime.datetime.strftime(x, '%d-%m-%Y')))
        daybook_wih_fixed_data.reset_index(inplace=True, drop=True)
        daybook_wih_fixed_data.to_excel("./temp/daybook_wih_fixed_data.xlsx")
        return daybook_wih_fixed_data
    # def prepare_valid_ids_with_bank_receipt_voucher_filtering(self, consolidatedChequeReport, startDate, endDate):
    #     valid_list, filtered_df = consolidatedChequeReport.get_id_list_in_time_range(startDate,endDate)
    #     if valid_list is []:
    #         return pd.DataFrame()
    #     daybook_with_added_data = self.df[ self.df['Number'].isin(valid_list)].copy()
    #     daybook_with_added_data.reset_index(inplace=True, drop=True)
    #     daybook_with_added_data['Debit Ledger'] = daybook_with_added_data.apply(lambda x: filtered_df['Bank Name'][x['Number']] if not pd.isnull(x["Debit Ledger"]) else None, axis=1)
    #     daybook_with_added_data['Date'] = daybook_with_added_data['Number'].apply(lambda x: str(datetime.datetime.strftime(filtered_df['Bank Date'][x], '%d-%m-%Y')))
    #     daybook_with_added_data['Narration'] = daybook_with_added_data.apply(lambda x: x['Narration'] + ' ' + filtered_df['Narration'][x['Number']],axis=1)
    #     daybook_with_added_data.to_excel("./temp/daybook_wih_added_data.xlsx")
    #     return daybook_with_added_data
    def create_id_for_voucher(self, Bank_Name,Date,type='p'):
        bank_letter = Bank_Name[0].upper()
        month_number = str(int(Date.strftime('%m')))
        self.id_count+=1
        return type.upper()+bank_letter+month_number+'-'+str(self.id_count)        
    def prepare_payment_voucher_daybook_entries(self, consolidated_df):
        if consolidated_df.empty:
            return pd.DataFrame()
        row_1_df = pd.DataFrame()
        row_1_df['Number'] = consolidated_df.apply( lambda x: self.create_id_for_voucher(x['Bank Name'],x['Date']), axis=1 )
        consolidated_df['Date'] = consolidated_df['Date'].apply( lambda x: str(x.strftime("%d-%m-%Y")))    
        row_1_df['Date'] = consolidated_df['Date']
        row_1_df['Voucher Type'] = "Payment Voucher"
        row_1_df['Debit Ledger'] =  PAYMENT_INTERMEDIARY_TALLY_LEDGERNAME
        row_1_df['Debit Amount'] =  consolidated_df['Amount']
        row_1_df['Narration'] = consolidated_df['Narration']
        row_2_df = pd.DataFrame()
        row_2_df['Number'] = row_1_df['Number']
        row_2_df['Date'] = consolidated_df['Date']
        row_2_df['Voucher Type'] = "Payment Voucher"
        row_2_df["Credit Ledger"] = consolidated_df["Bank Name"]
        row_2_df["Credit Amount"] = consolidated_df["Amount"]
        row_2_df['Narration'] = consolidated_df['Narration']
        output_df = pd.concat([row_1_df, row_2_df]).sort_index(kind='merge')
        output_df.to_excel('./temp/payment_voucher_only_daybook.xlsx')
        return output_df   
    def prepare_receipt_voucher_without_cheques_daybook_entries(self, consolidated_df):
        if consolidated_df.empty:
            return pd.DataFrame()
        row_1_df = pd.DataFrame()
        row_1_df['Number'] = consolidated_df.apply( lambda x: self.create_id_for_voucher(x['Bank Name'],x['Date'],type='r'), axis=1 )
        row_1_df['Date'] = consolidated_df['Date'].apply( lambda x: str(x.strftime("%d-%m-%Y")))    
        row_1_df['Voucher Type'] = "Receipt Voucher"
        row_1_df['Debit Ledger'] =  consolidated_df["Bank Name"]
        row_1_df['Debit Amount'] =  consolidated_df['Amount']
        row_1_df['Narration'] = consolidated_df['Narration']
        row_2_df = pd.DataFrame()
        row_2_df['Number'] = row_1_df['Number']
        row_2_df['Date'] = row_1_df['Date']
        row_2_df['Voucher Type'] = "Receipt Voucher"
        row_2_df["Credit Ledger"] = RECEIPT_INTERMEDIARY_TALLY_LEDGERNAME
        row_2_df["Credit Amount"] = consolidated_df["Amount"]
        row_2_df['Narration'] = consolidated_df['Narration']
        output_df = pd.concat([row_1_df, row_2_df]).sort_index(kind='merge')
        output_df.to_excel('./temp/receipt_voucher_without_cheques_daybook.xlsx')
        return output_df  
    def prepare_receipt_voucher_with_cheques_daybook_entries(self, consolidated_df):
        if consolidated_df.empty:
            print("Empty consolidatedChequeReceiptVouchers")
            return pd.DataFrame()
        consolidated_df['Narration'] = consolidated_df.apply(lambda x: x['Cheque No.'] if x['Bank Name']==HDFC_TALLY_LEDGERNAME else x['Narration'], axis=1 )
        row_1_df = pd.DataFrame()
        row_1_df['Number'] = consolidated_df.apply( lambda x: self.create_id_for_voucher(x['Bank Name'],x['Date'],type='c'), axis=1 )
        row_1_df['Date'] = consolidated_df['Date'].apply( lambda x: str(x.strftime("%d-%m-%Y")))    
        row_1_df['Voucher Type'] = "Receipt Voucher"
        row_1_df['Debit Ledger'] =  consolidated_df["Bank Name"]
        row_1_df['Debit Amount'] =  consolidated_df['Amount']
        row_1_df['Narration'] = consolidated_df['Narration']   
        row_2_df = pd.DataFrame()
        row_2_df['Number'] = row_1_df['Number']
        row_2_df['Date'] = row_1_df['Date']
        row_2_df['Voucher Type'] = "Receipt Voucher"
        row_2_df["Credit Ledger"] = consolidated_df['Debit Ledger']
        row_2_df["Credit Amount"] = consolidated_df["Amount"]
        row_2_df['Narration'] = consolidated_df['Narration']
        output_df = pd.concat([row_1_df, row_2_df]).sort_index(kind='merge')
        output_df.to_excel('./temp/receipt_voucher_with_cheques_daybook.xlsx')
        return output_df   
    def prepare_daybook(self, consolidatedChequeReceiptVouchers, consolidatedBankPaymentVouchers, consolidatedWithoutChequeReceiptVouchers):
        final_daybook = pd.DataFrame()    
        final_daybook = final_daybook.append(self.prepare_valid_ids_without_bank_receipt_voucher_filtering(), ignore_index=True)
        # final_daybook = final_daybook.append(self.prepare_valid_ids_with_bank_receipt_voucher_filtering(consolidatedChequeReport, startDate, endDate), ignore_index=True)
        final_daybook = final_daybook.append(self.prepare_receipt_voucher_with_cheques_daybook_entries(consolidatedChequeReceiptVouchers), ignore_index=True)
        final_daybook = final_daybook.append(self.prepare_payment_voucher_daybook_entries(consolidatedBankPaymentVouchers), ignore_index=True)
        final_daybook = final_daybook.append(self.prepare_receipt_voucher_without_cheques_daybook_entries(consolidatedWithoutChequeReceiptVouchers), ignore_index=True)
        column_list = "Number	Date	Voucher Type	Debit Ledger	Debit Amount	Credit Ledger	Credit Amount	Narration".split('\t')
        final_daybook = final_daybook.reindex(columns=column_list)
        final_daybook.to_excel('./temp/final_daybook.xlsx', index=False)
        return final_daybook

class ConsolidatedReceiptVouchers:
    def __init__(self, snapshot_list):
        self.snapshot_list = snapshot_list
        self.receipt_with_cheques = pd.DataFrame()
        self.receipt_without_cheques = pd.DataFrame()
        self.main_df = pd.DataFrame()

    def prepare_df(self, startDate, endDate, mode="matched_cheques"):    
        self.main_df = pd.DataFrame()
        for each in self.snapshot_list:
            temp_df = pd.DataFrame(each.get_master_table())
            if not temp_df.empty:
                if each.get_company()=='universal':
                    bank_name = ICICI_TALLY_LEDGERNAME_UNI
                elif each.get_bank() =='icici':
                    bank_name = ICICI_TALLY_LEDGERNAME_GOK
                else: 
                    bank_name = HDFC_TALLY_LEDGERNAME
                temp_df['Bank Name'] = bank_name         
                self.main_df = self.main_df.append(temp_df, ignore_index=True)
        if self.main_df.empty:
            return       
        
        self.main_df.to_excel('./temp/test123.xlsx')
         
        self.main_df.drop('Closing Balance', axis='columns', inplace=True)
        self.main_df.drop('Infi Date', axis='columns', inplace=True)
        self.main_df = self.main_df[ ~(self.main_df['meta'].isna())]
        # self.main_df = self.main_df[ (self.main_df['Party Name'].isna())]
        self.main_df.drop('meta', axis='columns', inplace=True)
        if mode == "matched_cheques":
            self.main_df = self.get_receipts_with_cheque_entries()
        else:
            self.main_df = self.get_receipts_without_cheque_entries()
        self.main_df.drop('Debit', axis='columns', inplace=True)
        self.main_df['Date'] = self.main_df['Bank Date'].map( lambda x: self.process_date(x))
        self.main_df.drop('Bank Date', axis='columns', inplace=True)
        self.main_df = self.main_df[ (self.main_df['Date']>=startDate) & (self.main_df['Date']<=endDate) ]
        self.main_df.rename(columns={'Chq No': 'Cheque No.', 'Bank Narration':'Narration', 'Credit':'Amount', 'Party Name': 'Debit Ledger'}, inplace=True)

        self.main_df.reset_index(inplace=True, drop=True) 
        if mode == "matched_cheques":
            self.main_df.to_excel('./temp/receipt cheque voucher consolidated.xlsx')
            self.receipt_with_cheques = self.main_df    
            print('Prepared consolidated Receipt Vouchers df')
        else:
            self.main_df.to_excel('./temp/receipt voucher without cheques daybook.xlsx') 
            self.receipt_without_cheques = self.main_df   
            print('Prepared consolidated Receipt Vouchers without cheques df')

    def process_date(self, val):
        try:
            return dateutil.parser.parse(val, dayfirst=True)
        except :
            print("Cannot process invalid date value: '", val, "'. Skipping")
            return np.NaN
    def get_receipts_without_cheque_entries(self):
        self.main_df = self.main_df.replace(r'^\s*$', np.NaN, regex=True)
        new_df = self.main_df.dropna(subset=['Credit'])
        new_df =  new_df[ ~(new_df['Bank Narration'].str.contains("CHQ DEP - MICR 1 CLG - KOTTARAKARA", regex=False) ) & ~(new_df['Bank Narration'].str.contains("CLG/", regex=False)) ]
        return new_df
    def get_receipts_with_cheque_entries(self):
        self.main_df = self.main_df.replace(r'^\s*$', np.NaN, regex=True)
        new_df = self.main_df[ (self.main_df['Credit'].notna())]
        new_df =  new_df[ (new_df['Bank Narration'].str.contains("CHQ DEP - MICR 1 CLG - KOTTARAKARA", regex=False) ) | (new_df['Bank Narration'].str.contains("CLG/", regex=False)) ]
        new_df["Party Name"] = new_df["Party Name"].replace(np.NaN, RECEIPT_INTERMEDIARY_TALLY_LEDGERNAME, regex=True)  
        return new_df

    def get_receipt_without_cheques_df(self):
        return self.receipt_without_cheques
    def get_receipt_with_cheques_df(self):
        return self.receipt_with_cheques    
   
class ConsolidatedPaymentVouchers:
    def __init__(self, snapshot_list):
        self.snapshot_list = snapshot_list
        self.paymentVoucherDF = pd.DataFrame()
        self.main_df = pd.DataFrame()

    def prepare_df(self, startDate, endDate):    
        self.main_df = pd.DataFrame()
        for each in self.snapshot_list:
            temp_df = pd.DataFrame(each.get_master_table())
            if not temp_df.empty:
                if each.get_company()=='universal':
                    bank_name = ICICI_TALLY_LEDGERNAME_UNI
                elif each.get_bank() =='icici':
                    bank_name = ICICI_TALLY_LEDGERNAME_GOK
                else: 
                    bank_name = HDFC_TALLY_LEDGERNAME
                temp_df['Bank Name'] = bank_name         
                self.main_df = self.main_df.append(temp_df, ignore_index=True)
        if self.main_df.empty:
            return        
        self.main_df = self.main_df.replace(r'^\s*$', np.NaN, regex=True)
        self.main_df.drop('Closing Balance', axis='columns', inplace=True)
        self.main_df.drop('Infi Date', axis='columns', inplace=True)
        self.main_df.drop('Party Name', axis='columns', inplace=True)
        self.main_df = self.main_df.dropna(subset=['Debit'])
        # self.main_df.drop('Credit', axis='columns', inplace=True)
        self.main_df.drop('Chq No', axis='columns', inplace=True)
        self.main_df['Date'] = self.main_df['Bank Date'].map( lambda x: self.process_date(x))
        self.main_df = self.main_df[ (self.main_df['Date']>=startDate) & (self.main_df['Date']<=endDate) ]
        self.main_df.drop('Bank Date', axis='columns', inplace=True)
        self.main_df.drop('meta', axis='columns', inplace=True)
        self.main_df.rename(columns={'Bank Date': 'Date', 'Bank Narration':'Narration', 'Debit':'Amount', }, inplace=True)
        # print(self.main_df.head())

        self.main_df.reset_index(inplace=True, drop=True)   
        self.main_df.to_excel('./temp/payment voucher consolidated.xlsx')    
        self.paymentVoucherDF = self.main_df
    def process_date(self, val):
            try:
                final_val = dateutil.parser.parse(val, dayfirst=True)
                # print(val, final_val)
                return final_val
            except :
                raise
    def get_payment_entries_df(self):
        return self.paymentVoucherDF
