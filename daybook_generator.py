import xlrd
import xlwt
import os.path

def remove_escape_char(input_str):
    translation_dict = {}
    translation_dict.update({ chr(char):None for char in range(1,32) })
    output_str = input_str.translate(translation_dict)
    return output_str

def remove_ampersand_and_next_line(input_str):
    output_str = input_str.replace('&amp;','&')
    output_str = output_str.replace('&','&amp;')
    output_str = output_str.replace('\n','')
    return output_str    

def format_date(input_date):
    output_date = input_date.split('-')
    output_date.reverse()
    output_date = ''.join(output_date)
    return output_date

def format_date_type2(input_date):
    output_date = input_date.split('/')
    output_date.reverse()
    if(len(output_date[0])==2):
        output_date[0] = '20'+output_date[0]
    output_date = ''.join(output_date)
    return output_date

def load_ledger_map():
    i=LEDGERMAP_START_ROW
    try:
        while True:
            tally_ledger_name_list.append(str(ledgermap_worksheet.cell(i,1).value))
            infi_ledger_name_list.append(str(ledgermap_worksheet.cell(i,0).value))
            i+=1    
    except IndexError:
        pass        
    for each in tally_ledger_name_list:
        if each not in tally_ledger_name_list_occurence1:
            tally_ledger_name_list_occurence1.append(each)
    if(len(tally_ledger_name_list) == len(infi_ledger_name_list)):
        print("Ledgermap load OK, ",len(tally_ledger_name_list)," entries loaded.")
        return
    else:
        print("Ledgermap load fail")
        exit()

def sort_fixed_ledger_names(credit_ledger_name, credit_ledger_amt):
        required_order = tally_ledger_name_list_occurence1
        credit_ledger_name_new = []
        credit_ledger_amt_new = []
        for each in required_order:
            if each in credit_ledger_name:
                ind = credit_ledger_name.index(each)
                amt = credit_ledger_amt[ind]
                credit_ledger_amt_new.append(amt)
                credit_ledger_name_new.append(each)
        # print("credit_ledger_amt_new", credit_ledger_amt_new)        
        # print("credit_ledger_name_new", credit_ledger_name_new)        
        return credit_ledger_name_new, credit_ledger_amt_new  

def insert_tally_header():
    data=fillerdata_worksheet.cell(FILLERDATA_DAYBOOK,0).value
    data = remove_escape_char(data)
    data = remove_ampersand_and_next_line(data)
    xml_file.write(data+'\n') 
    return

def insert_tally_footer():
    data=fillerdata_worksheet.cell(FILLERDATA_DAYBOOK,1).value
    data = remove_escape_char(data)
    data = remove_ampersand_and_next_line(data)
    xml_file.write(data+'\n') 
    return


    
