def validateAmount(amount):
    if amount.lower() == "quit":
        return "quit"
    try:
        validNumber = float(amount)

        if validNumber < 0:
            return "Negative"
        #Input manager can use string "Negative" to print negative number in input error message

        return validNumber
    
    except ValueError:
        return "Invalid"
    #Input manager can use "Invalid" to print that characters or spaces are not allowed error msg

def validateDescription(description):
    description = description.strip()

    if description.lower() == "quit":
            return "quit"

    if description == "":
        return "Empty"
    #Input manager can use string "Empty" to print empty error message

    if len(description) < 2:
         return "Short"
    #Input manager can use string "Short" to print description is too short error message