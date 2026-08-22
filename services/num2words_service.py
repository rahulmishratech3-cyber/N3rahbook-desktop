"""
Number to Words Converter (Indian Currency Format)
Converts numeric totals to words like "Eighty Thousand Four Hundred Eight Rupees Only"
"""

def number_to_words_indian(num):
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "Zero Rupees Only"

    if num == 0:
        return "Zero Rupees Only"

    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
             "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
             "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    rupees = int(num)
    paise = round((num - rupees) * 100)

    def convert_below_thousand(n):
        words = ""
        if n >= 100:
            words += units[n // 100] + " Hundred "
            n %= 100
        if n >= 20:
            words += tens[n // 10] + " "
            n %= 10
        if n > 0:
            words += units[n] + " "
        return words

    def convert_rupees(n):
        if n == 0:
            return ""
        
        parts = []
        crores = n // 10000000
        n %= 10000000
        
        lakhs = n // 100000
        n %= 100000
        
        thousands = n // 1000
        n %= 1000
        
        if crores > 0:
            parts.append(convert_below_thousand(crores).strip() + " Crore")
        if lakhs > 0:
            parts.append(convert_below_thousand(lakhs).strip() + " Lakh")
        if thousands > 0:
            parts.append(convert_below_thousand(thousands).strip() + " Thousand")
        if n > 0:
            parts.append(convert_below_thousand(n).strip())
            
        return " ".join(parts)

    rupee_str = convert_rupees(rupees).strip()
    if not rupee_str:
        rupee_str = "Zero"

    res = f"{rupee_str} Rupees"
    if paise > 0:
        paise_str = convert_below_thousand(paise).strip()
        res += f" and {paise_str} Paise"
        
    res += " Only"
    return res
