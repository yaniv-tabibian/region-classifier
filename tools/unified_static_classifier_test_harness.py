"""
Unified STATIC region classifier for the 1-D formulation, covering BOTH cases:

    Case 1 - adjacent   : gap g = 0   (Right-A == Left-B, shared border)
    Case 2 - separated  : gap g > 0   (a strip of Outside of width g between them)

Geometry (left -> right):  Left-A=0, Right-A=W_A, Left-B=W_A+g, Right-B=W_A+g+W_B
    A = shortest distance to nearest of {Left-A, Right-A}   (blue line)
    B = shortest distance to nearest of {Left-B, Right-B}   (green line)

Classifier inputs: (A, B, W_A, W_B, g) only -- never the position.
Key quantity: the SIGNED difference D = B - A.

    D >= W_A + g            -> Outside (left of A)
    g <= D <  W_A + g       -> In A
    -g <  D <  g            -> Outside (the gap; only reachable when g>0)
    -(W_B+g) < D <= -g      -> In B
    D <= -(W_B + g)         -> Outside (right of B)

When g == 0 the "gap" interval collapses and D == 0 becomes the shared-edge
straddle of Case 1: resolved by the half-width tie-break, else the provably
undecidable band |dist to shared| <= min(W_A/2,W_B/2).
"""
import random

random.seed(11)
TOL = 1e-9


# ---------------------------------------------------------------- geometry
def geometry(x, wA, wB, g):
    LA, RA, LB, RB = 0.0, wA, wA + g, wA + g + wB
    A = min(abs(x - LA), abs(x - RA))
    B = min(abs(x - LB), abs(x - RB))
    if x < -TOL or x > RB + TOL:
        label = "Outside"
    elif abs(x) <= TOL or abs(x - RB) <= TOL:
        label = "Outside"            # outer edge
    elif x < RA - TOL:
        label = "In A"
    elif x > LB + TOL:
        label = "In B"
    elif g > TOL and RA + TOL < x < LB - TOL:
        label = "Outside"            # the gap interior
    else:
        label = "Boundary"           # exactly on an inner edge / shared line
    return A, B, label


# ---------------------------------------------------------- the classifier
def classify(A, B, wA, wB, g, tol=1e-9):
    D = B - A
    if D >= wA + g - tol:
        return "Outside"                          # left of A
    if D <= -(wB + g) + tol:
        return "Outside"                          # right of B
    if D > g + tol:
        return "In A"                             # A left half
    if D < -g - tol:
        return "In B"                             # B right half
    # here |D| ~ within [-g, g]
    if g > tol:                                   # Case 2: gap present
        if D >= g - tol:
            return "In A"                         # A inner-edge plateau (D=+g)
        if D <= -g + tol:
            return "In B"                         # B inner-edge plateau (D=-g)
        return "Outside"                          # strictly inside the gap
    # Case 1 (g==0): D ~ 0 is the shared-edge straddle
    t = A                                         # == B
    if t > wB / 2 + tol:
        return "In A"
    if t > wA / 2 + tol:
        return "In B"
    return "Ambiguous"


def resolve_band_with_state(A, B, wA, wB, g, prev_state):
    """The 1-bit RUN-TIME fix. For Case 2 (g>0) classify() is already exact, so
    prev_state is never consulted. For Case 1 (g==0) a snapshot inside the band
    t <= min(wA/2, wB/2) is provably undecidable; the missing bit (which side of
    the shared line) is carried by continuity -> keep the last decided side. The
    online classifier flips it on a shared-line crossing (A,B both dip to ~0).
    Result: the run-time output is ALWAYS In A / In B / Outside -- never Ambiguous.
    """
    verdict = classify(A, B, wA, wB, g)
    return verdict if verdict != "Ambiguous" else prev_state


# ------------------------------------------------------------- evaluation
def decidable(A, B, label, wA, wB, g):
    if g <= TOL and label in ("In A", "In B") \
            and abs(A - B) <= TOL and A <= min(wA / 2, wB / 2) + TOL:
        return False          # Case-1 undecidable band
    return True


def run(g_mode, n_worlds=400, n_x=1400):
    wrong, ambiguous_ok, abstain_bad, total = [], 0, 0, 0
    for _ in range(n_worlds):
        wA = round(random.uniform(0.5, 10.0), 3)
        wB = round(random.uniform(0.5, 10.0), 3)
        g = 0.0 if g_mode == "case1" else round(random.uniform(0.5, 10.0), 3)
        span = wA + wB + g
        for i in range(n_x):
            x = -span - 3 + (2 * span + 6) * (i + 0.37) / n_x   # offset off edges
            A, B, label = geometry(x, wA, wB, g)
            if label == "Boundary":
                continue
            total += 1
            pred = classify(A, B, wA, wB, g)
            dec = decidable(A, B, label, wA, wB, g)
            if pred == "Ambiguous":
                if dec:
                    abstain_bad += 1
                else:
                    ambiguous_ok += 1
                continue
            if pred != label and dec and len(wrong) < 6:
                wrong.append((round(x, 3), A, B, wA, wB, g, label, pred))
            elif pred != label and dec:
                wrong.append(True)
    return total, len([w for w in wrong if w is not True]) + \
        sum(1 for w in wrong if w is True), \
        [w for w in wrong if w is not True], ambiguous_ok, abstain_bad


