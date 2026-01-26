from psychopy.data import QuestHandler

class QuestController:
    def __init__(self, start_val, max_weak, target):
        self.max_weak = max_weak
        self.target = target
        self.start_val = start_val
        self.current_intensity = start_val
        self.n_resets = 0

        self._make()

    def _make(self):
        self.handler = QuestHandler(
            startVal=self.start_val,
            startValSd=1.0,
            minVal=1.0,
            maxVal=self.max_weak,
            pThreshold=self.target,
            stepType="linear",
            nTrials=None,
            beta=3.5,
            gamma=0.5,
            delta=0.01
        )

    def update_max_weak(self, new_max):
        self.max_weak = new_max
        self.handler.maxVal = new_max
    
    def next_intensity(self):
        val = self.handler.next()
        self.current_intensity = round(max(1.0, min(val, self.max_weak)), 1)
        return self.current_intensity

    def add_response(self, correct, intensity):
        self.handler.addResponse(correct, intensity=intensity)

    def reset(self, verbose=False):
        self.start_val = min(self.handler.mean(), self.max_weak)
        self._make()
        self.n_resets += 1
        if verbose:
            print("QUEST has been reset to start value: ", self.start_val)