def sale_pass():
    credit_ledger_name = []
    credit_ledger_amt = []
    final_row_no=0
    step_1_workbook = xlwt.Workbook()
    step_1_sheet = step_1_workbook.add_sheet('Sheet_1')

    def insert_sale_Row(row_no):
        row = step_1_sheet.row(row_no)
        row.write(0,date)
        row.write(1,debit_ledger_party)
        row.write(2,inv_no)
        row.write(3,inv_no)
        row.write(4,debit_ledger_party)
        row.write(5,debit_ledger_party)
        row.write(6,debit_ledger_party)
        row.write(7,debit_ledger_party)
        row.write(8,debit_amt)
        row.write(9,inv_no)
        row.write(10,debit_amt)

        ledger_obj_data = ""
        for ledger_name, ledger_amt in zip(credit_ledger_name, credit_ledger_amt):
            ledger_obj_data += fillerdata_worksheet.cell(0,0).value
            ledger_obj_data += ledger_name
            ledger_obj_data += fillerdata_worksheet.cell(0,1).value
            ledger_obj_data += str(ledger_amt)
            ledger_obj_data += fillerdata_worksheet.cell(0,2).value
            ledger_obj_data += str(ledger_amt)
            ledger_obj_data += fillerdata_worksheet.cell(0,3).value
        row.write(11,ledger_obj_data)
        return     

    i=DAYBOOK_START_ROW
    while True:
        try:
            inv_no = daybook_worksheet.cell(i, INV_COL).value
            voucher_type = daybook_worksheet.cell(i, VOUCH_TYPE_COL).value           
            date = daybook_worksheet.cell(i, DATE_COL).value
            if not voucher_type=="Sale":
                i+=1
                continue    
            if(daybook_worksheet.cell(i, DEBIT_LED_COL).value):
                debit_ledger_party = daybook_worksheet.cell(i, DEBIT_LED_COL).value
                debit_amt = -1*float(daybook_worksheet.cell(i, DEBIT_AMT_COL).value)
                narration = daybook_worksheet.cell(i, NARRATION_COL).value
            else:
                credit_ledger = daybook_worksheet.cell(i, CREDIT_LED_COL).value
                credit_amt = daybook_worksheet.cell(i, CREDIT_AMT_COL).value
                credit_ledger_amt.append(credit_amt)
                if credit_ledger in infi_ledger_name_list:
                    credit_ledger_name.append(tally_ledger_name_list[ infi_ledger_name_list.index(credit_ledger) ])                          
                else:
                    print("NOT found:", credit_ledger)
                    credit_ledger_amt.pop()  
            next_row_inv_no = daybook_worksheet.cell(i+1, INV_COL).value
            next_row_voucher_type = daybook_worksheet.cell(i+1, VOUCH_TYPE_COL).value
            if next_row_inv_no!=inv_no or next_row_voucher_type!="Sale":
                credit_ledger_name, credit_ledger_amt = sort_fixed_ledger_names(credit_ledger_name, credit_ledger_amt)
                date = format_date(date)
                insert_sale_Row(final_row_no)
                final_row_no+=1
                debit_ledger_party=""
                debit_amt=""
                credit_ledger_name = []
                credit_ledger_amt = []
            i+=1    
        except IndexError:
            break
    step_1_workbook.save("./intermediate_files/step1_book_sales.xls")  

    # print("Converting to xml data.")
    xml_workbook = xlwt.Workbook()
    xml_sheet1 = xml_workbook.add_sheet('Sheet_1')

    xmlinput_book = xlrd.open_workbook('./intermediate_files/step1_book_sales.xls')
    xmlinput_sheet = xmlinput_book.sheet_by_index(0)

    row = 0
    while True:
        data=""
        try:
            val = xmlinput_sheet.cell(row,0).value
        except IndexError:
            break
        for i in range(0,12):
            data+=fillerdata_worksheet.cell(3,i).value
            try:
                data+=xmlinput_sheet.cell(row,i).value
            except TypeError:
                data+=str(xmlinput_sheet.cell(row,i).value)
        data+=fillerdata_worksheet.cell(3,12).value
        data = remove_escape_char(data)
        data = remove_ampersand_and_next_line(data)
        sheet_row = xml_sheet1.row(row)
        sheet_row.write(0,data)
        xml_file.write(data+'\n') 
        row+=1
    xml_workbook.save('./intermediate_files/step_2_sales.xls')
    print("Sales process task completed. ",row,"written.")