if __name__ == "__main__":
    print("=" * 74)
    print("TEST A - Case 2 (separated, gap g>0):  unified classifier vs truth")
    tot, nwrong, ex, amb_ok, amb_bad = run("case2")
    print(f"  samples                 : {tot}")
    print(f"  CONFIDENT-WRONG (bugs)  : {nwrong}")
    print(f"  abstained (Ambiguous)   : {amb_ok + amb_bad}   (expected 0 for Case 2)")
    for e in ex:
        print("   ", e)
    print()
    print("=" * 74)
    print("TEST B - Case 1 (adjacent, g==0):  same classifier vs truth")
    tot, nwrong, ex, amb_ok, amb_bad = run("case1")
    print(f"  samples                 : {tot}")
    print(f"  CONFIDENT-WRONG (bugs)  : {nwrong}")
    print(f"  correctly abstained     : {amb_ok}   (the undecidable band)")
    print(f"  wrongly abstained       : {amb_bad}")
    print()
    print("=" * 74)
    print("TEST C - Case 2 is single-snapshot EXACT (no identical (A,B) with")
    print("         different label when g>0):")
    wA, wB, g = 4.0, 3.0, 3.0
    # a point in A's inner half and one in the gap can never share (A,B):
    ain = geometry(3.5, wA, wB, g)     # In A, right half
    gap = geometry(5.5, wA, wB, g)     # gap midpoint (Outside)
    print(f"  In A  x=3.5 -> (A,B)={ain[:2]}  D={ain[1]-ain[0]:+.2f}  truth={ain[2]}  pred={classify(*ain[:2],wA,wB,g)}")
    print(f"  gap   x=5.5 -> (A,B)={gap[:2]}  D={gap[1]-gap[0]:+.2f}  truth={gap[2]}  pred={classify(*gap[:2],wA,wB,g)}")
    print("  => distinct D, distinct label: the gap removes the Case-1 ambiguity.")
    print()
    print("=" * 74)
    print("TEST D - what the carried bit does and does NOT buy you")
    print("  D1 walks a trajectory carrying the PREVIOUS OUTPUT (never the truth), so")
    print("  the test can actually fail -- and it does: with g=0, D == 0 across the")
    print("  whole right half of A AND the whole left half of B, so a shared-edge")
    print("  crossing changes nothing in D and the carried bit never flips.")
    print("  D2 adds the crossing detector (both distances dip to ~0 together), which")
    print("  is the missing event. That is what classifier.py implements.")
    print()
    class Dip:
        """One region's 'distance dipped to ~0 and rebounded' detector -- the same
        mechanism as _RegionState in src/region_classifier/classifier.py: an
        adaptive threshold tracking a decayed estimate of |delta d| (~ speed*dt),
        and a crossing reported on the REBOUND out of a local minimum."""

        def __init__(self, k=1.4, decay=0.85, floor=1e-9):
            self.k, self.decay, self.floor = k, decay, floor
            self.prev = self.eps = None
            self.falling = False
            self.local_min = float("inf")

        def update(self, d):
            crossed = False
            if self.prev is not None:
                self.eps = max(abs(d - self.prev), (self.eps or 0.0) * self.decay)
                thr = self.k * max(self.eps, self.floor)
                if d < self.prev:
                    self.falling, self.local_min = True, min(self.local_min, d)
                elif d > self.prev and self.falling:
                    if self.local_min < thr:
                        crossed = True
                    self.falling, self.local_min = False, float("inf")
            self.prev = d
            return crossed

    for wA, wB in ((4.0, 4.0), (7.0, 3.0), (2.0, 8.0)):
        for mode in ("carry-only", "carry+crossing"):
            prev, bad, tot = "Outside", 0, 0
            da, db = Dip(), Dip()
            n = 40000
            for i in range(n + 1):
                x = -1.0 + (wA + wB + 2.0) * i / n
                A, B, label = geometry(x, wA, wB, 0.0)
                if label == "Boundary":
                    continue
                out = resolve_band_with_state(A, B, wA, wB, 0.0, prev_state=prev)
                ca, cb = da.update(A), db.update(B)
                if mode == "carry+crossing" and ca and cb:
                    # both dipped to ~0 together => that was the shared A/B edge
                    out = {"In A": "In B", "In B": "In A"}.get(prev, out)
                tot += 1
                if out != label:
                    bad += 1
                prev = out
            verdict = "<== the carried bit alone is NOT enough" if bad > tot // 100 else "OK"
            print(f"  wA={wA:<4} wB={wB:<4} {mode:<15}: {bad:>6}/{tot} wrong "
                  f"({100 * bad / tot:5.1f}%)  {verdict}")
    print()
    print("  Conclusion: 'keep the last decided side' is the right answer to 'this")
    print("  snapshot cannot decide', but it is only half of an online classifier --")
    print("  the crossing detector supplies the flip. Case 2 (g>0) needs neither:")
    print("  classify() is single-snapshot exact there.")
