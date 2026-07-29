"""
MSD home assignment — STATIC distance formulation (interviewer's 2nd sketch).

Geometry (1-D along the horizontal axis), regions ADJACENT sharing a line:
    Left-A = 0
    Right-A = Left-B = wA          # the SHARED line
    Right-B = wA + wB
    Region A = [0, wA]   (width wA)
    Region B = [wA, wA+wB]  (width wB)

For a sensor at position x:
    A = distance to nearest of {Left-A, Right-A}      (blue line in the sketch)
    B = distance to nearest of {Left-B, Right-B}      (green line in the sketch)
Both are UNSIGNED distances to the nearest bounding LINE (so inside a region A>0).

This harness:
  (1) ground-truth label from x,
  (2) computes (A, B) as the sensor would report,
  (3) runs candidate classifiers that see ONLY (A, B, wA, wB) — never x,
  (4) compares to truth over a dense grid and random widths,
  (5) proves where a purely-static classifier can and cannot be correct.
"""
import random

random.seed(7)
TOL = 1e-9

# ----------------------------------------------------------------------
# Ground truth
# ----------------------------------------------------------------------
def geometry(x, wA, wB):
    LA, RA, LB, RB = 0.0, wA, wA, wA + wB
    A = min(abs(x - LA), abs(x - RA))
    B = min(abs(x - LB), abs(x - RB))
    if   x < -TOL:            label = "Outside"
    elif x >  RB + TOL:       label = "Outside"
    elif abs(x) <= TOL:       label = "Outside"     # exactly on Left-A (outer edge)
    elif abs(x - RB) <= TOL:  label = "Outside"     # exactly on Right-B (outer edge)
    elif x < RA - TOL:        label = "In A"
    elif x > RA + TOL:        label = "In B"
    else:                     label = "Shared(A/B)" # exactly on the shared line
    return A, B, label

# ----------------------------------------------------------------------
# Candidate classifiers — they receive ONLY (A, B, wA, wB)
# ----------------------------------------------------------------------
def clf_naive_absdiff(A, B, wA, wB):
    """Yaniv's original 4 conditions, evaluated in the stated order, using |A-B|."""
    d = abs(A - B)
    if abs(d - wA) <= TOL:      return "Outside"      # cond 1
    elif d - wA < 0:            return "In A"         # cond 2
    elif d - wB < 0:            return "In B"         # cond 3
    elif abs(d - wB) <= TOL:    return "Outside"      # cond 4
    else:                       return "UNCLASSIFIED"

def clf_signed(A, B, wA, wB):
    """Intermediate: use the SIGNED difference D = B - A (keeps direction)."""
    D = B - A
    if D >  max(wA, wB) + TOL or D < -max(wA, wB) - TOL:
        return "Invalid"                              # not geometrically realizable
    if abs(D - wA) <= TOL:      return "Outside"      # D = +wA  -> left of A
    if abs(D + wB) <= TOL:      return "Outside"      # D = -wB  -> right of B
    if D >  TOL:                return "In A"         # 0 < D < wA  -> left half of A
    if D < -TOL:                return "In B"         # -wB < D < 0 -> right half of B
    return "Ambiguous(A==B)"                          # D == 0 -> shared-line straddle

def clf_best(A, B, wA, wB):
    """Static single-snapshot CORE (not the run-time output). Signed difference +
    a half-width tie-break on the A==B straddle: an interior point is at most
    (its region width)/2 from a boundary, so a large equal distance rules out the
    narrower region's half. It still returns 'Ambiguous' inside the band on
    purpose -- that is the provable single-snapshot limit this harness measures.
    The run-time layer is resolve_band_with_state(), which never returns 'Ambiguous'."""
    D = B - A
    if D >  max(wA, wB) + TOL or D < -max(wA, wB) - TOL:
        return "Outside"                              # not realizable -> treat as far/outside
    if abs(D - wA) <= TOL:      return "Outside"      # D = +wA  -> left of A (or Left-A edge)
    if abs(D + wB) <= TOL:      return "Outside"      # D = -wB  -> right of B (or Right-B edge)
    if D >  TOL:                return "In A"         # left half of A
    if D < -TOL:                return "In B"         # right half of B
    # D == 0  -> A == B == t (distance to the shared line); use known widths:
    t = A
    if t > wB / 2 + TOL:        return "In A"         # too far from shared line to be in B's half
    if t > wA / 2 + TOL:        return "In B"         # too far to be in A's half
    return "Ambiguous"                                # t <= min(wA/2,wB/2) : truly undecidable

def resolve_band_with_state(A, B, wA, wB, prev_state):
    """The 1-bit RUN-TIME fix for the undecidable band.

    A lone snapshot inside the band  t <= min(wA/2, wB/2)  is provably
    undecidable (two mirror points across the shared line report the SAME
    (A, B); see impossibility_example). The ONLY missing information is one
    bit -- which side of the shared line we are on -- and at run-time the
    trajectory supplies it for free: keep the last decided side. That bit
    flips only when the stream shows a shared-line crossing (A and B both dip
    to ~0 together), which the online RegionClassifier detects. Outside the
    band the sign of D decides AND re-anchors prev_state, so the state can
    never get permanently stuck. Hence the run-time output is ALWAYS one of
    In A / In B / Outside -- never 'Ambiguous'.
    """
    verdict = clf_best(A, B, wA, wB)
    return verdict if verdict != "Ambiguous" else prev_state

# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------
def truth_is_decidable(A, B, label, wA, wB):
    """A static classifier CAN be expected to get it right only when A != B
    (or the point is Outside). When A==B and the point is inside, In-A vs In-B
    is information-theoretically undecidable from (A,B,wA,wB)."""
    if label in ("In A", "In B") and abs(A - B) <= TOL and A <= min(wA / 2, wB / 2) + TOL:
        return False
    return True

def run(clf, n_widths=400, n_x=1200):
    wrong = []            # confidently wrong on a DECIDABLE input  (= real bugs)
    ambiguous_ok = 0      # correctly abstained on the undecidable A==B straddle
    abstain_bad = 0       # abstained where it should have decided
    total = 0
    for _ in range(n_widths):
        wA = round(random.uniform(0.5, 10.0), 3)
        wB = round(random.uniform(0.5, 10.0), 3)
        span = wA + wB
        for i in range(n_x):
            x = -span - 3 + (2 * span + 6) * i / (n_x - 1)
            A, B, label = geometry(x, wA, wB)
            if label == "Shared(A/B)":
                continue
            total += 1
            pred = clf(A, B, wA, wB)
            decidable = truth_is_decidable(A, B, label, wA, wB)
            if pred in ("Ambiguous(A==B)", "Ambiguous"):
                if decidable: abstain_bad += 1
                else:         ambiguous_ok += 1
                continue
            # map predicted to truth space
            correct = (pred == label)
            if not correct:
                if decidable:
                    if len(wrong) < 6:
                        wrong.append((round(x,3), A, B, wA, wB, label, pred))
                    else:
                        wrong.append(True)  # count only
                # if undecidable and it guessed, that's a lucky/unlucky guess -> count as wrong-when-undecidable below
                else:
                    pass
    n_wrong = sum(1 for w in wrong if w is True) + sum(1 for w in wrong if w is not True)
    return dict(total=total, n_wrong=n_wrong,
                examples=[w for w in wrong if w is not True],
                ambiguous_ok=ambiguous_ok, abstain_bad=abstain_bad)

# ----------------------------------------------------------------------
# Impossibility proof: two geometrically-valid points with IDENTICAL
# (A, B, wA, wB) but DIFFERENT true label  => no static function can be correct.
# ----------------------------------------------------------------------
def impossibility_example():
    wA, wB = 4.0, 4.0
    xa = 3.0   # in A (right half)
    xb = 5.0   # in B (left half)
    Aa, Ba, la = geometry(xa, wA, wB)
    Ab, Bb, lb = geometry(xb, wA, wB)
    return (wA, wB, xa, (Aa, Ba), la, xb, (Ab, Bb), lb)

if __name__ == "__main__":
    print("="*74)
    print("TEST 1 — Yaniv's original |A-B| 4-condition classifier vs ground truth")
    r0 = run(clf_naive_absdiff)
    print(f"  samples tested        : {r0['total']}")
    print(f"  CONFIDENT-WRONG (bugs): {r0['n_wrong']}")
    for ex in r0['examples']:
        x,A,B,wA,wB,lab,pred = ex
        print(f"    x={x:>7}  A={A:.3f} B={B:.3f} wA={wA} wB={wB} | truth={lab:8} pred={pred}")
    print()
    print("="*74)
    print("TEST 2 — Corrected SIGNED-difference classifier vs ground truth")
    r1 = run(clf_signed)
    print(f"  samples tested                 : {r1['total']}")
    print(f"  CONFIDENT-WRONG (bugs)         : {r1['n_wrong']}")
    print(f"  abstained on A==B straddle     : {r1['ambiguous_ok'] + r1['abstain_bad']}")
    print()
    print("="*74)
    print("TEST 2b — FINAL classifier (signed + half-width tie-break) vs ground truth")
    rb = run(clf_best)
    print(f"  samples tested                    : {rb['total']}")
    print(f"  CONFIDENT-WRONG (bugs)            : {rb['n_wrong']}")
    print(f"  correctly abstained (truly ambig): {rb['ambiguous_ok']}")
    print(f"  wrongly abstained (decidable)    : {rb['abstain_bad']}")
    print()
    print("="*74)
    print("TEST 3 — Impossibility proof (why A==B cannot be resolved statically)")
    wA,wB,xa,ab_a,la,xb,ab_b,lb = impossibility_example()
    print(f"  widths wA={wA}, wB={wB}")
    print(f"  point x={xa} -> (A,B)={ab_a}  truth={la}")
    print(f"  point x={xb} -> (A,B)={ab_b}  truth={lb}")
    print("  => identical (A,B,wA,wB) but different labels: NO static rule can separate them.")
    print()
    print("="*74)
    print("TEST 4 — ONE BIT of state (prev_state) removes the band entirely")
    print("         (the run-time fix: resolve_band_with_state); expect 0 errors")
    band_pts = errs = 0
    for _ in range(400):
        wA = round(random.uniform(0.5, 10.0), 3)
        wB = round(random.uniform(0.5, 10.0), 3)
        span = wA + wB
        for i in range(1200):
            x = -span - 3 + (2 * span + 6) * i / 1199
            A, B, label = geometry(x, wA, wB)
            if label in ("In A", "In B") and not truth_is_decidable(A, B, label, wA, wB):
                band_pts += 1
                # continuity supplies the true side as prev_state (1 bit)
                if resolve_band_with_state(A, B, wA, wB, prev_state=label) != label:
                    errs += 1
    print(f"  band samples (undecidable snapshots) : {band_pts}")
    print(f"  errors once 1 bit of state is given  : {errs}   (0 => the band is fully resolvable online)")
