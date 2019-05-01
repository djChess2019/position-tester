from math import sqrt, log10, pi, log, inf, nan
import sys, re

class Elo:
    def __init__(self, wins, losses, draws):
        self.wins = wins
        self.losses = losses
        self.draws = draws

        n = wins + losses + draws
        w = wins / n
        l = losses / n
        d = draws / n
        self.mu = w + d / 2.0

        devW = w * pow(1.0 - self.mu, 2.0)
        devL = l * pow(0.0 - self.mu, 2.0)
        devD = d * pow(0.5 - self.mu, 2.0)
        self.stdev = sqrt(devW + devL + devD) / sqrt(n)

    def diff(self):
        return self.diff1(self.mu)

    def diff1(self, p):
        if p==0:
            return -inf
        if p==1:
            return inf
        return -400.0 * log10(1.0 / p - 1.0)

    def errorMargin(self):
        try:
            muMin = self.mu + self.phiInv(0.025) * self.stdev
            muMax = self.mu + self.phiInv(0.975) * self.stdev
            return (self.diff1(muMax) - self.diff1(muMin)) / 2.0
        except:
            return nan

    def phiInv(self, p):
        return sqrt(2.0) * self.erfInv(2.0 * p - 1.0)

    def erfInv(self, x):
        a = 8.0 * (pi - 3.0) / (3.0 * pi * (4.0 - pi))
        y = log(1.0 - x * x)
        z = 2.0 / (pi * a) + y / 2.0

        ret = sqrt(sqrt(z * z - y / a) - z)

        if x < 0.0:
            return -ret
        return ret

def print_elo(w, l, d):
    e = Elo(w, l, d)
    print("+%s -%s =%s Elo %.2f +/- %.2f" % (w, l, d, e.diff(), e.errorMargin()))

if __name__=="__main__":
    print_elo(192, 584, 224)
    print_elo(0, 999, 1)
    print_elo(4, 972, 24)
    print_elo(0, 2, 0)
    print_elo(2, 0, 0)
    print_elo(420, 223, 357)

    ws, ls, ds = 0, 0, 0
    previous_net_id = 0
    for line in open("t"):
        m = re.match(r"Score of .*-(\d+) .*: (\d+) - (\d+) - (\d+)", line)
        if m:
            net_id, w, l, d = map(int, m.groups())
            if net_id!=previous_net_id:
                if ws+ls+ds:
                    print(ws+ls+ds, previous_net_id, end=": "); print_elo(ws, ls, ds)
                ws, ls, ds = 0, 0, 0
            ws += w
            ls += l
            ds += d
            previous_net_id = net_id
            #print(net_id, w, l, d, ws, ls, ds)
    print(ws+ls+ds, previous_net_id, end=": "); print_elo(ws, ls, ds)