def purchase_pass():
    debit_ledger_name = []
    debit_ledger_amt = []
    final_row_no=0
    step_1_workbook = xlwt.Workbook()
    step_1_sheet = step_1_workbook.add_sheet('Sheet_1')

    def insert_purchase_Row(row_no):
        row = step_1_sheet.row(row_no)
        row.write(0,'"' + voucher_type + '"')
        row.write(1,date)
        row.write(2,narration)
        row.write(3,credit_ledger_party)
        row.write(4,voucher_type)
        row.write(5,orig_bill_no)
        row.write(6,inv_no)
        row.write(7,credit_ledger_party)
        row.write(8,credit_ledger_party)
        row.write(9,credit_ledger_party)
        row.write(10,credit_amt)
        row.write(11,orig_bill_no)
        row.write(12,credit_amt)

        ledger_obj_data = ""
        for ledger_name, ledger_amt in zip(debit_ledger_name, debit_ledger_amt):
            if voucher_type=="GST Purchase-Interstate" and ledger_name in tally_gst_purchase_modification_ledger_names:
                ledger_name = convert_GST_to_IGST(ledger_name)
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_PURCHASE_LEDGER,0).value
            ledger_obj_data += ledger_name
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_PURCHASE_LEDGER,1).value
            ledger_obj_data += str(ledger_amt)
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_PURCHASE_LEDGER,2).value
            ledger_obj_data += str(ledger_amt)
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_PURCHASE_LEDGER,3).value
        row.write(13,ledger_obj_data)
        return     
    # TODO: date format
    i=DAYBOOK_START_ROW
    while True:
        try:
            inv_no = daybook_worksheet.cell(i, INV_COL).value
            voucher_type = daybook_worksheet.cell(i, VOUCH_TYPE_COL).value           
            if not voucher_type=="Purchase":
                i+=1
                continue   
            date = daybook_worksheet.cell(i, DATE_COL).value
            voucher_type = classify_purchase_type(inv_no) 
            if(daybook_worksheet.cell(i, CREDIT_LED_COL).value):
                credit_ledger_party = daybook_worksheet.cell(i, CREDIT_LED_COL).value
                credit_amt = daybook_worksheet.cell(i, CREDIT_AMT_COL).value
                narration = daybook_worksheet.cell(i, NARRATION_COL).value
                narration, orig_bill_no = process_narration(narration, inv_no)
            else:
                debit_ledger = daybook_worksheet.cell(i, DEBIT_LED_COL).value
                debit_amt = -1*float(daybook_worksheet.cell(i, DEBIT_AMT_COL).value)
                debit_ledger_amt.append(debit_amt)
                if debit_ledger in infi_ledger_name_list:
                    debit_ledger_name.append(tally_ledger_name_list[ infi_ledger_name_list.index(debit_ledger) ])      
                else:
                    print("NOT found:", debit_ledger)
                    debit_ledger_amt.pop()  
            next_row_inv_no = daybook_worksheet.cell(i+1, INV_COL).value
            if next_row_inv_no!=inv_no:
                debit_ledger_name, debit_ledger_amt = sort_fixed_ledger_names(debit_ledger_name, debit_ledger_amt)
                # print(debit_ledger_name)
                date = format_date(date)
                insert_purchase_Row(final_row_no)
                final_row_no+=1
                credit_ledger_party=""
                credit_amt=""
                debit_ledger_name = []
                debit_ledger_amt = []
            i+=1    
        except IndexError:
            break
    step_1_workbook.save("./intermediate_files/step1_book_purchase.xls")  

    # print("Converting to xml data.")
    xml_workbook = xlwt.Workbook()
    xml_sheet1 = xml_workbook.add_sheet('Sheet_1')

    xmlinput_book = xlrd.open_workbook('./intermediate_files/step1_book_purchase.xls')
    xmlinput_sheet = xmlinput_book.sheet_by_index(0)

    row = 0
    while True:
        data=""
        try:
            val = xmlinput_sheet.cell(row,0).value
        except IndexError:
            break
        for i in range(0,14):
            data+=fillerdata_worksheet.cell(FILLERDATA_PURCHASE,i).value
            try:
                data+=xmlinput_sheet.cell(row,i).value
            except TypeError:
                data+=str(xmlinput_sheet.cell(row,i).value)
        data+=fillerdata_worksheet.cell(FILLERDATA_PURCHASE,14).value
        data = remove_escape_char(data)
        data = remove_ampersand_and_next_line(data)
        sheet_row = xml_sheet1.row(row)
        sheet_row.write(0,data)
        xml_file.write(data+'\n') 
        row+=1
    xml_workbook.save('./intermediate_files/step_2_purchase.xls')
    print("Purchase process task completed. ",row,"written.")

