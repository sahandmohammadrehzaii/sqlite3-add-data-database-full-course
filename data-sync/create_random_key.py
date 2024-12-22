import random

def generate_activation_codes(count, length=16):
    codes = []
    for _ in range(count):
        code = ''.join(random.choices('0123456789', k=length))
        codes.append(code)
    return codes

# تولید 200 کد شانزده رقمی
activation_codes = generate_activation_codes(2000)

# ذخیره کدها در یک فایل یا نمایش در کنسول
with open("activation_codes.txt", "w") as file:
    for code in activation_codes:
        file.write(code + "',\n'")

print("200 کد شانزده رقمی ایجاد شد و در فایل 'activation_codes.txt' ذخیره گردید.")