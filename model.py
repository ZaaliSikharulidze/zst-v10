import numpy as np

class ZSTModel:

    def predict(self, features):

        rsi, mom, vol = features

        score = 0

        if rsi < 30:
            score += 1
        if mom > 0:
            score += 1

        return score / 2