def payment_voucher_pass():
    final_row_no=0
    step_1_workbook = xlwt.Workbook()
    step_1_sheet = step_1_workbook.add_sheet('Sheet_1')
    bank_date = None
    def insert_receipt_payment_Row(row_no, isReceipt):
        if isReceipt:
            main_ledger = credit_ledger_party
            main_amt = credit_amt
            sub_ledger = debit_ledger_party
            sub_amt = debit_amt
            identifier = "Receipt"
        else:
            main_ledger = debit_ledger_party
            main_amt = debit_amt
            sub_ledger = credit_ledger_party
            sub_amt = credit_amt
            identifier = "Payment"
        row = step_1_sheet.row(row_no)
        row.write(0,date)
        row.write(1,narration)
        row.write(2,inv_no)
        row.write(3,main_ledger)
        row.write(4,main_ledger)
        row.write(5,main_amt)
        row.write(6,sub_ledger)
        row.write(7,sub_amt)
        row.write(8,date)
        row.write(9,date)
        if bank_date:
            bank_date_data = " <BANKERSDATE>" + bank_date + " </BANKERSDATE>"
            row.write(10,bank_date_data)
        else:
            row.write(10,'') 
        row.write(11,main_ledger)
        row.write(12,main_ledger)
        row.write(13,sub_amt)
        # identifier
        row.write(14,identifier)
        return     
    i=DAYBOOK_START_ROW
    while True:
        try:
            inv_no = daybook_worksheet.cell(i, INV_COL).value
            voucher_type = daybook_worksheet.cell(i, VOUCH_TYPE_COL).value       
            date = daybook_worksheet.cell(i, DATE_COL).value
            try:
                temp_data = daybook_worksheet.cell(i, BANK_DATE_COL).value
                if temp_data!= '':
                    bank_date = temp_data
            except IndexError:
                pass    
            isReceipt=None
            if not (voucher_type=="Payment Voucher" or voucher_type=="Receipt Voucher"):
                i+=1
                continue 
            elif(voucher_type=="Receipt Voucher"):
                voucher_type="Receipt"
                isReceipt=True
            else:
                voucher_type="Payment"
                isReceipt=False
            if(daybook_worksheet.cell(i, CREDIT_LED_COL).value):
                credit_ledger_party = daybook_worksheet.cell(i, CREDIT_LED_COL).value
                credit_amt = daybook_worksheet.cell(i, CREDIT_AMT_COL).value
                narration = daybook_worksheet.cell(i, NARRATION_COL).value
                if credit_ledger_party in infi_ledger_name_list:
                    credit_ledger_party = tally_ledger_name_list[ infi_ledger_name_list.index(credit_ledger_party) ]                                             
            elif((daybook_worksheet.cell(i, DEBIT_LED_COL).value)):
                debit_ledger_party = daybook_worksheet.cell(i, DEBIT_LED_COL).value
                debit_amt = -1*float(daybook_worksheet.cell(i, DEBIT_AMT_COL).value)
                if debit_ledger_party in infi_ledger_name_list:
                    debit_ledger_party = tally_ledger_name_list[ infi_ledger_name_list.index(debit_ledger_party) ]                        
                else:
                    pass
                    # print("NOT found:", debit_ledger_party)
            next_row_inv_no = daybook_worksheet.cell(i+1, INV_COL).value
            if next_row_inv_no!=inv_no:
                date = format_date(date)
                if bank_date:
                    bank_date = format_date_type2(bank_date)
                    
                # TEMP FOR PAYMENT VOUCHER EXCLUSION<DELETE THE IF-Else CLAUSES> 
                # if isReceipt:    
                #     if debit_ledger_party=='Cash':
                #         insert_receipt_payment_Row(final_row_no, isReceipt)
                #         final_row_no+=1
                #     else:
                #         pass
                insert_receipt_payment_Row(final_row_no, isReceipt)
                final_row_no+=1
                credit_ledger_party=""
                debit_ledger_party=""
                credit_amt=0
                debit_amt=0
                bank_date = None
            i+=1    
        except IndexError:
            break
    step_1_workbook.save("./intermediate_files/step1_book_receipt_and_payment.xls")  

    # print("Converting to xml data.")
    xml_workbook = xlwt.Workbook()
    xml_sheet1 = xml_workbook.add_sheet('Sheet_1')

    xmlinput_book = xlrd.open_workbook('./intermediate_files/step1_book_receipt_and_payment.xls')
    xmlinput_sheet = xmlinput_book.sheet_by_index(0)


    row = 0
    while True:
        data=""
        try:
            val = xmlinput_sheet.cell(row,14).value
        except IndexError:
            break
        if(val=="Receipt"):
            filler_row = FILLERDATA_RECEIPT
        elif(val=="Payment"):
            filler_row = FILLERDATA_PAYMENT  
        else:
            print('val type not receipt/voucher, is ', val)      
        for i in range(0,14):
            data+=fillerdata_worksheet.cell(filler_row,i).value
            try:
                data+=xmlinput_sheet.cell(row,i).value
            except TypeError:
                data+=str(xmlinput_sheet.cell(row,i).value)
        data+=fillerdata_worksheet.cell(filler_row,14).value
        data = remove_escape_char(data)
        data = remove_ampersand_and_next_line(data)
        sheet_row = xml_sheet1.row(row)
        sheet_row.write(0,data)
        xml_file.write(data+'\n') 
        row+=1
    xml_workbook.save('./intermediate_files/step_2_receipt_and_payment.xls')
    print("receipt_and_payment process task completed. ",row,"written.")

