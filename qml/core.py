import xlrd
import xlwt
import os
import datetime, pytz
import math
import pickle
import time

APP_NAME = "Infi Hdfc Analyzer"
# print = sg.Print

def get_current_time():
    t = datetime.datetime.now(pytz.timezone('Asia/Kolkata')) 
    formatted_time = str(t.hour)+':'+str(t.minute)+' '+str(t.day)+'/'+str(t.month)+'/'+str(t.year)
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
        self.bank = None
        self.company = None
        self.save_path = None
        # self.createSavePath()
        return         
    def createSavePath(self):
        self.save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\Snapshot_"+self.month+'_'+self.year+'_'+self.bank
        return
    def update_last_edited_time(self):
        self.last_edited_time = get_current_time()  
    def get_last_edited_time(self):
        return self.last_edited_time  
    def get_year(self):
        return self.year
    def get_bank(self):
        return self.bank 
    def get_company(self):
        return self.company 
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

    def compare_date(self,date1, date2):
        # date1 format dd-mm-yyyy
        # date2 format dd/mm/yy or dd-bbb-yyyy
        assert datetime.datetime.strptime(date1, "%d-%m-%Y")
        try:
            date2 = datetime.datetime.strptime(date2, "%d/%m/%y")
        except ValueError:
            date2 = datetime.datetime.strptime(date2, "%d-%b-%Y")
        date2 = date2.strftime("%d/%m/%y")
        # print(date1, date2)
        date1 = date1.split('-')
        date1[2] = date1[2][2:]
        date2 = date2.split('/')
        if date1[2] == date2[2]:
            if date1[1] == date2[1]:
                if date1[0] >= date2[0]:
                    return False
                else:
                    return True
            elif date1[1] > date2[1]:
                return False
            else:
                return True
        elif date1[2] > date2[2]:
            return False
        else:
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
            infiTransDate = each[1]
            # print(infiTransDate, bank_date) 
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
        # transDate, transNo, book, code, ledgerName, chqNo, chqDate, transtypeVoucher, narration, debit, credit = None
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
            date= datetime.datetime.strptime(date,'%d-%b-%Y')
        except ValueError:
            date = datetime.datetime.strptime(date,'%d/%m/%Y')
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

    def __init__(self,company,month,year,bank,master_table, master_selected_rows, master_excel_export_path):
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

    def update_last_edited_time(self):
        self.last_edited_time = get_current_time()
    def get_master_table(self):
        return self.master_table
    def get_master_selected_rows(self):
        return self.master_selected_rows
    def get_master_excel_export_path(self):
        return self.master_excel_export_path  
    def get_month(self):
        return self.month
    def get_year(self):
        return self.year
    def get_bank(self):
        return self.bank 
    def get_company(self):
        return self.company      
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
    years = ['2019','2020','2021','2022','2023']
    banks = ['hdfc', 'icici']
    companies = ['gokul','universal']
    cheque_report_dict = {}
    def __init__(self):
        return
    def get_years(self):
        return self.years   
    def load_cheque_report_collection(self):
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
            print(self.cheque_report_dict)
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
    def add_cheque_report_to_colection(self, chequeReport,  year,  company):
        ref = self.get_dict_reference(year,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('adding chequeReport to ',year,company,'to chequeReportCollection with ref',ref)    
        self.cheque_report_dict[ref] = chequeReport
        status, code = self.save_cheque_report_collection()
        if status:
            print('ChequeReportCollection save success!!')
        else:
            print('ChequeReportCollection save fail with code ',code)   
        return True   
    def get_cheque_report_from_collection(self,  year, company):
        ref = self.get_dict_reference(year,company)
        if not ref:
            return None
        try:
            return self.cheque_report_dict[ref]
        except KeyError:
            return None        

class TableSnapshotCollection:
    save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.fil"
    table_list = {}
    months = ['april','may','june','july','august','september','october','november','december','january', 'february', 'march']
    years = ['2019','2020','2021','2022','2023']
    banks = ['hdfc', 'icici']
    companies = ['gokul','universal']

    def __init__(self):
        return
    def get_months(self):
        return self.months
    def get_years(self):
        return self.years    
    def load_table(self):
        try:
            with open(self.save_path, 'rb') as f:
                data_loaded = pickle.load(f)
                self.table_list = data_loaded
        except FileNotFoundError:
            return False
        print('LOAD OK')    
        self.print_table()    
        return
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
        self.print_table()    
        return True, 0        
    def print_table(self):
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
    def add_table_to_colection(self, tableSnapshot, month, year, bank, company):
        ref = self.get_dict_reference(month,year,bank,company)
        if not ref:
            print('FAIL: No reference for key in tabledict generated')
            return False
        print('adding table to ',month,year,bank,company,'to table list with ref',ref,'.')    
        self.table_list[ref] = tableSnapshot
        status, code = self.save_table()
        if status:
            print('TableCollection save success!!')
        else:
            print('TableCollection save fail with code ',code)   
        return True   
    def get_table_from_collection(self, month, year, bank,company):
        ref = self.get_dict_reference(month,year,bank,company)
        if not ref:
            return None
        try:
            return self.table_list[ref]
        except KeyError:
            return None

def begin_exit_procedure(master_table, master_selected_rows, master_excel_export_path, save_path,window, default_save_path, tableSnapshot):
    data_to_save = prepare_save_data(master_table, master_selected_rows, save_path, master_excel_export_path)
    try:
        with open(default_save_path, 'wb') as f:
            pickle.dump(data_to_save, f)
        print('Saved at default path')
    except FileNotFoundError:
        print("Default path NOT EXIST")
    if(tableSnapshot):
        print('master_selected_rows for saving : ',master_selected_rows)
        tableSnapshot.set_master_selected_rows(master_selected_rows) 
        tableSnapshot.set_master_excel_export_path(master_excel_export_path)
        tableSnapshotCollection = TableSnapshotCollection()
        tableSnapshotCollection.load_table()
        tableSnapshotCollection.add_table_to_colection(tableSnapshot, tableSnapshot.get_month(), tableSnapshot.get_year(), tableSnapshot.get_bank(), tableSnapshot.get_company())
        print('TableSnapshot saved at collection from sec window')
    if save_path and validate_save_path(save_path):
        print('save_path', save_path)
        if(sg.PopupYesNo("Do you want to save at \"" + save_path + "\"", title='Save File?',keep_on_top=True )=="Yes"):
            try:
                with open(save_path, 'wb') as f:
                    pickle.dump(data_to_save, f)
                print('OK')
            except FileNotFoundError:
                print("FILE NOT EXIST")        
    # else:
        # k = sg.PopupYesNo("Do you want to save?", title='Save File?',keep_on_top=True )
        # print('SAVE?:', k)
        # if(k=="Yes"): 
            # print('RETURN WITH FALSE')
            # return False
    window.close()    
    return True 

hdfcBankChequeStatement = HDFCBankChequeStatement()
iciciBankChequeStatement = ICICIBankChequeStatement()

chq_rep_save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\appendix.ini"

def get_chq_report_loc():
    try:
        with open(chq_rep_save_path, 'rb') as f:
            data_loaded = pickle.load(f)
            path_dict = data_loaded
            return path_dict
    except FileNotFoundError:
        print('appendix not found')
        return {}        
    return {} 
def save_chq_report_loc(path_dict):
    try:
        with open(chq_rep_save_path, 'wb') as f:
            pickle.dump(path_dict, f)
        print('Chq Report Location saved.')
    except FileNotFoundError:
        print(chq_rep_save_path,'does not exist.')  