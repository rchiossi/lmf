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


def print_cards(deck):
    cards = sorted(deck.keys())

    print('# Cartas -------')
    for l, card in zip(range(len(cards)), cards):
        print('{:3}: {}x {}'.format(l, deck[card], card))


def print_price_table(table, select):
    cards = sorted(set([c for (c, s) in table.keys()]))
    stores = sorted(set([s for (c, s) in table.keys()]))

    fmt = '| {:^15.15} |' + ' {:>6}' * len(cards) + ' |'
    header = fmt.format('Loja / Carta', *range(len(cards)))

    print('\n' + '-' * len(header))
    print(header)
    print('-' * len(header))

    for store in stores:
        values = []

        if store in select.values():
            fmt = '| \033[91m{:15.15}\033[0m |'.format(store)
        else:
            fmt = '| {:15.15} |'.format(store)

        for card in cards:
            v = '.'
            if (card, store) in table.keys():
                v = table[card, store]

            if select is not None and card in select.keys() and select[card] == store:
                fmt += ' \033[92m{:>6}\033[0m'
            else:
                fmt += ' {:>6}'

            values.append(v)

        print(fmt.format(*values) + ' |')

    print('-' * len(header))


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

        if FILTER_BASICS and card in basics:
            continue

        if card in cards:
            cards[card] += amount
        else:
            cards[card] = amount

    return cards


def get_price_list(card):
    price_list = []

    url = "http://www.ligamagic.com.br/?view=cards/card&%s" % urllib.parse.urlencode({'card': card})

#    with open("data/%s.html" % urllib.parse.urlencode({'card': card}), "r") as f:
#        data = f.read()

    with urllib.request.urlopen(url) as f:
        data = f.read().decode('utf-8')

#        with open("data/%s.html" % urllib.parse.urlencode({'card':card}), "w") as out:
#            out.write(data)

    data = html.unescape(data)

    if data is None:
        print('Not found')
        return None

    p = re.compile('onmouseover="omoEstoque(.*?)</tr>', re.S)
    m = p.findall(data)

    for block in m:
        lines = block.split('\n')[1:-1]

        store = re.search("title='(.+)'", lines[0]).group(1)
        edition = re.search('title="(.+)"', lines[1]).group(1)
        price = float(
            re.search("<b>R\$ (.+)</b>", lines[2]).group(1).replace(',', '.'))
        amount = int(re.search(">(.+) unid", lines[3].replace(',','')).group(1))

        price_list.append((store, edition, amount, price))

    return price_list


def minimize(table, stores):
    cards = sorted(set([c for (c, s) in table.keys()]))
    select = {}

    if stores is None:
        stores = sorted(set([s for (c, s) in table.keys()]))

    for card in cards:
        v = -1
        for store in stores:
            if (card, store) not in table.keys():
                continue

            if v == -1 or table[card,store] < v:
                v = table[card,store]
                select[card] = store

    return select


def optimize(table, deck, limit):
    stores = sorted(set([s for (c, s) in table.keys()]))
    cards = sorted(set([c for (c, s) in table.keys()]))
    comb = list(itertools.combinations(stores, limit))
    total = -1
    select = None

    for c in comb:
        s = minimize(table, c)

        t = 0
        for card in cards:
            for store in stores:
                t += table[card, store] * deck[card] if card in s.keys() and s[card] == store else 99999999

        if total != -1 and t > total:
            continue

        total = t
        select = s

    return select


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    deck = load_deck(sys.argv[1])

    if deck is None or len(deck) == 0:
        print("Error loading deck: %s" % sys.argv[1])
        sys.exit(0)

    table = {}
    for card, amount in deck.items():
        print("\nLoading price for: %s" % card)
        price_list = get_price_list(card)

        print_price_list(price_list)

        if price_list is None:
            print("Card not found: %s" % card)
            continue

        for item in price_list:
            if item[2] < amount:
                continue

            table[card,item[0]] = item[3]

    select = minimize(table, None)

    print()
    print_cards(deck)
    print_price_table(table, select)

    total = sum([table[card, store] * deck[card] for card, store in select.items()])
    print("\n# Total = R$ {0:.2f}".format(total))

    for i in range(5, 0, -1):
        print("\n# Optimized {} ----------".format(i))

        select = optimize(table, deck, i)
        print_price_table(table, select)

        total = sum([table[card, store] * deck[card] for card, store in select.items()])
        print("\n# Total = R$ {0:.2f}".format(total))

if __name__ == "__main__":
    main()