def journal_pass():
    final_row_no=0
    step_1_workbook = xlwt.Workbook()
    step_1_sheet = step_1_workbook.add_sheet('Sheet_1')

    def insert_journal_Row(row_no, credit_ledger_party, debit_ledger_party ):
        credit_ledger_party = remove_escape_char(credit_ledger_party)
        debit_ledger_party = remove_escape_char(debit_ledger_party)

        # if debit_ledger_party == "SUSPENSE A/C":
        #     main_ledger = credit_ledger_party
        #     main_amt = credit_amt
        #     sub_ledger = debit_ledger_party
        #     sub_amt = debit_amt
        # elif credit_ledger_party == "SUSPENSE A/C":
        #     main_ledger = debit_ledger_party
        #     main_amt = debit_amt
        #     sub_ledger = credit_ledger_party
        #     sub_amt = credit_amt
        # else:
        #     print("No suspense a/c in journal entry, line ", row_no)   
        # if debit_ledger_party != "SUSPENSE A/C" or credit_ledger_party != "SUSPENSE A/C":
        #     print("No suspense a/c in journal entry, line ", row_no) 
        #     # print( "No suspense account in ",inv_no )
        #     pass
        main_ledger = debit_ledger_party
        main_amt = debit_amt
        sub_ledger = credit_ledger_party
        sub_amt = credit_amt
        
        row = step_1_sheet.row(row_no)
        row.write(0,date)
        row.write(1,narration)
        row.write(2,inv_no)
        row.write(3,main_ledger)
        row.write(4,main_ledger)
        row.write(5,main_amt)
        row.write(6,main_amt)
        row.write(7,sub_ledger)
        row.write(8,sub_amt)
        row.write(9,sub_amt)
        return     
    i=DAYBOOK_START_ROW
    while True:
        try:
            inv_no = daybook_worksheet.cell(i, INV_COL).value
            voucher_type = daybook_worksheet.cell(i, VOUCH_TYPE_COL).value       
            date = daybook_worksheet.cell(i, DATE_COL).value
            if not voucher_type=="Journal Entry":
                i+=1
                continue 
            if(daybook_worksheet.cell(i, CREDIT_LED_COL).value):
                credit_ledger_party = daybook_worksheet.cell(i, CREDIT_LED_COL).value
                credit_amt = daybook_worksheet.cell(i, CREDIT_AMT_COL).value
                narration = daybook_worksheet.cell(i, NARRATION_COL).value
                if credit_ledger_party in infi_ledger_name_list:
                    credit_ledger_party = tally_ledger_name_list[ infi_ledger_name_list.index(credit_ledger_party) ]   
                else:
                    # print("NOT found:", credit_ledger_party)    
                    pass                     
            elif((daybook_worksheet.cell(i, DEBIT_LED_COL).value)):
                debit_ledger_party = daybook_worksheet.cell(i, DEBIT_LED_COL).value
                debit_amt = -1*float(daybook_worksheet.cell(i, DEBIT_AMT_COL).value)
                if debit_ledger_party in infi_ledger_name_list:
                    debit_ledger_party = tally_ledger_name_list[ infi_ledger_name_list.index(debit_ledger_party) ]                        
                else:
                    # print("NOT found:", debit_ledger_party)
                    pass
            next_row_inv_no = daybook_worksheet.cell(i+1, INV_COL).value
            if next_row_inv_no!=inv_no:
                date=format_date(date)
                insert_journal_Row(final_row_no, credit_ledger_party, debit_ledger_party)
                final_row_no+=1
                credit_ledger_party=""
                debit_ledger_party=""
                credit_amt=0
                debit_amt=0
            i+=1    
        except IndexError:
            break
    step_1_workbook.save("./intermediate_files/step1_book_journal.xls")  

    # print("Converting to xml data.")
    xml_workbook = xlwt.Workbook()
    xml_sheet1 = xml_workbook.add_sheet('Sheet_1')

    xmlinput_book = xlrd.open_workbook('./intermediate_files/step1_book_journal.xls')
    xmlinput_sheet = xmlinput_book.sheet_by_index(0)

    row = 0
    while True:
        data=""
        try:
            val = xmlinput_sheet.cell(row,0).value
        except IndexError:
            break
        filler_row = FILLERDATA_JOURNAL
        for i in range(0,10):
            data+=fillerdata_worksheet.cell(filler_row,i).value
            try:
                data+=xmlinput_sheet.cell(row,i).value
            except TypeError:
                data+=str(xmlinput_sheet.cell(row,i).value)
        data+=fillerdata_worksheet.cell(filler_row,10).value
        data = remove_escape_char(data)
        data = remove_ampersand_and_next_line(data)
        sheet_row = xml_sheet1.row(row)
        sheet_row.write(0,data)
        xml_file.write(data+'\n') 
        row+=1
    xml_workbook.save('./intermediate_files/step_2_journal.xls')
    print("journal process task completed. ",row,"written.")

