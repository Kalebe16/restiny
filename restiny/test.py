import random


def test(aaa={}):
    aaa[random.randint(1, 10)] = random.randint(1, 10)
    print(aaa)


test()
test()
test()
test()
test()
