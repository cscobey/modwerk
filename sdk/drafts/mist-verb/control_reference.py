# Copyright 2026 cscobey. MIT; see LICENSE.
"""Independent integer definition of sample-timed control ramps for trace tests."""

SCALE = 1 << 24
MASK = SCALE - 1
CURRENT = (0, 1, 2, 3, 4, 0xbf)
TRACE = CURRENT + tuple(range(0xc8, 0xce)) + tuple(range(0xe0, 0xe6)) + tuple(range(0xe8, 0xee))


def q23(value):
    return max(-8388608, min(8388607, round(value * 8388608)))


def targets(parameters):
    time, damp, diff, smear, gain, mix = parameters[:6]
    return (
        (time << 16) * q23(.98 * 128 / 127) // 8388608,
        (q23(.9) * 8388608 - (damp << 16) * q23(.85 * 128 / 127)) // 8388608,
        (diff << 16) * q23(.95 * 128 / 127) // 8388608,
        8388607 if smear == 127 else smear << 16,
        min(8388607, round(10 ** ((-40 + 40 * gain / 127) / 20) * 8388608)),
        8388607 if mix == 127 else mix << 16,
    )


def events(base, first_block):
    """Include a mid-ramp reversal and enough steady time to reach each endpoint."""
    return {
        0: base,
        first_block + 32: [0] * 12,
        first_block + 40: [127] * 6 + [0] * 6,
        first_block + 80: [127, 127, 0, 0, 0, 40] + [0] * 6,
        first_block + 96: [0, 0, 127, 127, 127, 0] + [0] * 6,
        first_block + 128: base,
    }


class Ramps:
    def __init__(self, goal):
        self.goal = list(goal)
        self.value = [v * SCALE for v in goal]
        self.step = [0] * 6
        self.remaining = [0] * 6

    def retarget(self, goal):
        for i, target in enumerate(goal):
            if target != self.goal[i]:
                self.goal[i] = target
                delta = target * SCALE - self.value[i]
                self.step[i] = delta // 256 if delta >= 0 else -((-delta) // 256)
                self.remaining[i] = 256

    def tick(self, indices):
        for i in indices:
            if self.remaining[i]:
                self.remaining[i] -= 1
                self.value[i] = (self.value[i] + self.step[i] if self.remaining[i]
                                 else self.goal[i] * SCALE)

    def trace(self):
        return ([v // SCALE for v in self.value] + [v & MASK for v in self.value]
                + self.remaining + self.goal)


def verify_trace(rows, prefix_frames, timeline):
    ramp = None
    parameters = timeline[0]
    clock = 0
    checked = 0
    for row in rows:
        block = row[0]
        if block in timeline:
            parameters = timeline[block]
        if block * 16 < prefix_frames:
            continue
        goal = targets(parameters)
        if ramp is None:
            ramp = Ramps(goal)
        else:
            ramp.retarget(goal)
        for _ in range(16):
            ramp.tick((5,))
            if clock < 32000:
                ramp.tick(range(5))
                clock += 44100
            clock -= 32000
        actual = row[3:]
        expected = ramp.trace()
        if actual != expected:
            differences = [(hex(TRACE[i]), a, b) for i, (a, b) in
                           enumerate(zip(actual, expected)) if a != b]
            raise RuntimeError(f'Control trace differs at block {block}: {differences}')
        checked += 1
    if not checked:
        raise RuntimeError('No active control trace')
    return {'sampleRampLength': 256, 'tankRampMs': 8,
            'mixRampMs': 256000 / 44100, 'blocksChecked': checked,
            'coefficientFractionCounterAndTargetTraceExact': True,
            'rapidRetargeting': True}