def sales_return_pass():
    debit_ledger_name = []
    debit_ledger_amt = []
    final_row_no=0
    step_1_workbook = xlwt.Workbook()
    step_1_sheet = step_1_workbook.add_sheet('Sheet_1')

    def insert_sales_return_Row(row_no):
        primary_party = ordered_final_list_name.pop(0)
        primary_amt = ordered_final_list_amt.pop(0)
        row = step_1_sheet.row(row_no)
        row.write(0,date)
        row.write(1,narration)
        row.write(2,inv_no)
        row.write(3,primary_party)
        row.write(4,primary_party)
        row.write(5,primary_amt)
        row.write(6,primary_amt)

        ledger_obj_data = ""
        for ledger_name, ledger_amt in zip(ordered_final_list_name, ordered_final_list_amt):
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN_LEDGER,0).value
            ledger_obj_data += ledger_name
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN_LEDGER,1).value
            if(float(ledger_amt)>0):
                ledger_obj_data += "No" 
            else:
                ledger_obj_data += "Yes" 
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN_LEDGER,2).value
            ledger_obj_data += str(ledger_amt)
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN_LEDGER,3).value
            ledger_obj_data += str(ledger_amt)
            ledger_obj_data += fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN_LEDGER,4).value
        row.write(7,ledger_obj_data)
        return     
    i=DAYBOOK_START_ROW
    while True:
        try:
            inv_no = daybook_worksheet.cell(i, INV_COL).value
            voucher_type = daybook_worksheet.cell(i, VOUCH_TYPE_COL).value           
            date = daybook_worksheet.cell(i, DATE_COL).value
            if not voucher_type=="Sales Return":
                i+=1
                continue    
            if(daybook_worksheet.cell(i, CREDIT_LED_COL).value):
                credit_ledger_party = daybook_worksheet.cell(i, CREDIT_LED_COL).value
                credit_amt = daybook_worksheet.cell(i, CREDIT_AMT_COL).value
                narration = daybook_worksheet.cell(i, NARRATION_COL).value
            else:
                debit_ledger = daybook_worksheet.cell(i, DEBIT_LED_COL).value
                debit_amt = -1*float(daybook_worksheet.cell(i, DEBIT_AMT_COL).value)
                debit_ledger_amt.append(debit_amt)
                if debit_ledger in infi_ledger_name_list:
                    debit_ledger_name.append(tally_ledger_name_list[ infi_ledger_name_list.index(debit_ledger) ])                          
                else:
                    print("NOT found:", debit_ledger)
                    debit_ledger_amt.pop()  
            next_row_inv_no = daybook_worksheet.cell(i+1, INV_COL).value
            if next_row_inv_no!=inv_no:
                debit_ledger_name, debit_ledger_amt = sort_fixed_ledger_names(debit_ledger_name, debit_ledger_amt)
                #Bug FIX
                ordered_final_list_name = debit_ledger_name
                ordered_final_list_amt = debit_ledger_amt
                ordered_final_list_name.append(credit_ledger_party)
                ordered_final_list_amt.append(credit_amt)

                date = format_date(date)
                insert_sales_return_Row(final_row_no)
                final_row_no+=1
                credit_ledger_party=""
                credit_amt=""
                debit_ledger_name = []
                debit_ledger_amt = []
            i+=1    
        except IndexError:
            break
    step_1_workbook.save("./intermediate_files/step1_book_sales_return.xls")  

    # print("Converting to xml data.")
    xml_workbook = xlwt.Workbook()
    xml_sheet1 = xml_workbook.add_sheet('Sheet_1')

    xmlinput_book = xlrd.open_workbook('./intermediate_files/step1_book_sales_return.xls')
    xmlinput_sheet = xmlinput_book.sheet_by_index(0)

    row = 0
    while True:
        data=""
        try:
            val = xmlinput_sheet.cell(row,0).value
        except IndexError:
            break
        for i in range(0,8):
            data+=fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN,i).value
            try:
                data+=xmlinput_sheet.cell(row,i).value
            except TypeError:
                data+=str(xmlinput_sheet.cell(row,i).value)
        data+=fillerdata_worksheet.cell(FILLERDATA_SALES_RETURN,8).value
        data = remove_escape_char(data)
        data = remove_ampersand_and_next_line(data)
        sheet_row = xml_sheet1.row(row)
        sheet_row.write(0,data)
        xml_file.write(data+'\n') 
        row+=1
    xml_workbook.save('./intermediate_files/step_2_sales_return.xls')
    print("Sales Return process task completed. ",row,"written.")

