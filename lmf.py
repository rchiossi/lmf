#!/usr/bin/env python3

import itertools
import re
import sys
import urllib.request

import html

FILTER_BASICS = True
basics = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']


def usage():
    print("Usage:")


def print_price_list(price_list):
    t = sorted(price_list, key=lambda val: val[3])

    print('-' * 80)
    print('| {0:^32} | {1:^22} | {2:^5} | {3:^8} |'.format("Loja", "Coleção", "Quant", "Preço"))
    print('-' * 80)
    for i in t:
        print('| {0:32.32} | {1:22.22} | {2:5} | {3:8.8} |'.format(i[0], i[1], i[2], i[3]))
    print("-" * 80)


def print_minimized(select):
    for key, item in select.items():
        print("{0:10.10} : {1}".format(key, " ".join("{0:1}".format('\033[92mX\033[0m' if v else '-') for v in item)))


def load_deck(filename):
    with open(filename) as f:
        data = f.read()

    if data is None:
        return None
        print("Unable to find deck: %s", filename)
        sys.exit(0)

    cards = {}
    for line in data.split('\n'):
        m = re.match('^([0-9]+) (.+)', line.strip())

        if m is None:
            continue

        amount = int(m.group(1))
        card = m.group(2)

        if card in cards:
            cards[card] += amount
        else:
            cards[card] = amount

    return cards


def get_price_list(card):
    price_list = []

    url = "http://www.ligamagic.com.br/?view=cards/card&%s" % urllib.parse.urlencode({'card': card})
    print(url)

    with open("%s.html" % urllib.parse.urlencode({'card': card}), "r") as f:
        data = f.read()

#    with urllib.request.urlopen(url) as f:
#        data = f.read().decode('utf-8')

#        with open("%s.html" % urllib.parse.urlencode({'card':card}), "w") as out:
#            out.write(data)

    data = html.unescape(data)

    if data is None:
        print('Not found')
        return None

    p = re.compile('onmouseover="omoEstoque(.*?)</tr>', re.S)
    m = p.findall(data)

    for block in m:
        lines = block.split('\n')[1:-1]

        title = re.search("title='(.+)'", lines[0]).group(1)
        edition = re.search('title="(.+)"', lines[1]).group(1)
        price = float(
            re.search("<b>R\$ (.+)</b>", lines[2]).group(1).replace(',', '.'))
        quantity = int(re.search(">(.+) unid", lines[3]).group(1))

        price_list.append((title, edition, quantity, price))

    return price_list


def card_table(price_list, amount):
    ct = {}
    for item in price_list:
        if item[2] < amount:
            continue
        if item[0] not in ct.keys() or item[3] < ct[item[0]]:
            ct[item[0]] = item[3] * item[2]

    return ct if len(ct) > 0 else None


def minimize(group):
    select = {key: [False] * len(group[key]) for key in group.keys()}
    total = [-1] * len(next(iter(group.values())))

    for k, g in group.items():
        for n, v in enumerate(g):
            if total[n] != -1 and v >= total[n]:
                continue

            total[n] = v
            for sk, si in select.items():
                si[n] = sk == k

    return sum(total), select


def optimize(stores, limit):
    comb = list(map(dict, itertools.combinations(stores.items(), limit)))
    total = -1
    select = None

    for c in comb:
        t, s = minimize(c)

        if total != -1 and t > total:
            continue

        total = t
        select = s

    return total, select


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    deck = load_deck(sys.argv[1])

    if deck is None or len(deck) == 0:
        print("Error loading deck: %s" % sys.argv[1])
        sys.exit(0)

    cards = {}
    for card, amount in deck.items():
        if FILTER_BASICS and card in basics:
            continue

        print("Getting price list for: %s" % card)
        price_list = get_price_list(card)

        if price_list is None:
            print("Card not found: %s" % card)
            continue

        ct = card_table(price_list, amount)

        cards[card] = ct

    card_index = cards.keys()

    stores = {}
    for n, card in enumerate(card_index):
        table = cards[card]
        for store, price in table.items():
            if store not in stores:
                stores[store] = [99999] * len(card_index)

            stores[store][n] = price

    print("# Minimized ----------")

    total, select = minimize(stores)

    print("total = {0:.2f}".format(total))
    print_minimized(select)

    for i in range(5, 0, -1):
        print("\n# Optimized {} ----------".format(i))

        total, select = optimize(stores, i)

        print("total = {0:.2f}".format(total))
        print_minimized(select)

if __name__ == "__main__":
    main()
