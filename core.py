from time import strftime
from typing_extensions import final
import xlrd
import xlwt
import os
import datetime, pytz
import pickle
import locale
locale.setlocale(locale.LC_NUMERIC, 'hi_IN')
from copy import deepcopy

# Fix for opening xlsx
xlrd.xlsx.ensure_elementtree_imported(False, None)
xlrd.xlsx.Element_has_iter = True

APP_NAME = "Infi Hdfc Analyzer"

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
    def set_master_table(self, table):
        self.master_table = table
        return
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
    save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.filv2"
    save_path_old = os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableSnapshotCollection.fil"
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
    def rename_old_save_path(self):
        os.rename(self.save_path_old,self.save_path_old+'_000')        
    def load_table(self):
        print(self.save_path)
        try:
            with open(self.save_path, 'rb') as f:
                data_loaded = pickle.load(f)
                self.table_list = data_loaded
        except FileNotFoundError:
            return False
        print('LOAD OK')    
        self.print_table()    
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
        self.print_table()    
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

class TableOperations:
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
    
    def get_table_from_collection(self, month, year, bank, company):
        self.month = month
        self.year = year
        self.bank = bank
        self.company = company
        snapshot = self.tableSnapshotCollection.get_table_from_collection(month,year,bank,company) 
        if not snapshot:
            return snapshot,'', '', ''
        credit_bal = 0.0
        debit_bal = 0.0       
        master_table = snapshot.get_master_table()
        for each in master_table:
            if(each['Credit'] != ''):
                credit_bal+=float(each['Credit'])
            if(each['Debit'] != ''):
                debit_bal+=float(each['Debit'])
        credit_bal = locale.format_string("%.2f", credit_bal, grouping=True)  
        debit_bal =  locale.format_string("%.2f", debit_bal, grouping=True)  
        return snapshot, self.format_table_data(master_table), credit_bal, debit_bal

    def format_table_data(self, _tableData):
        tableData = deepcopy(_tableData)
        for each in tableData:
            if(each['Credit'] != ''):
                each['Credit'] = locale.format_string("%.2f", float(each['Credit']), grouping=True)
            if(each['Debit'] != ''):
                each['Debit'] = locale.format_string("%.2f", float(each['Debit']), grouping=True)
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

    def prepare_table_data(self, statementObj, infiChequeStatement):
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
                match_list = infiChequeStatement.findMatchByChequeNumber(bank_entry[2], bank_entry[5], bank_entry[0])
                # if len(match_list)>1:
                #     print("match_list: ",match_list)
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
                            table_row['Credit'] = bank_entry[4]
                            table_row['Debit'] = bank_entry[5]
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
                            table_row['Credit'] = ""
                            table_row['Debit'] = bank_entry[5]
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
                    table_row['Credit'] = bank_entry[4]
                    table_row['Debit'] = bank_entry[5]
                    table_row['Closing Balance'] = bank_entry[6]
                    table_row['meta'] = ""                    
                    final_table.append(table_row)      

        elif(self.bank=='icici'):
            bank_statement = statementObj.getEntryList()
            final_table = []
            for bank_entry in bank_statement:
                if(bank_entry[4]!=None or bank_entry[4] != ''):
                    match_list = infiChequeStatement.findMatchByChequeNumber(bank_entry[4], bank_entry[7], bank_entry[2])
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
                            table_row['Party Name'] = bank_entry[3]
                            table_row['Infi Date'] = bank_entry[0]
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

    def convert_old_schema_to_new_schema(self):
        oldTableSnapshotCollection = TableSnapshotCollection()
        if not oldTableSnapshotCollection.load_old_table():
            print('No old table snapshot found')
            return False
        collection = oldTableSnapshotCollection.get_table_list()
        # for snapshot in collection:
        for key,snapshot in collection.items():    
            master_table = snapshot.get_master_table()
            root_dict = []
            for row in master_table:
                row_dict={}
                row_dict['Bank Date'] = row[0]
                row_dict['Bank Narration'] = row[1]
                row_dict['Chq No'] = row[2]
                row_dict['Party Name'] = row[3]
                row_dict['Infi Date'] = row[4]
                row_dict['Credit'] = row[5]
                row_dict['Debit'] = row[6]
                row_dict['Closing Balance'] = row[7]
                row_dict['meta'] = row[8]
                root_dict.append(row_dict)  
            snapshot.set_master_table(root_dict) 
            self.tableSnapshotCollection.add_table_to_colection(snapshot, snapshot.get_month(), snapshot.get_year(), snapshot.get_bank(), snapshot.get_company())
        print('Renaming old file')
        oldTableSnapshotCollection.rename_old_save_path()
        print('Reloading table snapshot collection')
        if self.tableSnapshotCollection.load_table():
            print('TablesnapshotCollection reload success!!')
        return True
        
    def add_snapshot_to_table(self, statement_path):
        if self.month in ['january', 'february', 'march']:
            financial_year = str(int(self.year)-1)
        else:
            financial_year = self.year    
        infiChequeStatement=self.chequeReportCollection.get_cheque_report_from_collection(financial_year,self.company)
        if not infiChequeStatement:
            return False, -1
        if self.bank == 'hdfc':
            hdfcBankChequeStatement = HDFCBankChequeStatement()
            if not hdfcBankChequeStatement.setPath(statement_path):
                return False, -3
            try:
                hdfcBankChequeStatement.grab_data()    
            except TypeError:
                return False, -3                    
            master_table = self.prepare_table_data(hdfcBankChequeStatement, infiChequeStatement)    
        else:
            iciciBankChequeStatement = ICICIBankChequeStatement()
            if not iciciBankChequeStatement.setPath(statement_path):
                return False, -4
            try:
                iciciBankChequeStatement.grab_data()    
            except TypeError:
                return False, -4    
            master_table = self.prepare_table_data(iciciBankChequeStatement, infiChequeStatement)    
        tableSnapshot = TableSnapshot(self.company, self.month, self.year, self.bank, master_table,[],None)
        self.tableSnapshotCollection.add_table_to_colection(tableSnapshot, self.month, self.year, self.bank, self.company)
        return True, 1

    def save_snapshot_to_table(self, tableSnapshot):
        self.tableSnapshotCollection.add_table_to_colection(tableSnapshot, self.month, self.year, self.bank, self.company)

    def save_chequeReport_to_collection(self, chequeReportpath):
        infiChequeStatement = InfiChequeStatement()
        if not infiChequeStatement.setPath(chequeReportpath):
            return False
        infiChequeStatement.grab_data()  
        self.chequeReportCollection.add_cheque_report_to_colection(infiChequeStatement,self.year,self.company)  
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
                stmtdate = each['Bank Date'].split('/')
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


    #     self.chq_rep_save_path = os.getenv('APPDATA')+'\\'+APP_NAME+"\\appendix.ini"

    # def get_chq_report_loc(self):
    #     try:
    #         with open(self.chq_rep_save_path, 'rb') as f:
    #             data_loaded = pickle.load(f)
    #             path_dict = data_loaded
    #             return path_dict
    #     except FileNotFoundError:
    #         print('appendix not found')
    #         return {}        
    #     return {} 
    # def save_chq_report_loc(self, path_dict):
        # try:
        #     with open(self.chq_rep_save_path, 'wb') as f:
        #         pickle.dump(path_dict, f)
        #     print('Chq Report Location saved.')
        # except FileNotFoundError:
        #     print(self.chq_rep_save_path,'does not exist.')  

    def show_opening_window(self):
        chequeReportCollection = ChequeReportCollection()
        if chequeReportCollection.load_cheque_report_collection():
            print('ChequeReportCollection load success!!')
       
        tableSnapshot = None
        infi_path_dict = {}
        def update_leftcolumn(values):
            if values['radio_Gokul']:
                company = 'Gokul'
            else:
                company= 'Universal'    
            if values['radio_HDFC']:
                bank = 'hdfc'
            else:
                bank = 'icici' 
            try:
                month = values['month_list'][0]
                year = values['year_list'][0]
            except IndexError:
                return None,bank,company
            window['right_col_title1'].update(' ' + month + ' ' + year)
            tableSnapshot = tableSnapshotCollection.get_table_from_collection(month,year,bank,company)
            if tableSnapshot:
                window['existing_data_tb' ].update('Yes')
                window['show_table_but'].update(disabled=False)
                window['lastsave_data_tb'].update(tableSnapshot.get_last_edited_time())
                # print('master_selected_rows',tableSnapshot.get_master_selected_rows())
                return tableSnapshot,bank,company
            else:
                window['existing_data_tb' ].update('No')
                window['lastsave_data_tb'].update('None')
                window['show_table_but'].update(disabled=True)
                return None,bank,company   
        infi_path_dict = get_chq_report_loc()
        company = None
        while True:
            event, values = window.read()
            # print(event,values)
            if event in [None,'Exit']:	# if user closes window or clicks cancel
                window.SaveToDisk(save_path)
                break
            elif event == "Change Cheque Report Dir":
                window.SaveToDisk(save_path)
                window.close()
                show_cheque_report_window()
            elif event is 'table_save_but':
                if values['radio_Gokul']:
                    company = 'Gokul'
                else:
                    company= 'Universal'
                try:
                    month = values['month_list'][0]
                    year = values['year_list'][0]
                except IndexError:
                    continue  
                # print(month,year,company)
                if sg.PopupYesNo('Do you want to save the table for '+ month + ' '+ year+' for '+company) != 'Yes':
                    continue
                fail=False
                # window['infi_path'].update(text_color="#000000")
                infiChequeStatement=chequeReportCollection.get_cheque_report_from_collection(year,company)
                if not infiChequeStatement:
                    sg.popup_error('No cheque report found for company '+company + ' for year ' + year + '.') 
                    continue   
                window['statement_path'].update(text_color="#000000")            
                HDFC_statement = ICICI_statement = None                
                if values['radio_HDFC']:
                    HDFC_statement = values['statement_path']
                    if not hdfcBankChequeStatement.setPath(HDFC_statement):
                        window['statement_path'].update(text_color="#FF0000")
                        fail=True
                else:
                    ICICI_statement = values['statement_path']
                    if not iciciBankChequeStatement.setPath(ICICI_statement):
                        window['statement_path'].update(text_color="#FF0000")
                        fail=True                 
                if fail:
                    continue
                window['progbar'].update_bar(10)
                window.refresh()
                # infiChequeStatement.grab_data()
                window['progbar'].update_bar(20)
                window.refresh()
                if( HDFC_statement ):
                    hdfcBankChequeStatement.grab_data()
                    bank='HDFC'
                else:
                    iciciBankChequeStatement.grab_data()   
                    bank='ICICI'
                window['progbar'].update_bar(40)
                window.refresh()
                master_table = prepare_table_data(bank, infiChequeStatement)
                window['progbar'].update_bar(60)
                window.refresh()
                tableSnapshot = TableSnapshot(company, month, year, bank, master_table,[],None)
                tableSnapshotCollection.add_table_to_colection(tableSnapshot,month,year,bank,company)
                window['progbar'].update_bar(80)
                window.refresh() 
                window['progbar'].update_bar(100)
                window.refresh()
                tableSnapshot,bank,company = update_leftcolumn(values)
            elif event is 'table_del_but':
                try:
                    month = values['month_list'][0]
                    year = values['year_list'][0]
                except IndexError:
                    continue 
                if values['radio_HDFC']:
                    bank = 'hdfc'
                else:
                    bank = 'icici'     
                if sg.PopupYesNo('Delete table '+ month + ' '+ year + '?') != 'Yes':
                    continue
                if not tableSnapshotCollection.delete_table_from_collection(month,year,bank,company):
                    print('Deletion failed.')
                    continue
                tableSnapshot,bank,company = update_leftcolumn(values)
            elif event in ['month_list', 'year_list', 'radio_HDFC','radio_ICICI','radio_Gokul','radio_Universal']:  
                tableSnapshot,bank,company = update_leftcolumn(values)
            elif event is 'continuePrev_but':
                window.close()
                show_second_window(True, previous_path=(os.getenv('APPDATA')+'\\'+APP_NAME+"\\tableData.fil"))
            elif event is 'show_table_but':
                window.SaveToDisk(save_path)
                window.close()
                show_second_window(bank=bank, tableSnapshot=tableSnapshot)
                break 
            # elif event is 'enable_but':
                # print("Enabling buttons")
                # window['infi_path'].update(disabled = False)
                # window['filebrowse_but'].update(disabled = False)
            # elif event is 'import_but':
            #     fail=False
            #     window['infi_path'].update(text_color="#000000")
            #     window['statement_path'].update(text_color="#000000")            
            #     if not infiChequeStatement.setPath(values['infi_path']):
            #         window['infi_path'].update(text_color="#FF0000")
            #         fail=True
            #     HDFC_statement = ICICI_statement = None                
            #     if values['radio_HDFC']:
            #         HDFC_statement = values['statement_path']
            #         if not hdfcBankChequeStatement.setPath(HDFC_statement):
            #             window['statement_path'].update(text_color="#FF0000")
            #             fail=True
            #     else:
            #         ICICI_statement = values['statement_path']
            #         if not iciciBankChequeStatement.setPath(ICICI_statement):
            #             window['statement_path'].update(text_color="#FF0000")
            #             fail=True                                 
            #     if fail:
            #         continue
            #     window['progbar'].update_bar(10)
            #     window.refresh()
            #     infiChequeStatement.grab_data()
            #     window['progbar'].update_bar(50)
            #     window.refresh()
            #     if( HDFC_statement ):
            #         hdfcBankChequeStatement.grab_data()
            #         bank='HDFC'
            #     else:
            #         iciciBankChequeStatement.grab_data()   
            #         bank='ICICI'
            #     window['progbar'].update_bar(100)
            #     window.refresh()
            #     window['next_but'].update(disabled=False)
            # if event is 'next_but':
            #     window.SaveToDisk(save_path)
            #     window.close()
            #     show_second_window(bank=bank)
            #     break 
        # window.close()

