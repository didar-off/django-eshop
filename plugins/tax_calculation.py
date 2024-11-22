from plugins.countries import countries

def tax_calculation(country, order_total):
    tax_rate = 0

    for i in countries():
        if country == i['country']:
            tax_rate += int(float(i['tax_rate'])) / 100 * float(order_total)

    return tax_rate