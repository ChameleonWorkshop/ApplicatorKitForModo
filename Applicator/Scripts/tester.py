import random
data = []
for i in range(0, 50):
    data.append(random.uniform(0.0, 1.0))

params = {}
params['a'] = 'a'
params['b'] = 'b'
print(params)


s = 'sdasda.csv'
path = s[-4:]
print(path)

min = 0
max = len(data)
for i in range(min, max):
    range_count = 0
    range_sum = 0.0
    for y in range(i-3, i+4):
        if y >=0 and y < max:
            range_count += 1
            range_sum += data[y]

    strength = range_sum / range_count
    #print(f'{str(i)} - {str(range_count)} - {str(range_sum)} - {str(data[i])} - {str(strength)}')


