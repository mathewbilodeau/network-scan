def decimal_to_binary(decimal_number: str):
    decimal_temp = int(decimal_number)
    binary_digits = []
    binary_number = ""

    # if binary_digits[0] == 0:
    #    raise ValueError("Decimal number cannot have leading zero")

    while decimal_temp > 0:
        binary_digits.append(decimal_temp % 2)
        decimal_temp //= 2

    binary_digits.reverse()  # reverse() method does not return list, it alters list

    for digit in binary_digits:
        binary_number += str(digit)

    return binary_number


def binary_to_decimal(binary_number: str):
    binary_temp = binary_number[::-1]  # string reversal using list slice necessary to start from rightmost digit
    decimal_number = 0
    digit_incrementer = 0

    for digit in binary_temp:
        if digit != "0" and digit != "1":
            raise ValueError("Binary number can only contain 0 or 1")
        else:
            decimal_number += int(digit) * 2 ** digit_incrementer
            digit_incrementer += 1

    return decimal_number


