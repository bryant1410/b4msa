# author: Eric S. Tellez <eric.tellez@infotec.mx>
# under the same terms than the multilingual benchmark

import numpy as np
import logging
from multiprocessing import Pool

import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s :%(message)s',
                    level=logging.INFO)

OPTION_NONE = 'none'
OPTION_GROUP = 'group'
OPTION_DELETE = 'delete'


basic_options = [OPTION_DELETE, OPTION_GROUP, OPTION_NONE]
base_params = dict(
    strip_diac=[False, True],
    usr_option=basic_options,
    url_option=basic_options,
    lc=[False, True],
    token_list=[1, 2, 3, 4, 5, 6, 7],
)

_base_params = sorted(base_params.items())


class ParameterSelection:
    def __init__(self):
        pass

    def sample_param_space(self, n, q=3):
        for i in range(n):
            kwargs = {}
            for k, v in _base_params:
                if len(v) == 0:
                    continue

                if k == 'token_list':
                    x = list(v)
                    np.random.shuffle(x)
                    kwargs[k] = sorted(x[:q])
                else:
                    kwargs[k] = np.random.choice(v)

            yield kwargs

    def expand_neighbors(self, s):
        for k, v in sorted(s.items()):
            if v in (True, False):
                x = s.copy()
                x[k] = not v
                yield x
            elif v in basic_options:
                for _v in basic_options:
                    if _v != v:
                        x = s.copy()
                        x[k] = _v
                        yield x
            elif k == 'token_list':
                for _v in base_params[k]:
                    if _v not in v:
                        x = s.copy()
                        x[k] = x[k].copy()
                        x[k].append(_v)
                        yield x

    def search(self, fun_score, bsize=32, qinitial=3, hill_climbing=True, pool=None):
        tabu = set()  # memory for tabu search

        # initial approximation, montecarlo based process
        def get_best(cand):
            if pool is None:
                X = list(map(lambda x: fun_score(x[0], x[1]), cand))
            else:
                X = list(pool.map(lambda x: fun_score(x[0], x[1]), cand))

            # a list of tuples (score, conf)
            return max(zip(X, [c[0] for c in cand]), key=lambda x: x[0])

        L = []
        for conf in self.sample_param_space(bsize, q=qinitial):
            code = get_filename(conf)
            if code in tabu:
                continue

            tabu.add(code)
            L.append((conf, code))

        best = get_best(L)
        if hill_climbing:
            # second approximation, hill climbing process
            while True:
                bscore = best[0]
                L = []

                for conf in self.expand_neighbors(best[1]):
                    code = get_filename(conf)
                    if code in tabu:
                        continue

                    tabu.add(code)
                    L.append((conf, code))
                    # best = max(best, (fun_score(conf, code), conf))

                best = max(best, get_best(L), key=lambda x: x[0])
                if bscore == best[0]:
                    break

        return best


def get_filename(kwargs, basename=None):
    L = []
    if basename:
        L.append(basename)
        
    for k, v in sorted(kwargs.items()):
        L.append("{0}={1}".format(k, v).replace(" ", ""))

    return "-".join(L)