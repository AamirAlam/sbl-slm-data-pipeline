"""Reproducible audit sampling for routine model approvals."""
import math
import random

from .schema import require


def select(revisions, seed):
    population = sorted(set(revisions))
    count = math.ceil(len(population) * 0.10) if population else 0
    rng = random.Random(seed)
    selected = sorted(rng.sample(population, count)) if count else []
    return {"algorithm": "python-random-sample/v1", "seed": seed,
            "population": population, "selected": selected, "fraction": 0.10}


def record(store, actor, population, seed, expected):
    sample = select(population, seed)
    with store.transaction(expected) as db:
        ref = store.put(db, sample)
        store.append(db, "audit_sample", actor, {"ref": ref}, [ref, *sample["selected"]])
        return ref, sample