def contra_pass():
    # TODO: WIP
    final_row_no=0
    step_1_workbook = xlwt.Workbook()
    step_1_sheet = step_1_workbook.add_sheet('Sheet_1')

    def insert_journal_Row(row_no, credit_ledger_party, debit_ledger_party ):
        credit_ledger_party = remove_escape_char(credit_ledger_party)
        debit_ledger_party = remove_escape_char(debit_ledger_party)
        main_ledger = debit_ledger_party
        main_amt = debit_amt
        sub_ledger = credit_ledger_party
        sub_amt = credit_amt
        
        row = step_1_sheet.row(row_no)
        row.write(0,date)
        row.write(1,narration)
        row.write(2,inv_no)
        row.write(3,main_ledger)
        row.write(4,main_ledger)
        row.write(5,main_amt)
        row.write(6,main_amt)
        row.write(7,sub_ledger)
        row.write(8,sub_amt)
        row.write(9,sub_amt)
        return     
    i=DAYBOOK_START_ROW
    while True:
        try:
            inv_no = daybook_worksheet.cell(i, INV_COL).value
            voucher_type = daybook_worksheet.cell(i, VOUCH_TYPE_COL).value       
            date = daybook_worksheet.cell(i, DATE_COL).value
            if not voucher_type=="Journal Entry":
                i+=1
                continue 
            if(daybook_worksheet.cell(i, CREDIT_LED_COL).value):
                credit_ledger_party = daybook_worksheet.cell(i, CREDIT_LED_COL).value
                credit_amt = daybook_worksheet.cell(i, CREDIT_AMT_COL).value
                narration = daybook_worksheet.cell(i, NARRATION_COL).value
                if credit_ledger_party in infi_ledger_name_list:
                    credit_ledger_party = tally_ledger_name_list[ infi_ledger_name_list.index(credit_ledger_party) ]   
                else:
                    # print("NOT found:", credit_ledger_party)    
                    pass                     
            elif((daybook_worksheet.cell(i, DEBIT_LED_COL).value)):
                debit_ledger_party = daybook_worksheet.cell(i, DEBIT_LED_COL).value
                debit_amt = -1*float(daybook_worksheet.cell(i, DEBIT_AMT_COL).value)
                if debit_ledger_party in infi_ledger_name_list:
                    debit_ledger_party = tally_ledger_name_list[ infi_ledger_name_list.index(debit_ledger_party) ]                        
                else:
                    # print("NOT found:", debit_ledger_party)
                    pass
            next_row_inv_no = daybook_worksheet.cell(i+1, INV_COL).value
            if next_row_inv_no!=inv_no:
                date=format_date(date)
                insert_journal_Row(final_row_no, credit_ledger_party, debit_ledger_party)
                final_row_no+=1
                credit_ledger_party=""
                debit_ledger_party=""
                credit_amt=0
                debit_amt=0
            i+=1    
        except IndexError:
            break
    step_1_workbook.save("./intermediate_files/step1_book_journal.xls")  

    # print("Converting to xml data.")
    xml_workbook = xlwt.Workbook()
    xml_sheet1 = xml_workbook.add_sheet('Sheet_1')

    xmlinput_book = xlrd.open_workbook('./intermediate_files/step1_book_journal.xls')
    xmlinput_sheet = xmlinput_book.sheet_by_index(0)

    row = 0
    while True:
        data=""
        try:
            val = xmlinput_sheet.cell(row,0).value
        except IndexError:
            break
        filler_row = FILLERDATA_JOURNAL
        for i in range(0,10):
            data+=fillerdata_worksheet.cell(filler_row,i).value
            try:
                data+=xmlinput_sheet.cell(row,i).value
            except TypeError:
                data+=str(xmlinput_sheet.cell(row,i).value)
        data+=fillerdata_worksheet.cell(filler_row,10).value
        data = remove_escape_char(data)
        data = remove_ampersand_and_next_line(data)
        sheet_row = xml_sheet1.row(row)
        sheet_row.write(0,data)
        xml_file.write(data+'\n') 
        row+=1
    xml_workbook.save('./intermediate_files/step_2_journal.xls')
    print("journal process task completed. ",row,"written.")


load_ledger_map()
insert_tally_header()
sale_pass()
purchase_pass()
# payment_voucher_pass()
journal_pass()
sales_return_pass()
insert_tally_footer()
xml_file.close()
