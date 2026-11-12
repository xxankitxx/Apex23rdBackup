"""11 Nov 2026 (docs/42 section 5.2, docs/44 section 4A, docs/45 section 7): the coherent competing-risk model as an
engine artefact. One model, not eight: for each interval (0-30, 30-60, 60-180, 180-300 s), GIVEN no barrier was hit
before it, a three-way softmax gives P(profit barrier first), P(adverse barrier first), P(neither) in that interval.

    S(0) = 1,  S(j) = S(j-1) * h_survive(j)
    P(up by J)   = sum over j <= J of S(j-1) * h_up(j)
    P(down by J) = sum over j <= J of S(j-1) * h_down(j)

So the horizon probabilities are consistent by construction and need no repair afterwards. Fitted offline
(research/predict/fit_hazard.py); here only the scoring, the same function for the artefact's lines and the engine."""
import numpy as np

CLIP = 4.0
KIND = "hazard"


def score(art, X):
    """(pT, pA), each (rows, horizons), cumulative. art: dict(med, sd, W) with W[j] = [[w_up...], [w_down...]],
    intercept first, on standardised and clipped features."""
    X = np.atleast_2d(np.asarray(X, float))
    med, sd = np.asarray(art["med"], float), np.asarray(art["sd"], float)
    Z = np.clip(np.nan_to_num((X - med) / sd, nan=0.0, posinf=CLIP, neginf=-CLIP), -CLIP, CLIP)
    A = np.c_[np.ones(len(Z)), Z]
    nh = len(art["W"])
    pT, pA = np.zeros((len(Z), nh)), np.zeros((len(Z), nh))
    S = np.ones(len(Z))
    cu, cd = np.zeros(len(Z)), np.zeros(len(Z))
    for j in range(nh):
        W = np.asarray(art["W"][j], float)                     # (2, p + 1): up, down; survive is the reference
        U = np.c_[np.zeros(len(Z)), A @ W.T]
        U -= U.max(1, keepdims=True)
        E = np.exp(U)
        P = E / E.sum(1, keepdims=True)                        # survive, up, down
        cu, cd = cu + S * P[:, 1], cd + S * P[:, 2]
        S = S * P[:, 0]
        pT[:, j], pA[:, j] = cu, cd
    return pT, pA
