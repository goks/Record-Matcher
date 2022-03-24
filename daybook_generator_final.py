import xlrd
import xlwt
import os.path

class TallyVoucher:
    DAYBOOK_START_ROW = 1
    LEDGERMAP_START_ROW = 0
    TOTAL_INPUT_COLS=34738
    INV_COL = 0
    DATE_COL = 1
    VOUCH_TYPE_COL = 2
    DEBIT_LED_COL = 3
    DEBIT_AMT_COL = 4
    CREDIT_LED_COL = 5
    CREDIT_AMT_COL = 6
    NARRATION_COL = 7
    BANK_DATE_COL = 8
    FILLERDATA_PURCHASE = 5
    FILLERDATA_RECEIPT = 11
    FILLERDATA_PAYMENT = 9
    FILLERDATA_JOURNAL = 13
    FILLERDATA_SALES_RETURN = 15
    FILLERDATA_PURCHASE_LEDGER = 7
    FILLERDATA_SALES_RETURN_LEDGER = 19
    FILLERDATA_DAYBOOK = 17

    def __init__(self, daybook_path):

        assert os.path.isfile(r'.\supporting_data\ledger_map.xlsx')
        assert os.path.isfile(r'.\supporting_data\filler_data.xls')

        self.daybook_workbook = xlrd.open_workbook('Daybook.xlsx')
        self.daybook_worksheet = self.daybook_workbook.sheet_by_index(0)

        self.ledgermap_workbook = xlrd.open_workbook(r'supporting_data\ledger_map.xlsx')
        self.ledgermap_worksheet = self.ledgermap_workbook.sheet_by_index(0)

        self.fillerdata_workbook = xlrd.open_workbook(r'supporting_data\filler_data.xls')
        se;f.fillerdata_worksheet = fillerdata_workbook.sheet_by_index(0)

        xml_file = open("Step_3_Daybook.xml","w")#write mode

        tally_ledger_name_list = []
        tally_ledger_name_list_occurence1 = []
        infi_ledger_name_list = []
        tally_gst_purchase_modification_ledger_names = ["5% GST Purchase", "0% GST Purchase", "12% GST Purchase", "18% GST Purchase"]
        return
    def load_ledger_map(self):
        i=self.LEDGERMAP_START_ROW
        try:
            while True:
                self.tally_ledger_name_list.append(str(self.ledgermap_worksheet.cell(i,1).value))
                self.infi_ledger_name_list.append(str(self.ledgermap_worksheet.cell(i,0).value))
                i+=1    
        except IndexError:
            pass        
        for each in self.tally_ledger_name_list:
            if each not in self.tally_ledger_name_list_occurence1:
                self.tally_ledger_name_list_occurence1.append(each)
        if(len(self.tally_ledger_name_list) == len(self.infi_ledger_name_list)):
            print("Ledgermap load OK, ",len(self.tally_ledger_name_list)," entries loaded.")
            return
        else:
            print("Ledgermap load fail")
            exit()

class TallyVoucherSupportFunctions:
    def remove_escape_char(self, input_str):
        translation_dict = {}
        translation_dict.update({ chr(char):None for char in range(1,32) })
        output_str = input_str.translate(translation_dict)
        return output_str

    def remove_ampersand_and_next_line(self,input_str):
        output_str = input_str.replace('&amp;','&')
        output_str = output_str.replace('&','&amp;')
        output_str = output_str.replace('\n','')
        return output_str    

    def format_date(self, input_date):
        output_date = input_date.split('-')
        output_date.reverse()
        output_date = ''.join(output_date)
        return output_date

    def format_date_type2(self, input_date):
        output_date = input_date.split('/')
        output_date.reverse()
        if(len(output_date[0])==2):
            output_date[0] = '20'+output_date[0]
        output_date = ''.join(output_date)
        return output_date

    def process_narration(narration, inv_no):
        temp =  narration.split(',')
        orig_bill_no = temp[1]
        orig_bill_no = orig_bill_no.split(':')[1]
        new_narration = "Infi Inv.No: " + inv_no +","+ temp[2]
        return new_narration, orig_bill_no    

    def classify_purchase_type(inv_no):
        if(inv_no[0] == 'I'):
            return "GST Purchase-Interstate"
        if(inv_no[0] == 'G'):
            return "GST Purchase-Local"   
        else:
            return "Purchase"    

    def convert_GST_to_IGST(ledger_name):
        new_name = ledger_name.split()
        new_name[1]= 'I'+new_name[1]
        return ' '.join(new_name)    
