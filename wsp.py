from __future__ import print_function
import random
from math import sqrt

def dist(dims, p1, p2):
    s = 0
    for i, d in enumerate(dims):
        n = (p1[i] - p2[i]) / (d[1] - d[0])
        s += n * n
    return sqrt(s)

def wsp(dims, size, dmin):
    random.seed()
    points = []
    for _ in range(size):
        points.append(tuple(random.uniform(d[0], d[1]) for d in dims))

    p0 = points[0]
    while True:
        next = []
        for p in points:
            if dist(dims, p, p0) >= dmin:
                next.append(p)
        if len(next) + 1 == len(points):
            return points
        
        minlen = float("inf")
        p1 = None
        for p in points:
            cur = dist(dims, p, p0)
            if minlen > cur:
                minlen = cur
                p1 = p
        next.append(p0)
        p0 = p1
        points = next

if __name__ == "__main__":
    a = wsp([(0, 10), (0, 100), (0, 10), (0, 100)], 200, 1)
    print(a)
    print(len(a))
